import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

class RealTimeDetectionPage extends StatefulWidget {
  const RealTimeDetectionPage({super.key});

  @override
  State<RealTimeDetectionPage> createState() => _RealTimeDetectionPageState();
}

class _RealTimeDetectionPageState extends State<RealTimeDetectionPage> {
  final String baseUrl = "http://localhost:8000"; // Python backend URL
  bool isLoading = true;
  List<_CameraInfo> cameras = [];
  Timer? _refreshTimer;

  @override
  void initState() {
    super.initState();
    _loadCameras();
    _refreshTimer = Timer.periodic(const Duration(seconds: 10), (_) => _loadCameras());
  }

  @override
  void dispose() {
    _refreshTimer?.cancel();
    super.dispose();
  }

  Future<void> _loadCameras() async {
    try {
      // Prefer rich /api endpoints (streaming support)
      final resp = await http.get(Uri.parse('$baseUrl/api/cameras'));
      if (resp.statusCode == 200) {
        final List<dynamic> data = json.decode(resp.body);
        final list = data.map((e) => _CameraInfo.fromJson(e)).toList();
        setState(() {
          cameras = list;
          isLoading = false;
        });
        // Ensure local cameras are started
        for (final cam in list) {
          if (cam.idx != null && cam.statusText == 'Active') {
            // Start only if backend thread is stopped
            if (cam.runtimeStatus != 'running') {
              _startCamera(cam.idx!);
            }
          }
        }
        return;
      }
    } catch (_) {}

    // Fallback to simple list (no streaming). Use /cameras and build minimal tiles.
    try {
      final resp = await http.get(Uri.parse('$baseUrl/cameras'));
      if (resp.statusCode == 200) {
        final List<dynamic> data = json.decode(resp.body);
        setState(() {
          cameras = data.map((e) => _CameraInfo.fallbackFromJson(e)).toList();
          isLoading = false;
        });
        return;
      }
    } catch (_) {}

    // If all fails, show one local webcam tile as placeholder
    setState(() {
      cameras = [
        _CameraInfo(
          id: 'CAM-LOCAL',
          name: 'Local Webcam',
          source: '0',
          statusText: 'Active',
          width: 640,
          height: 480,
          idx: 0,
          runtimeStatus: 'stopped',
        ),
      ];
      isLoading = false;
    });
  }

  Future<void> _startCamera(int idx) async {
    try {
      await http.post(Uri.parse('$baseUrl/api/camera/$idx/start'));
    } catch (_) {}
  }

  Future<void> _stopCamera(int idx) async {
    try {
      await http.post(Uri.parse('$baseUrl/api/camera/$idx/stop'));
    } catch (_) {}
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
              child: const Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    "Real-Time\nDetection",
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 28,
                      fontWeight: FontWeight.bold,
                      height: 1.2,
                    ),
                  ),
                  SizedBox(height: 6),
                  Text(
                    "Available cameras with real-time face detection",
                    style: TextStyle(
                      color: Colors.white70,
                      fontSize: 14,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 20),
            Expanded(
              child: isLoading
                  ? const Center(
                      child: CircularProgressIndicator(
                        valueColor: AlwaysStoppedAnimation<Color>(Colors.lightBlueAccent),
                      ),
                    )
                  : GridView.builder(
                      itemCount: cameras.length,
                      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                        crossAxisCount: 2,
                        crossAxisSpacing: 12,
                        mainAxisSpacing: 12,
                      ),
                      itemBuilder: (context, index) {
                        final cam = cameras[index];
                        return _CameraTile(
                          baseUrl: baseUrl,
                          camera: cam,
                          onStart: cam.idx != null ? () => _startCamera(cam.idx!) : null,
                          onStop: cam.idx != null ? () => _stopCamera(cam.idx!) : null,
                        );
                      },
                    ),
            ),
          ],
        ),
      ),
    );
  }
}

class _CameraInfo {
  final String id;
  final String name;
  final String? statusText; // Active/Offline
  final String? source; // stringified to be safe
  final int? width;
  final int? height;
  final int? idx; // backend index for /api endpoints
  final String? runtimeStatus; // running/stopped

  _CameraInfo({
    required this.id,
    required this.name,
    this.statusText,
    this.source,
    this.width,
    this.height,
    this.idx,
    this.runtimeStatus,
  });

  factory _CameraInfo.fromJson(Map<String, dynamic> json) {
    return _CameraInfo(
      id: (json['id'] ?? 'CAM-${DateTime.now().millisecondsSinceEpoch}').toString(),
      name: (json['name'] ?? 'Camera').toString(),
      statusText: (json['status'] ?? 'Active').toString(),
      source: json['source']?.toString(),
      width: json['width'] is int ? json['width'] as int : int.tryParse('${json['width']}'),
      height: json['height'] is int ? json['height'] as int : int.tryParse('${json['height']}'),
      idx: json['_idx'] is int ? json['_idx'] as int : int.tryParse('${json['_idx']}'),
      runtimeStatus: json['_status']?.toString(),
    );
  }

  factory _CameraInfo.fallbackFromJson(Map<String, dynamic> json) {
    return _CameraInfo(
      id: (json['id'] ?? 'CAM-${DateTime.now().millisecondsSinceEpoch}').toString(),
      name: (json['name'] ?? 'Camera').toString(),
      statusText: (json['status'] ?? 'Active').toString(),
      source: json['source']?.toString(),
      width: json['width'] is int ? json['width'] as int : int.tryParse('${json['width']}'),
      height: json['height'] is int ? json['height'] as int : int.tryParse('${json['height']}'),
      idx: null,
      runtimeStatus: null,
    );
  }
}

class _CameraTile extends StatefulWidget {
  final String baseUrl;
  final _CameraInfo camera;
  final VoidCallback? onStart;
  final VoidCallback? onStop;

  const _CameraTile({
    super.key,
    required this.baseUrl,
    required this.camera,
    this.onStart,
    this.onStop,
  });

  @override
  State<_CameraTile> createState() => _CameraTileState();
}

class _CameraTileState extends State<_CameraTile> {
  Uint8List? _frameBytes;
  Timer? _timer;
  bool _starting = false;

  @override
  void initState() {
    super.initState();
    _maybeAutoStart();
    _beginPolling();
  }

  void _maybeAutoStart() {
    if (widget.camera.idx != null && widget.camera.runtimeStatus != 'running' && (widget.camera.statusText == 'Active')) {
      _starting = true;
      widget.onStart?.call();
      Future.delayed(const Duration(milliseconds: 600), () {
        if (mounted) setState(() => _starting = false);
      });
    }
  }

  void _beginPolling() {
    _timer?.cancel();
    _timer = Timer.periodic(const Duration(milliseconds: 300), (_) => _fetchFrame());
  }

  Future<void> _fetchFrame() async {
    if (!mounted) return;
    // Prefer /api snapshot when idx available
    final int? idx = widget.camera.idx;
    String? url;
    if (idx != null) {
      url = '${widget.baseUrl}/api/camera/$idx/snapshot?t=${DateTime.now().millisecondsSinceEpoch}';
    }
    if (url == null) {
      // No streaming available from simple_api; skip fetching
      return;
    }
    try {
      final resp = await http.get(Uri.parse(url)).timeout(const Duration(seconds: 2));
      if (resp.statusCode == 200 && resp.bodyBytes.isNotEmpty) {
        setState(() {
          _frameBytes = resp.bodyBytes;
        });
      }
    } catch (_) {}
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final cam = widget.camera;
    return ClipRRect(
      borderRadius: BorderRadius.circular(12),
      child: Stack(
        children: [
          Container(color: const Color(0xFF2B2F3B)),
          if (_frameBytes != null)
            Positioned.fill(
              child: Image.memory(
                _frameBytes!,
                gaplessPlayback: true,
                fit: BoxFit.cover,
                filterQuality: FilterQuality.low,
              ),
            )
          else
            const Positioned.fill(
              child: Center(
                child: Icon(Icons.videocam, color: Colors.white38, size: 40),
              ),
            ),

          // Gradient overlay bottom
          Positioned(
            left: 0,
            right: 0,
            bottom: 0,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
              decoration: const BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.bottomCenter,
                  end: Alignment.topCenter,
                  colors: [Color(0xAA000000), Color(0x00000000)],
                ),
              ),
              child: Row(
                children: [
                  Container(
                    width: 8,
                    height: 8,
                    decoration: BoxDecoration(
                      color: (cam.statusText == 'Active') ? const Color(0xFF39D98A) : const Color(0xFFFFB020),
                      shape: BoxShape.circle,
                    ),
                  ),
                  const SizedBox(width: 6),
                  Expanded(
                    child: Text(
                      cam.name,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.w600),
                    ),
                  ),
                  if (cam.idx != null) ...[
                    IconButton(
                      onPressed: widget.onStart,
                      icon: Icon(Icons.play_arrow, size: 18, color: _starting ? Colors.white30 : Colors.white70),
                      tooltip: 'Start',
                      padding: EdgeInsets.zero,
                      constraints: const BoxConstraints(),
                    ),
                    const SizedBox(width: 6),
                    IconButton(
                      onPressed: widget.onStop,
                      icon: const Icon(Icons.stop, size: 18, color: Colors.white70),
                      tooltip: 'Stop',
                      padding: EdgeInsets.zero,
                      constraints: const BoxConstraints(),
                    ),
                  ],
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
