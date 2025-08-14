import 'dart:convert';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:camera/camera.dart';
import 'package:flutter_vlc_player/flutter_vlc_player.dart';
import 'package:http/http.dart' as http;
import 'package:path_provider/path_provider.dart';
import 'package:permission_handler/permission_handler.dart';

class RealTimeDetectionPage extends StatefulWidget {
  const RealTimeDetectionPage({super.key});

  @override
  State<RealTimeDetectionPage> createState() => _RealTimeDetectionPageState();
}

class _RealTimeDetectionPageState extends State<RealTimeDetectionPage> {
  List<CameraConfig> cameras = [];
  List<CameraController?> cameraControllers = [];
  List<VlcPlayerController?> vlcControllers = [];
  bool isLoading = true;
  String? errorMessage;

  @override
  void initState() {
    super.initState();
    _loadCameraConfiguration();
  }

  @override
  void dispose() {
    _disposeControllers();
    super.dispose();
  }

  void _disposeControllers() {
    for (var controller in cameraControllers) {
      controller?.dispose();
    }
    for (var controller in vlcControllers) {
      controller?.dispose();
    }
  }

  Future<void> _loadCameraConfiguration() async {
    try {
      setState(() {
        isLoading = true;
        errorMessage = null;
      });

      // Try to load from assets first
      try {
        final response = await http.get(Uri.parse('/assets/cameras.json'));
        if (response.statusCode == 200) {
          final List<dynamic> data = json.decode(response.body);
          cameras = data.map((json) => CameraConfig.fromJson(json)).toList();
        } else {
          throw Exception('Failed to load cameras.json from assets');
        }
      } catch (e) {
        // Fallback: try to load from local file system
        try {
          final directory = await getApplicationDocumentsDirectory();
          final file = File('${directory.path}/cameras.json');
          if (await file.exists()) {
            final contents = await file.readAsString();
            final List<dynamic> data = json.decode(contents);
            cameras = data.map((json) => CameraConfig.fromJson(json)).toList();
          } else {
            // Create default configuration if file doesn't exist
            cameras = _createDefaultCameraConfig();
          }
        } catch (e) {
          // Use default configuration as fallback
          cameras = _createDefaultCameraConfig();
        }
      }

      // Initialize controllers for each camera
      await _initializeControllers();

      setState(() {
        isLoading = false;
      });
    } catch (e) {
      setState(() {
        isLoading = false;
        errorMessage = 'Error loading camera configuration: $e';
      });
    }
  }

  List<CameraConfig> _createDefaultCameraConfig() {
    return [
      CameraConfig(
        name: "Local Webcam",
        source: 0,
        width: 640,
        height: 480,
        id: "CAM-001",
        status: "Active",
      ),
      CameraConfig(
        name: "CCTV Stream 1",
        source: "rtsp://admin:admin@192.168.1.100:554/stream1",
        width: 640,
        height: 480,
        id: "CAM-002",
        status: "Active",
      ),
      CameraConfig(
        name: "CCTV Stream 2",
        source: "http://192.168.1.101:8080/video",
        width: 640,
        height: 480,
        id: "CAM-003",
        status: "Active",
      ),
      CameraConfig(
        name: "Backup Webcam",
        source: 1,
        width: 640,
        height: 480,
        id: "CAM-004",
        status: "Active",
      ),
    ];
  }

  Future<void> _initializeControllers() async {
    // Dispose existing controllers
    _disposeControllers();
    
    cameraControllers = List.filled(cameras.length, null);
    vlcControllers = List.filled(cameras.length, null);

    for (int i = 0; i < cameras.length; i++) {
      final camera = cameras[i];
      
      if (camera.source is int) {
        // Local webcam
        try {
          await _initializeLocalCamera(i);
        } catch (e) {
          print('Failed to initialize local camera $i: $e');
        }
      } else if (camera.source is String) {
        // CCTV stream
        try {
          await _initializeVlcController(i);
        } catch (e) {
          print('Failed to initialize VLC controller $i: $e');
        }
      }
    }
  }

  Future<void> _initializeLocalCamera(int index) async {
    try {
      // Request camera permission
      final status = await Permission.camera.request();
      if (status.isDenied) {
        throw Exception('Camera permission denied');
      }

      // Get available cameras
      final cameras = await availableCameras();
      if (cameras.isEmpty) {
        throw Exception('No cameras available');
      }

      // Use the specified camera index or default to first camera
      final cameraIndex = this.cameras[index].source as int;
      final selectedCamera = cameraIndex < cameras.length 
          ? cameras[cameraIndex] 
          : cameras.first;

      // Create and initialize controller
      final controller = CameraController(
        selectedCamera,
        ResolutionPreset.medium,
        enableAudio: false,
      );

      await controller.initialize();
      
      if (mounted) {
        setState(() {
          cameraControllers[index] = controller;
        });
      }
    } catch (e) {
      print('Error initializing local camera: $e');
      rethrow;
    }
  }

  Future<void> _initializeVlcController(int index) async {
    try {
      final camera = cameras[index];
      final controller = VlcPlayerController.network(
        camera.source as String,
        hwAcc: HwAcc.full,
        autoPlay: true,
        autoInitialize: true,
      );

      if (mounted) {
        setState(() {
          vlcControllers[index] = controller;
        });
      }
    } catch (e) {
      print('Error initializing VLC controller: $e');
      rethrow;
    }
  }

  Widget _buildCameraWidget(int index) {
    final camera = cameras[index];
    final isLocalCamera = camera.source is int;
    final cameraController = cameraControllers[index];
    final vlcController = vlcControllers[index];

    return ClipRRect(
      borderRadius: BorderRadius.circular(12),
      child: Stack(
        children: [
          // Camera feed
          Container(
            width: double.infinity,
            height: double.infinity,
            color: Colors.grey[800],
            child: isLocalCamera
                ? _buildLocalCameraFeed(cameraController)
                : _buildCctvFeed(vlcController),
          ),
          
          // Camera info overlay (bottom-left)
          Positioned(
            left: 8,
            bottom: 8,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              decoration: BoxDecoration(
                color: Colors.black54,
                borderRadius: BorderRadius.circular(4),
              ),
              child: Text(
                camera.name,
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 12,
                  fontWeight: FontWeight.w500,
                ),
              ),
            ),
          ),
          
          // LIVE indicator (top-right)
          Positioned(
            top: 8,
            right: 8,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              decoration: BoxDecoration(
                color: Colors.red,
                borderRadius: BorderRadius.circular(4),
              ),
              child: const Text(
                'LIVE',
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 10,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
          ),
          
          // Status indicator (top-left)
          Positioned(
            top: 8,
            left: 8,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
              decoration: BoxDecoration(
                color: camera.status == 'Active' ? Colors.green : Colors.orange,
                borderRadius: BorderRadius.circular(3),
              ),
              child: Text(
                camera.status,
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 8,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
          ),

          // Source type indicator (center-top)
          Positioned(
            top: 30,
            left: 0,
            right: 0,
            child: Center(
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: Colors.black54,
                  borderRadius: BorderRadius.circular(4),
                ),
                child: Text(
                  isLocalCamera ? 'Local Camera' : 'CCTV Stream',
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 10,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildLocalCameraFeed(CameraController? controller) {
    if (controller == null || !controller.value.isInitialized) {
      return const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            CircularProgressIndicator(color: Colors.white),
            SizedBox(height: 8),
            Text(
              'Initializing camera...',
              style: TextStyle(color: Colors.white, fontSize: 12),
            ),
          ],
        ),
      );
    }

    return CameraPreview(controller);
  }

  Widget _buildCctvFeed(VlcPlayerController? controller) {
    if (controller == null) {
      return const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            CircularProgressIndicator(color: Colors.white),
            SizedBox(height: 8),
            Text(
              'Connecting to stream...',
              style: TextStyle(color: Colors.white, fontSize: 12),
            ),
          ],
        ),
      );
    }

    return VlcPlayer(
      controller: controller,
      aspectRatio: 16 / 9,
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0B1220),
      body: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [Color(0xFF4AB1EB), Color(0xFF2D6AA6)],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    "Real-Time\nDetection",
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 28,
                      fontWeight: FontWeight.bold,
                      height: 1.2,
                    ),
                  ),
                  const SizedBox(height: 6),
                  const Text(
                    "Live camera feeds with real-time monitoring",
                    style: TextStyle(
                      color: Colors.white70,
                      fontSize: 14,
                    ),
                  ),
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      ElevatedButton.icon(
                        onPressed: _loadCameraConfiguration,
                        icon: const Icon(Icons.refresh),
                        label: const Text('Refresh'),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.white,
                          foregroundColor: const Color(0xFF2D6AA6),
                        ),
                      ),
                      const SizedBox(width: 12),
                      ElevatedButton.icon(
                        onPressed: () => _showConfigurationDialog(),
                        icon: const Icon(Icons.settings),
                        label: const Text('Configure'),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.white,
                          foregroundColor: const Color(0xFF2D6AA6),
                        ),
                      ),
                      const SizedBox(width: 12),
                      ElevatedButton.icon(
                        onPressed: () => _showAddCameraDialog(),
                        icon: const Icon(Icons.add),
                        label: const Text('Add Camera'),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.white,
                          foregroundColor: const Color(0xFF2D6AA6),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
            const SizedBox(height: 20),

            // Error message
            if (errorMessage != null)
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(12),
                margin: const EdgeInsets.only(bottom: 20),
                decoration: BoxDecoration(
                  color: Colors.red[100],
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: Colors.red),
                ),
                child: Text(
                  errorMessage!,
                  style: const TextStyle(color: Colors.red),
                ),
              ),

            // Camera grid
            if (isLoading)
              const Expanded(
                child: Center(
                  child: CircularProgressIndicator(color: Colors.white),
                ),
              )
            else if (cameras.isEmpty)
              const Expanded(
                child: Center(
                  child: Text(
                    'No cameras configured',
                    style: TextStyle(color: Colors.white, fontSize: 16),
                  ),
                ),
              )
            else
              Expanded(
                child: GridView.builder(
                  itemCount: cameras.length,
                  gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                    crossAxisCount: 2,
                    crossAxisSpacing: 12,
                    mainAxisSpacing: 12,
                    childAspectRatio: 4 / 3,
                  ),
                  itemBuilder: (context, index) {
                    return _buildCameraWidget(index);
                  },
                ),
              ),
          ],
        ),
      ),
    );
  }

  void _showConfigurationDialog() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Camera Configuration'),
        content: const Text(
          'To configure cameras, edit the cameras.json file in your assets folder.\n\n'
          'The file should contain an array of camera objects with the following structure:\n\n'
          '{\n'
          '  "name": "Camera Name",\n'
          '  "source": 0,  // Integer for local webcam, URL string for CCTV\n'
          '  "width": 640,\n'
          '  "height": 480,\n'
          '  "id": "CAM-001",\n'
          '  "status": "Active"\n'
          '}\n\n'
          'For local webcams, use integer indices (0, 1, 2, etc.).\n'
          'For CCTV streams, use RTSP/HTTP URLs.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('OK'),
          ),
        ],
      ),
    );
  }

  void _showAddCameraDialog() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Add New Camera'),
        content: const Text(
          'To add a new camera:\n\n'
          '1. Edit the cameras.json file in your assets folder\n'
          '2. Add a new camera configuration\n'
          '3. Click the Refresh button\n\n'
          'Example configurations:\n\n'
          'Local Webcam:\n'
          '{"name": "New Camera", "source": 2, "id": "CAM-005"}\n\n'
          'CCTV Stream:\n'
          '{"name": "IP Camera", "source": "rtsp://user:pass@ip:port/stream", "id": "CAM-006"}',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('OK'),
          ),
        ],
      ),
    );
  }
}

class CameraConfig {
  final String name;
  final dynamic source; // int for local webcam, String for URL
  final int width;
  final int height;
  final String id;
  final String status;

  CameraConfig({
    required this.name,
    required this.source,
    required this.width,
    required this.height,
    required this.id,
    required this.status,
  });

  factory CameraConfig.fromJson(Map<String, dynamic> json) {
    return CameraConfig(
      name: json['name'] ?? 'Unknown Camera',
      source: json['source'],
      width: json['width'] ?? 640,
      height: json['height'] ?? 480,
      id: json['id'] ?? 'CAM-000',
      status: json['status'] ?? 'Unknown',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'name': name,
      'source': source,
      'width': width,
      'height': height,
      'id': id,
      'status': status,
    };
  }
}
