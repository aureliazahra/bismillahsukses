import 'package:flutter/material.dart';
import 'cctvmanagement.dart'; // biar bisa pakai CameraData

class EditCameraDialog extends StatefulWidget {
  final CameraData camera;
  final Function(CameraData) onSave;

  const EditCameraDialog({
    super.key,
    required this.camera,
    required this.onSave,
  });

  @override
  State<EditCameraDialog> createState() => _EditCameraDialogState();
}

class _EditCameraDialogState extends State<EditCameraDialog> {
  late TextEditingController idController;
  late TextEditingController locationController;
  late TextEditingController sourceController;
  late TextEditingController refreshController;
  late TextEditingController nframesController;
  late TextEditingController motionController;
  late TextEditingController blurController;
  late TextEditingController anisotropyController;
  late TextEditingController exposureController;
  late TextEditingController luminanceController;

  bool showBoundingBox = true;
  bool exposureEnabled = true;

  @override
  void initState() {
    super.initState();
    idController = TextEditingController(text: widget.camera.id);
    locationController = TextEditingController(text: widget.camera.location);
    sourceController = TextEditingController(text: widget.camera.source.toString());
    refreshController = TextEditingController(text: "50");
    nframesController = TextEditingController(text: "3");
    motionController = TextEditingController(text: "10");
    blurController = TextEditingController(text: "10");
    anisotropyController = TextEditingController(text: "10");
    exposureController = TextEditingController(text: "10");
    luminanceController = TextEditingController(text: "10");
  }

  Widget _inputField(String label, TextEditingController controller) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: const TextStyle(color: Colors.white70)),
        const SizedBox(height: 6),
        TextField(
          controller: controller,
          style: const TextStyle(color: Colors.white),
          decoration: InputDecoration(
            filled: true,
            fillColor: const Color(0xFF0F0F2F),
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(8),
              borderSide: BorderSide.none,
            ),
            contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
          ),
        ),
        const SizedBox(height: 14),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    return Dialog(
      backgroundColor: const Color(0xFF05051A),
      insetPadding: const EdgeInsets.all(20),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // HEADER
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text(
                  "Edit Camera Settings",
                  style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold),
                ),
                IconButton(
                  icon: const Icon(Icons.close, color: Colors.white70),
                  onPressed: () => Navigator.pop(context),
                )
              ],
            ),
            const SizedBox(height: 20),

            // FORM INPUT
            _inputField("Camera ID", idController),
            _inputField("Location", locationController),
            _inputField("Source", sourceController),
            _inputField("Display refresh (ms)", refreshController),
            _inputField("Detect every N frames", nframesController),
            _inputField("Motion Threshold (0–1)", motionController),
            _inputField("Blur threshold (0–1)", blurController),
            _inputField("Anisotropy Threshold (0–1)", anisotropyController),

            // TOGGLES
            SwitchListTile(
              title: const Text("Show bounding box on skipped face", style: TextStyle(color: Colors.white70)),
              value: showBoundingBox,
              onChanged: (val) => setState(() => showBoundingBox = val),
              activeColor: Colors.blue,
            ),
            SwitchListTile(
              title: const Text("Exposure enabled", style: TextStyle(color: Colors.white70)),
              value: exposureEnabled,
              onChanged: (val) => setState(() => exposureEnabled = val),
              activeColor: Colors.blue,
            ),

            _inputField("Exposure gain", exposureController),
            _inputField("Min luminance", luminanceController),

            const SizedBox(height: 20),

            // ACTION BUTTONS
            Row(
              mainAxisAlignment: MainAxisAlignment.end,
              children: [
                TextButton(
                  onPressed: () => Navigator.pop(context),
                  child: const Text("Cancel", style: TextStyle(color: Colors.white70)),
                ),
                const SizedBox(width: 12),
                ElevatedButton(
                  onPressed: () {
                    final updatedCamera = CameraData(
                      id: idController.text,
                      name: widget.camera.name,
                      location: locationController.text,
                      status: widget.camera.status,
                      lastUpdated: DateTime.now(),
                      source: sourceController.text,
                      width: widget.camera.width,
                      height: widget.camera.height,
                    );
                    widget.onSave(updatedCamera);
                    Navigator.pop(context);
                  },
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.blue,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                    padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                  ),
                  child: const Text("Apply Changes"),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
