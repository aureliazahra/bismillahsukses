import 'package:flutter/material.dart';
import 'dart:async';
import 'dart:typed_data';
import '../config/camera_config.dart';
import '../services/mjpeg_service.dart';

class RealTimeDetectionPage extends StatefulWidget {
  const RealTimeDetectionPage({super.key});

  @override
  State<RealTimeDetectionPage> createState() => _RealTimeDetectionPageState();
}

class _RealTimeDetectionPageState extends State<RealTimeDetectionPage> {
  // Camera configuration - easily configurable for future scaling
  final List<CameraConfig> cameras = CameraPresets.defaultCameras;

  // Track streaming state for each camera
  final Map<String, bool> _streamingStates = {};
  final Map<String, StreamSubscription> _streamSubscriptions = {};
  final Map<String, Uint8List?> _lastFrames = {};

  @override
  void initState() {
    super.initState();
    // Initialize all cameras as stopped
    for (var camera in cameras) {
      _streamingStates[camera.id] = false;
      _lastFrames[camera.id] = null;
    }
  }

  @override
  void dispose() {
    // Clean up all stream subscriptions
    for (var subscription in _streamSubscriptions.values) {
      subscription.cancel();
    }
    super.dispose();
  }

  void _toggleStream(String cameraId) {
    setState(() {
      if (_streamingStates[cameraId] == true) {
        // Stop the stream
        _stopStream(cameraId);
      } else {
        // Start the stream
        _startStream(cameraId);
      }
    });
  }

  void _startStream(String cameraId) {
    final camera = cameras.firstWhere((c) => c.id == cameraId);
    
    try {
      final subscription = _createMjpegStream(camera.url, cameraId);
      _streamSubscriptions[cameraId] = subscription;
      _streamingStates[cameraId] = true;
    } catch (e) {
      print('Failed to start stream for camera $cameraId: $e');
      setState(() {
        _streamingStates[cameraId] = false;
      });
    }
  }

  void _stopStream(String cameraId) {
    final subscription = _streamSubscriptions[cameraId];
    if (subscription != null) {
      subscription.cancel();
      _streamSubscriptions.remove(cameraId);
    }
    _streamingStates[cameraId] = false;
  }

  StreamSubscription _createMjpegStream(String url, String cameraId) {
    final stream = MjpegService.createOptimalStream(
      url,
      timeout: const Duration(seconds: 10),
      refreshRate: const Duration(milliseconds: 100),
    );
    
    return stream.listen(
      (frame) {
        if (_streamingStates[cameraId] == true) {
          setState(() {
            _lastFrames[cameraId] = frame;
          });
        }
      },
      onError: (error) {
        print('Error streaming camera $cameraId: $error');
        setState(() {
          _streamingStates[cameraId] = false;
        });
      },
    );
  }

  void _showFullscreen(String cameraId) {
    final camera = cameras.firstWhere((c) => c.id == cameraId);
    final isStreaming = _streamingStates[cameraId] == true;
    
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (context) => CameraFullscreenView(
          camera: camera,
          isStreaming: isStreaming,
          lastFrame: _lastFrames[cameraId],
          onToggleStream: (cameraId) => _toggleStream(cameraId),
        ),
      ),
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
                    "Real-Time\nCCTV Monitoring",
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 28,
                      fontWeight: FontWeight.bold,
                      height: 1.2,
                    ),
                  ),
                  const SizedBox(height: 6),
                  Text(
                    "${cameras.length} cameras available • Click any card to expand",
                    style: const TextStyle(
                      color: Colors.white70,
                      fontSize: 14,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 20),

            // Camera Grid
            Expanded(
              child: GridView.builder(
                itemCount: cameras.length,
                gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                  crossAxisCount: 2,
                  crossAxisSpacing: 16,
                  mainAxisSpacing: 16,
                  childAspectRatio: 1.2,
                ),
                itemBuilder: (context, index) {
                  final camera = cameras[index];
                  final isStreaming = _streamingStates[camera.id] == true;
                  
                  return CameraCard(
                    camera: camera,
                    isStreaming: isStreaming,
                    lastFrame: _lastFrames[camera.id],
                    onToggleStream: _toggleStream,
                    onFullscreen: _showFullscreen,
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

class CameraCard extends StatelessWidget {
  final CameraConfig camera;
  final bool isStreaming;
  final Uint8List? lastFrame;
  final Function(String) onToggleStream;
  final Function(String) onFullscreen;

  const CameraCard({
    super.key,
    required this.camera,
    required this.isStreaming,
    this.lastFrame,
    required this.onToggleStream,
    required this.onFullscreen,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: () => onFullscreen(camera.id),
      child: Container(
        decoration: BoxDecoration(
          color: const Color(0xFF1A2332),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: isStreaming ? const Color(0xFF4AB1EB) : Colors.grey[700]!,
            width: 2,
          ),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.3),
              blurRadius: 10,
              offset: const Offset(0, 4),
            ),
          ],
        ),
        child: Column(
          children: [
            // Camera Feed Area
            Expanded(
              child: Container(
                width: double.infinity,
                margin: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.black,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(12),
                  child: isStreaming && lastFrame != null
                      ? Image.memory(
                          lastFrame!,
                          fit: BoxFit.cover,
                          width: double.infinity,
                          height: double.infinity,
                          errorBuilder: (context, error, stackTrace) {
                            return _buildPlaceholder();
                          },
                        )
                      : _buildPlaceholder(),
                ),
              ),
            ),

            // Camera Info and Controls
            Container(
              padding: const EdgeInsets.all(12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Camera Name and Status
                  Row(
                    children: [
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              camera.name,
                              style: const TextStyle(
                                color: Colors.white,
                                fontSize: 16,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                            Text(
                              camera.location,
                              style: TextStyle(
                                color: Colors.grey[400],
                                fontSize: 12,
                              ),
                            ),
                          ],
                        ),
                      ),
                      Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 8,
                          vertical: 4,
                        ),
                        decoration: BoxDecoration(
                          color: isStreaming 
                              ? const Color(0xFF4AB1EB)
                              : Colors.grey[600],
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Text(
                          isStreaming ? 'LIVE' : 'STOPPED',
                          style: TextStyle(
                            color: Colors.white,
                            fontSize: 10,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                    ],
                  ),
                  
                  const SizedBox(height: 12),
                  
                  // Control Buttons
                  Row(
                    children: [
                      Expanded(
                        child: ElevatedButton(
                          onPressed: () => onToggleStream(camera.id),
                          style: ElevatedButton.styleFrom(
                            backgroundColor: isStreaming 
                                ? const Color(0xFFE74C3C)
                                : const Color(0xFF27AE60),
                            foregroundColor: Colors.white,
                            padding: const EdgeInsets.symmetric(vertical: 8),
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(8),
                            ),
                          ),
                          child: Text(
                            isStreaming ? 'STOP' : 'START',
                            style: const TextStyle(
                              fontSize: 12,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ),
                      ),
                      const SizedBox(width: 8),
                      IconButton(
                        onPressed: () => onFullscreen(camera.id),
                        icon: const Icon(
                          Icons.fullscreen,
                          color: Color(0xFF4AB1EB),
                          size: 20,
                        ),
                        tooltip: 'Fullscreen',
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildPlaceholder() {
    return Container(
      color: Colors.grey[900],
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.videocam_off,
            size: 48,
            color: Colors.grey[600],
          ),
          const SizedBox(height: 8),
          Text(
            'Camera Stopped',
            style: TextStyle(
              color: Colors.grey[600],
              fontSize: 14,
              fontWeight: FontWeight.w500,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            'Click START to begin streaming',
            style: TextStyle(
              color: Colors.grey[500],
              fontSize: 12,
            ),
          ),
        ],
      ),
    );
  }
}

class CameraFullscreenView extends StatefulWidget {
  final CameraConfig camera;
  final bool isStreaming;
  final Uint8List? lastFrame;
  final Function(String) onToggleStream;

  const CameraFullscreenView({
    super.key,
    required this.camera,
    required this.isStreaming,
    this.lastFrame,
    required this.onToggleStream,
  });

  @override
  State<CameraFullscreenView> createState() => _CameraFullscreenViewState();
}

class _CameraFullscreenViewState extends State<CameraFullscreenView> {
  late bool _isStreaming;
  Uint8List? _lastFrame;

  @override
  void initState() {
    super.initState();
    _isStreaming = widget.isStreaming;
    _lastFrame = widget.lastFrame;
  }

  void _toggleStream() {
    setState(() {
      if (_isStreaming) {
        _stopStream();
      } else {
        _startStream();
      }
    });
  }

  void _startStream() {
    _isStreaming = true;
    
    final stream = MjpegService.createOptimalStream(
      widget.camera.url,
      timeout: const Duration(seconds: 10),
      refreshRate: const Duration(milliseconds: 100),
    );
    
    stream.listen(
      (frame) {
        if (_isStreaming) {
          setState(() {
            _lastFrame = frame;
          });
        }
      },
      onError: (error) {
        print('Error streaming camera ${widget.camera.id}: $error');
        setState(() {
          _isStreaming = false;
        });
      },
    );
  }

  void _stopStream() {
    _isStreaming = false;
  }

  @override
  void dispose() {
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      appBar: AppBar(
        backgroundColor: Colors.black,
        foregroundColor: Colors.white,
        title: Text('${widget.camera.name} - Fullscreen'),
        actions: [
          Container(
            margin: const EdgeInsets.only(right: 16),
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
            decoration: BoxDecoration(
              color: _isStreaming 
                  ? const Color(0xFF4AB1EB)
                  : Colors.grey[600],
              borderRadius: BorderRadius.circular(16),
            ),
            child: Text(
              _isStreaming ? 'LIVE' : 'STOPPED',
              style: const TextStyle(
                color: Colors.white,
                fontSize: 12,
                fontWeight: FontWeight.bold,
              ),
            ),
          ),
          IconButton(
            onPressed: _toggleStream,
            icon: Icon(
              _isStreaming ? Icons.stop : Icons.play_arrow,
              color: _isStreaming ? const Color(0xFFE74C3C) : const Color(0xFF27AE60),
            ),
            tooltip: _isStreaming ? 'Stop Stream' : 'Start Stream',
          ),
        ],
      ),
      body: Center(
        child: _isStreaming && _lastFrame != null
            ? Image.memory(
                _lastFrame!,
                fit: BoxFit.contain,
                errorBuilder: (context, error, stackTrace) {
                  return _buildFullscreenPlaceholder();
                },
              )
            : _buildFullscreenPlaceholder(),
      ),
    );
  }

  Widget _buildFullscreenPlaceholder() {
    return Container(
      color: Colors.grey[900],
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.videocam_off,
            size: 96,
            color: Colors.grey[600],
          ),
          const SizedBox(height: 24),
          Text(
            'Camera Stopped',
            style: TextStyle(
              color: Colors.grey[600],
              fontSize: 28,
              fontWeight: FontWeight.w500,
            ),
          ),
          const SizedBox(height: 12),
          Text(
            'Click the play button to begin streaming',
            style: TextStyle(
              color: Colors.grey[500],
              fontSize: 16,
            ),
          ),
          const SizedBox(height: 32),
          ElevatedButton.icon(
            onPressed: _toggleStream,
            icon: const Icon(Icons.play_arrow),
            label: const Text('START STREAM'),
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFF27AE60),
              foregroundColor: Colors.white,
              padding: const EdgeInsets.symmetric(
                horizontal: 24,
                vertical: 16,
              ),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(8),
              ),
            ),
          ),
        ],
      ),
    );
  }
}


