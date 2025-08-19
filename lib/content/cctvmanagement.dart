import 'package:flutter/material.dart';
import 'dart:convert';
import 'dart:async';
import 'package:http/http.dart' as http;
import 'package:lolos/content/edit.dart';


class CCTVManagementPage extends StatefulWidget {
  const CCTVManagementPage({super.key});

  @override
  State<CCTVManagementPage> createState() => _CCTVManagementPageState();
}

class _CCTVManagementPageState extends State<CCTVManagementPage> {
  List<CameraData> cameras = [];
  bool isLoading = true;
  String selectedFilter = "All";
  Timer? _refreshTimer;
  final String baseUrl = "http://localhost:8000"; // Python backend URL

  @override
  void initState() {
    super.initState();
    _loadCameras();
    // Refresh camera status every 10 seconds
    _refreshTimer = Timer.periodic(const Duration(seconds: 10), (timer) {
      _loadCameras();
    });
  }

 // Fungsi hapus kamera
void _deleteCamera(String id) {
  setState(() {
    cameras.removeWhere((camera) => camera.id == id);
  });
}

  //actions pop up

void _showCameraActions(CameraData camera) {
  showModalBottomSheet(
    context: context,
    backgroundColor: const Color(0xFF0A0A2A),
    shape: const RoundedRectangleBorder(
      borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
    ),
    builder: (context) {
      return Padding(
        padding: const EdgeInsets.all(16),
        child: Wrap(
          children: [
            ListTile(
              leading: const Icon(Icons.edit, color: Colors.white70),
              title: const Text("Edit", style: TextStyle(color: Colors.white)),
              onTap: () {
                 Navigator.pop(context);
  showDialog(
    context: context,
    builder: (context) => EditCameraDialog(
      camera: camera,
      onSave: (updatedCamera) {
        setState(() {
          cameras[cameras.indexWhere((c) => c.id == updatedCamera.id)] = updatedCamera;
        });
      },
    ),
  );
              },
            ),
            ListTile(
              leading: const Icon(Icons.videocam, color: Colors.white70),
              title: const Text("Live Preview", style: TextStyle(color: Colors.white)),
              onTap: () {
                Navigator.pop(context);
                // TODO: implementasi live preview
              },
            ),
            ListTile(
              leading: const Icon(Icons.refresh, color: Colors.white70),
              title: const Text("Refresh", style: TextStyle(color: Colors.white)),
              onTap: () {
                Navigator.pop(context);
                _loadCameras();
              },
            ),
            ListTile(
    leading: Icon(Icons.delete, color: Colors.red),
    title: Text("Delete", style: TextStyle(color: Colors.white)),
    onTap: () {
      // Sekarang jangan langsung hapus, tapi panggil confirm dialog
      Navigator.pop(context); 
showDialog(
    context: context,
    builder: (BuildContext context) {
      return AlertDialog(
        title: Text("Confirm Delete"),
        content: Text("Are you sure you want to delete this camera?"),
        actions: [
          TextButton(
            onPressed: () {
              Navigator.of(context).pop(); // Tutup konfirmasi
            },
            child: Text("Cancel"),
          ),
          ElevatedButton(
            onPressed: () {
              // TODO: logika delete download di sini
             _deleteCamera(camera.id);
              Navigator.of(context).pop(); // Tutup konfirmasi
            },
            child: Text("Delete"),
          ),
        ],
      );
    },
  );
    },
  ),
            ListTile(
              leading: const Icon(Icons.info, color: Colors.white70),
              title: const Text("Details", style: TextStyle(color: Colors.white)),
              onTap: () {
                Navigator.pop(context);
                _showCameraSettings(camera);
              },
            ),
          ],
        ),
      );
    },
  );
}



  @override
  void dispose() {
    _refreshTimer?.cancel();
    super.dispose();
  }

  Future<void> _loadCameras() async {
    try {
      final response = await http.get(Uri.parse('$baseUrl/cameras'));
      if (response.statusCode == 200) {
        final List<dynamic> data = json.decode(response.body);
        setState(() {
          cameras = data.map((json) => CameraData.fromJson(json)).toList();
          isLoading = false;
        });
      } else {
        // Fallback to mock data if API fails
        _loadMockData();
      }
    } catch (e) {
      print('Error loading cameras: $e');
      _loadMockData();
    }
  }

  void _loadMockData() {
    setState(() {
      cameras = [
        CameraData(
          id: "CAM-001",
          name: "Kamera CCTV 1",
          location: "Gate A",
          status: "Active",
          lastUpdated: DateTime.now().subtract(const Duration(minutes: 2)),
          source: 0,
          width: 640,
          height: 480,
        ),
        CameraData(
          id: "CAM-002",
          name: "IP Kamera Luar",
          location: "Gate B",
          status: "Active",
          lastUpdated: DateTime.now().subtract(const Duration(minutes: 1)),
          source: "rtsp://aatc:ke67bu@192.168.0.239:554/stream1",
          width: 640,
          height: 480,
        ),
        CameraData(
          id: "CAM-003",
          name: "IP Kamera Dalam",
          location: "Gate C",
          status: "Offline",
          lastUpdated: DateTime.now().subtract(const Duration(days: 27)),
          source: "rtsp://admin:admin@192.168.0.241:554/stream1",
          width: 640,
          height: 480,
        ),
      ];
      isLoading = false;
    });
  }

  Future<void> _addNewCamera() async {
    // Show dialog to add new camera
    showDialog(
      context: context,
      builder: (context) => AddCameraDialog(
        onCameraAdded: (camera) async {
          try {
            final response = await http.post(
              Uri.parse('$baseUrl/cameras'),
              headers: {'Content-Type': 'application/json'},
              body: json.encode(camera.toJson()),
            );
            if (response.statusCode == 200) {
              _loadCameras();
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('Camera added successfully!')),
              );
            }
          } catch (e) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(content: Text('Error adding camera: $e')),
            );
          }
        },
      ),
    );
  }

  Future<void> _toggleCameraStatus(CameraData camera) async {
    try {
      final newStatus = camera.status == "Active" ? "Offline" : "Active";
      final response = await http.put(
        Uri.parse('$baseUrl/cameras/${camera.id}'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({'status': newStatus}),
      );
      if (response.statusCode == 200) {
        _loadCameras();
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error updating camera: $e')),
      );
    }
  }

  List<CameraData> get filteredCameras {
    if (selectedFilter == "All") return cameras;
    return cameras.where((camera) => camera.status == selectedFilter).toList();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF05051A),
      body: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // === HEADER CARD ===
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [Color(0xFF0A0A2A), Color(0xFF131347)],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: BorderRadius.circular(20),
                boxShadow: [
                  BoxShadow(
                    color: Colors.blue.withOpacity(0.3),
                    blurRadius: 20,
                    spreadRadius: 2,
                    offset: const Offset(0, 5),
                  ),
                ],
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text(
                        "CCTV Management",
                        style: TextStyle(
                          color: Colors.white,
                          fontSize: 28,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      if (isLoading)
                        const SizedBox(
                          width: 20,
                          height: 20,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            valueColor: AlwaysStoppedAnimation<Color>(Colors.blue),
                          ),
                        ),
                    ],
                  ),
                  const SizedBox(height: 4),
                  RichText(
                    text: const TextSpan(
                      children: [
                        TextSpan(
                          text: "One Trace, ",
                          style: TextStyle(
                            color: Colors.white70,
                            fontSize: 16,
                          ),
                        ),
                        TextSpan(
                          text: "One Hope.",
                          style: TextStyle(
                            color: Color(0xFF57E6FF),
                            fontSize: 16,
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 16),
                  // Button Add New Camera
                  Container(
                    decoration: BoxDecoration(
                      borderRadius: BorderRadius.circular(30),
                      gradient: const LinearGradient(
                        colors: [Color(0xFF3A5BFF), Color(0xFF192BC2)],
                      ),
                    ),
                    child: ElevatedButton.icon(
                      onPressed: _addNewCamera,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.transparent,
                        shadowColor: Colors.transparent,
                        padding: const EdgeInsets.symmetric(
                            horizontal: 20, vertical: 12),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(30),
                        ),
                      ),
                      icon: const Icon(Icons.add, size: 18, color: Colors.white),
                      label: const Text(
                        "Add New Camera",
                        style: TextStyle(
                            fontSize: 14,
                            fontWeight: FontWeight.bold,
                            color: Colors.white),
                      ),
                    ),
                  ),
                ],
              ),
            ),

            const SizedBox(height: 20),

            // === FILTER BUTTONS (Equal Width) ===
            Row(
              children: [
                Expanded(child: _filterButton("All", selectedFilter == "All")),
                const SizedBox(width: 10),
                Expanded(child: _filterButton("Active", selectedFilter == "Active")),
                const SizedBox(width: 10),
                Expanded(child: _filterButton("Offline", selectedFilter == "Offline")),
              ],
            ),

            const SizedBox(height: 20),

            // === TABLE HEADER ===
            Container(
              padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 10),
              decoration: BoxDecoration(
                color: const Color(0xFF0F0F2F),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Row(
                children: const [
                  Expanded(flex: 2, child: _TableHeaderText("ID")),
                  Expanded(flex: 3, child: _TableHeaderText("Location")),
                  Expanded(flex: 2, child: _TableHeaderText("Status")),
                  Expanded(flex: 3, child: _TableHeaderText("Last Updated")),
                ],
              ),
            ),

            // === TABLE CONTENT ===
            Expanded(
              child: Container(
                decoration: BoxDecoration(
                  color: const Color(0xFF0A0A2A),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: isLoading
                    ? const Center(
                        child: CircularProgressIndicator(
                          valueColor: AlwaysStoppedAnimation<Color>(Colors.blue),
                        ),
                      )
                    : filteredCameras.isEmpty
                        ? const Center(
                            child: Text(
                              "No cameras found",
                              style: TextStyle(color: Colors.white70),
                            ),
                          )
                        : // === Ganti bagian ListView.builder di CCTVManagementPage ===
ListView.builder(
  itemCount: filteredCameras.length,
  itemBuilder: (context, index) {
    final camera = filteredCameras[index];
    final isActive = camera.status == "Active";

    return GestureDetector(
      onTap: () => _showCameraActions(camera), // 👈 pop up ketika ditekan
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 10),
        decoration: BoxDecoration(
          border: Border(
            bottom: BorderSide(color: Colors.white.withOpacity(0.05)),
          ),
        ),
        child: Row(
          children: [
            Expanded(flex: 2, child: Text(camera.id, style: const TextStyle(color: Colors.white70))),
            Expanded(flex: 3, child: Text(camera.location, style: const TextStyle(color: Colors.white70))),
            Expanded(
              flex: 2,
              child: Text(
                camera.status,
                style: TextStyle(
                  color: isActive ? const Color(0xFF3DC9FF) : const Color(0xFFFF9900),
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
            Expanded(flex: 3, child: Text(_formatDateTime(camera.lastUpdated), style: const TextStyle(color: Colors.white70))),
          ],
        ),
      ),
    );
  },
),

              ),
            ),
          ],
        ),
      ),
    );
  }

  String _formatDateTime(DateTime dateTime) {
    final now = DateTime.now();
    final difference = now.difference(dateTime);
    
    if (difference.inDays > 0) {
      return "${dateTime.day}/${dateTime.month}/${dateTime.year} - ${dateTime.hour}:${dateTime.minute.toString().padLeft(2, '0')}";
    } else if (difference.inHours > 0) {
      return "${difference.inHours}h ago";
    } else if (difference.inMinutes > 0) {
      return "${difference.inMinutes}m ago";
    } else {
      return "Just now";
    }
  }

  void _showCameraSettings(CameraData camera) {
    showDialog(
      context: context,
      builder: (context) => CameraSettingsDialog(camera: camera),
    );
  }

  Widget _filterButton(String text, bool isSelected) {
    return GestureDetector(
      onTap: () {
        setState(() {
          selectedFilter = text;
        });
      },
      child: Container(
        decoration: BoxDecoration(
          color: isSelected ? Colors.blueAccent : const Color(0xFF1B1B3C),
          borderRadius: BorderRadius.circular(20),
        ),
        padding: const EdgeInsets.symmetric(vertical: 8),
        alignment: Alignment.center,
        child: Text(
          text,
          style: const TextStyle(
            color: Colors.white,
            fontWeight: FontWeight.bold,
          ),
        ),
      ),
    );
  }
}

// === CAMERA DATA MODEL ===
class CameraData {
  final String id;
  final String name;
  final String location;
  final String status;
  final DateTime lastUpdated;
  final dynamic source;
  final int width;
  final int height;

  CameraData({
    required this.id,
    required this.name,
    required this.location,
    required this.status,
    required this.lastUpdated,
    required this.source,
    required this.width,
    required this.height,
  });

  factory CameraData.fromJson(Map<String, dynamic> json) {
    return CameraData(
      id: json['id'] ?? 'CAM-${DateTime.now().millisecondsSinceEpoch}',
      name: json['name'] ?? 'Unknown Camera',
      location: json['location'] ?? 'Unknown Location',
      status: json['status'] ?? 'Offline',
      lastUpdated: DateTime.now(),
      source: json['source'] ?? 0,
      width: json['width'] ?? 640,
      height: json['height'] ?? 480,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'location': location,
      'status': status,
      'source': source,
      'width': width,
      'height': height,
    };
  }
}

// === ADD CAMERA DIALOG ===
class AddCameraDialog extends StatefulWidget {
  final Function(CameraData) onCameraAdded;

  const AddCameraDialog({super.key, required this.onCameraAdded});

  @override
  State<AddCameraDialog> createState() => _AddCameraDialogState();
}

class _AddCameraDialogState extends State<AddCameraDialog> {
  final _formKey = GlobalKey<FormState>();
  final _idController = TextEditingController();
  final _locationController = TextEditingController();
  final _sourceController = TextEditingController();
  final _notesController = TextEditingController();

  bool isActive = true; // toggle status

  Widget _inputField(String label, TextEditingController controller,
      {String? hint, bool optional = false}) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Text(label,
                style: const TextStyle(color: Colors.white70, fontSize: 14)),
            if (optional)
              const Text(" (Optional)",
                  style: TextStyle(color: Colors.grey, fontSize: 12)),
          ],
        ),
        const SizedBox(height: 6),
        TextFormField(
          controller: controller,
          style: const TextStyle(color: Colors.white),
          decoration: InputDecoration(
            hintText: hint,
            hintStyle: const TextStyle(color: Colors.white38),
            filled: true,
            fillColor: const Color(0xFF0F0F2F),
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(8),
              borderSide: BorderSide.none,
            ),
            contentPadding:
                const EdgeInsets.symmetric(horizontal: 12, vertical: 14),
          ),
          validator: (value) {
            if (!optional && (value == null || value.isEmpty)) {
              return 'Please enter $label';
            }
            return null;
          },
        ),
        const SizedBox(height: 16),
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
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // === FORM INPUTS ===
              _inputField("Camera ID", _idController, hint: "CAM-200"),
              _inputField("Location", _locationController,
                  hint: "Ruang parkir belakang"),
              _inputField("Source", _sourceController,
                  hint: "rtsp://192.168.1.11:554/stream200"),

              // === STATUS TOGGLE ===
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text("Status",
                      style: TextStyle(color: Colors.white70, fontSize: 14)),
                  Row(
                    children: [
                      Switch(
                        value: isActive,
                        onChanged: (val) => setState(() => isActive = val),
                        activeColor: Colors.blue,
                      ),
                      Text(
                        isActive ? "Active" : "Offline",
                        style: const TextStyle(color: Colors.white),
                      ),
                    ],
                  )
                ],
              ),
              const SizedBox(height: 16),

              // === NOTES (Optional) ===
              _inputField("Notes/Description", _notesController,
                  optional: true, hint: "Area ini rawan pencurian"),

              const SizedBox(height: 20),

              // === BUTTONS ===
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  ElevatedButton(
                    onPressed: () {
                      if (_formKey.currentState!.validate()) {
                        final camera = CameraData(
                          id: _idController.text,
                          name: _idController.text,
                          location: _locationController.text,
                          status: isActive ? "Active" : "Offline",
                          lastUpdated: DateTime.now(),
                          source: _sourceController.text,
                          width: 640,
                          height: 480,
                        );
                        widget.onCameraAdded(camera);
                        Navigator.of(context).pop();
                      }
                    },
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.blue,
                      padding: const EdgeInsets.symmetric(
                          horizontal: 24, vertical: 14),
                      shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(30)),
                    ),
                    child: const Text("Add New Camera",
                        style: TextStyle(color: Colors.white)),
                  ),
                  const SizedBox(width: 12),
                  TextButton(
                    onPressed: () => Navigator.pop(context),
                    child: const Text("Cancel",
                        style: TextStyle(color: Colors.white70)),
                  ),
                ],
              )
            ],
          ),
        ),
      ),
    );
  }
}


// === CAMERA SETTINGS DIALOG ===
class CameraSettingsDialog extends StatelessWidget {
  final CameraData camera;

  const CameraSettingsDialog({super.key, required this.camera});

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      backgroundColor: const Color(0xFF0A0A2A),
      title: Text(
        "Settings - ${camera.name}",
        style: const TextStyle(color: Colors.white),
      ),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _settingRow("ID", camera.id),
          _settingRow("Name", camera.name),
          _settingRow("Location", camera.location),
          _settingRow("Status", camera.status),
          _settingRow("Source", camera.source.toString()),
          _settingRow("Resolution", "${camera.width}x${camera.height}"),
        ],
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(context).pop(),
          child: const Text("Close", style: TextStyle(color: Colors.white70)),
        ),
      ],
    );
  }

  Widget _settingRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(
            "$label:",
            style: const TextStyle(color: Colors.white70, fontWeight: FontWeight.bold),
          ),
          Text(
            value,
            style: const TextStyle(color: Colors.white),
          ),
        ],
      ),
    );
  }
}

// === TABEL HEADER TEXT STYLE ===
class _TableHeaderText extends StatelessWidget {
  final String text;
  const _TableHeaderText(this.text);

  @override
  Widget build(BuildContext context) {
    return Text(
      text,
      style:
          const TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
    );
  }
}
