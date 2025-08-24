import 'dart:io';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

class AddMissingPersonDialog extends StatefulWidget {
  final Function(Map<String, dynamic>) onPersonAdded;

  const AddMissingPersonDialog({super.key, required this.onPersonAdded});

  @override
  _AddMissingPersonDialogState createState() => _AddMissingPersonDialogState();
}

class _AddMissingPersonDialogState extends State<AddMissingPersonDialog> {
  final TextEditingController nameController = TextEditingController();
  final TextEditingController infoController = TextEditingController();
  final TextEditingController resultController = TextEditingController();
  File? _imageFile;

  Future<void> _pickImage() async {
    final pickedFile =
        await ImagePicker().pickImage(source: ImageSource.gallery);
    if (pickedFile != null) {
      setState(() {
        _imageFile = File(pickedFile.path);
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Dialog(
      backgroundColor: Colors.transparent,
      insetPadding: const EdgeInsets.all(20),
      child: Container(
        padding: const EdgeInsets.all(24),
        decoration: BoxDecoration(
          gradient: const LinearGradient(
            colors: [Color(0xFF0B1220), Color(0xFF163B69)],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: Colors.blueAccent, width: 1),
        ),
        child: SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.center,
            mainAxisSize: MainAxisSize.min,
            children: [
              const Text(
                "Add Missing Person",
                style: TextStyle(
                  fontSize: 22,
                  fontWeight: FontWeight.bold,
                  color: Colors.white,
                ),
              ),
              const SizedBox(height: 20),

              // Upload picture square box (centered)
              GestureDetector(
                onTap: _pickImage,
                child: Column(
                  children: [
                    Container(
                      width: 150,
                      height: 150,
                      decoration: BoxDecoration(
                        color: Colors.cyanAccent.withOpacity(0.2),
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(color: Colors.cyanAccent, width: 2),
                      ),
                      child: _imageFile != null
                          ? ClipRRect(
                              borderRadius: BorderRadius.circular(12),
                              child: Image.file(
                                _imageFile!,
                                fit: BoxFit.cover,
                              ),
                            )
                          : const Center(
                              child: Icon(
                                Icons.person,
                                size: 80,
                                color: Colors.white,
                              ),
                            ),
                    ),
                    const SizedBox(height: 8),
                    if (_imageFile == null)
                      const Text(
                        "Tap to upload photo",
                        style: TextStyle(
                          color: Colors.white70,
                          fontSize: 14,
                        ),
                      ),
                  ],
                ),
              ),
              const SizedBox(height: 20),

              // Name field
              _buildTextField("Name", nameController),
              const SizedBox(height: 12),

              // Additional Information
              _buildTextField("Additional Information", infoController),
              const SizedBox(height: 12),

              // Result
              _buildTextField("Result", resultController),
              const SizedBox(height: 20),

              // Buttons
              Row(
                mainAxisAlignment: MainAxisAlignment.end,
                children: [
                  ElevatedButton(
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.blueAccent,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                    ),
                    onPressed: () {
                      final data = {
                        "name": nameController.text,
                        "info": infoController.text,
                        "result": resultController.text,
                        "photo": _imageFile?.path ?? "",
                        "reportedTime": DateTime.now().toString().split(' ')[0], // Add current date
                      };
                      widget.onPersonAdded(data);
                      Navigator.pop(context);
                    },
                    child: const Text("Save Information"),
                  ),
                  const SizedBox(width: 10),
                  ElevatedButton(
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.grey,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                    ),
                    onPressed: () {
                      Navigator.pop(context);
                    },
                    child: const Text("Cancel"),
                  ),
                ],
              )
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildTextField(String label, TextEditingController controller) {
    return TextField(
      controller: controller,
      style: const TextStyle(color: Colors.white),
      decoration: InputDecoration(
        labelText: label,
        labelStyle: const TextStyle(color: Colors.white70),
        filled: true,
        fillColor: Colors.black,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
        ),
      ),
    );
  }
}
