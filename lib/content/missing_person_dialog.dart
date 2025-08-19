import 'dart:io';
import 'package:flutter/material.dart';

class MissingPersonDetailDialog extends StatelessWidget {
  final Map<String, dynamic> data;

  const MissingPersonDetailDialog({super.key, required this.data});

  @override
  Widget build(BuildContext context) {
    return Dialog(
      backgroundColor: Colors.transparent,
      child: Container(
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          color: const Color(0xFF0B1220),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: Colors.blueAccent),
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text("Missing Person",
                style: TextStyle(
                    color: Colors.white,
                    fontSize: 22,
                    fontWeight: FontWeight.bold)),

            const SizedBox(height: 16),

            // Foto
            Container(
              width: 150,
              height: 150,
              decoration: BoxDecoration(
                color: Colors.cyanAccent,
                borderRadius: BorderRadius.circular(8),
              ),
              child: data["photo"] != null && data["photo"].toString().isNotEmpty
                  ? ClipRRect(
                      borderRadius: BorderRadius.circular(8),
                      child: Image.file(
                        File(data["photo"]),
                        fit: BoxFit.cover,
                        errorBuilder: (context, error, stackTrace) {
                          return const Icon(Icons.person, size: 80, color: Colors.white);
                        },
                      ),
                    )
                  : const Icon(Icons.person, size: 80, color: Colors.white),
            ),

            const SizedBox(height: 16),

            // Nama
            _buildField("Name", data["name"]),
            _buildField("Additional Information", data["info"]),
            _buildField("Result", data["result"]),

            Align(
              alignment: Alignment.centerLeft,
              child: Text(
                "Reported Missing Time: ${data["reportedTime"]}",
                style: TextStyle(color: Colors.white70),
              ),
            ),

            const SizedBox(height: 20),

            // Tombol
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                ElevatedButton(
                  onPressed: () {
                    // Save info handler
                  },
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.blueAccent,
                  ),
                  child: const Text("Save Information"),
                ),
                const SizedBox(width: 10),
                ElevatedButton(
                  onPressed: () {
                    Navigator.pop(context);
                  },
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.redAccent,
                  ),
                  child: const Text("Delete Missing Person"),
                ),
              ],
            )
          ],
        ),
      ),
    );
  }

  Widget _buildField(String label, String value) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: TextStyle(color: Colors.white70)),
        Container(
          width: double.infinity,
          padding: const EdgeInsets.all(8),
          margin: const EdgeInsets.only(bottom: 12),
          decoration: BoxDecoration(
            color: Colors.black54,
            borderRadius: BorderRadius.circular(12),
          ),
          child: Text(value, style: TextStyle(color: Colors.white)),
        ),
      ],
    );
  }
}
