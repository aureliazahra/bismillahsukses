import 'package:flutter/material.dart';
import 'dart:async';
import 'dart:typed_data';
import '../config/camera_config.dart';
import '../config/local_camera_config.dart';
import '../services/mjpeg_service.dart';
import '../services/local_camera_stream_service.dart';

class RealTimeDetectionPage extends StatefulWidget {
  const RealTimeDetectionPage({super.key});

  @override
  State<RealTimeDetectionPage> createState() => _RealTimeDetectionPageState();
}

class _RealTimeDetectionPageState extends State<RealTimeDetectionPage> {
  // Camera configurations - both IP cameras and local cameras
  final List<CameraConfig> ipCameras = CameraPresets.defaultCameras;
  final List<LocalCameraConfig> localCameras = LocalCameraPresets.getAllPresets();
  
  // Combined list for display
  late List<dynamic> allCameras;

  // Track streaming state for each camera
  final Map<String, bool> _streamingStates = {};
  final Map<String, StreamSubscription> _streamSubscriptions = {};
  final Map<String, Uint8List?> _lastFrames = {};
  final Map<String, Timer> _localCameraTimers = {};

  @override
  void initState() {
    super.initState();
    _initializeCameras();
  }

  Future<void> _initializeCameras() async {
    // Initialize local camera service
    await LocalCameraService.initialize();
    
    // Combine both camera types
    allCameras = [...ipCameras, ...localCameras];
    
    // Initialize all cameras as stopped
    for (var camera in allCameras) {
      _streamingStates[camera.id] = false;
      _lastFrames[camera.id] = null;
    }
    
    setState(() {});
  }

  @override
  void dispose() {
    // Clean up all stream subscriptions
    for (var subscription in _streamSubscriptions.values) {
      subscription.cancel();
    }
    
    // Clean up local camera timers
    for (var timer in _localCameraTimers.values) {
      timer.cancel();
    }
    
    // Dispose all local cameras
    LocalCameraStreamService.disposeAll();
    
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
    try {
      // Check if it's a local camera
      final localCamera = localCameras.where((c) => c.id == cameraId).firstOrNull;
      if (localCamera != null) {
        _startLocalCameraStream(localCamera);
      } else {
        // It's an IP camera
        final ipCamera = ipCameras.firstWhere((c) => c.id == cameraId);
        _startIpCameraStream(ipCamera);
      }
    } catch (e) {
      print('Failed to start stream for camera $cameraId: $e');
      setState(() {
        _streamingStates[cameraId] = false;
      });
    }
  }

  void _startLocalCameraStream(LocalCameraConfig camera) async {
    final success = await camera.startStream();
    if (success) {
      setState(() {
        _streamingStates[camera.id] = true;
      });
      
      // Set up timer to update frames
      final timer = Timer.periodic(const Duration(milliseconds: 200), (_) {
        if (_streamingStates[camera.id] == true) {
          final frame = camera.lastFrame;
          if (frame != null) {
            setState(() {
              _lastFrames[camera.id] = frame;
            });
          }
        }
      });
      
      _localCameraTimers[camera.id] = timer;
    }
  }

  void _startIpCameraStream(CameraConfig camera) {
    final subscription = _createMjpegStream(camera.url, camera.id);
    _streamSubscriptions[camera.id] = subscription;
    _streamingStates[camera.id] = true;
  }

  void _stopStream(String cameraId) {
    // Check if it's a local camera
    final localCamera = localCameras.where((c) => c.id == cameraId).firstOrNull;
    if (localCamera != null) {
      _stopLocalCameraStream(cameraId);
    } else {
      // It's an IP camera
      _stopIpCameraStream(cameraId);
    }
  }

  void _stopLocalCameraStream(String cameraId) {
    // Stop timer
    final timer = _localCameraTimers[cameraId];
    if (timer != null) {
      timer.cancel();
      _localCameraTimers.remove(cameraId);
    }
    
    // Stop local camera stream
    LocalCameraStreamService.stopStream(cameraId);
    
    setState(() {
      _streamingStates[cameraId] = false;
    });
  }

  void _stopIpCameraStream(String cameraId) {
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
    final camera = allCameras.firstWhere((c) => c.id == cameraId);
    final isStreaming = _streamingStates[cameraId] == true;
    
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (context) => CameraFullscreenView(
          camera: camera,
          isStreaming: isStreaming,
          lastFrame: _lastFrames[cameraId],
          onToggleStream: (cameraId) => _toggleStream(cameraId),
          isLocalCamera: localCameras.any((c) => c.id == cameraId),
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
                    "${allCameras.length} cameras available • Click any card to expand",
                    style: const TextStyle(
                      color: Colors.white70,
                      fontSize: 14,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                        decoration: BoxDecoration(
                          color: Colors.white.withOpacity(0.2),
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Text(
                          '${ipCameras.length} IP Cameras',
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 12,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                      ),
                      const SizedBox(width: 8),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                        decoration: BoxDecoration(
                          color: Colors.white.withOpacity(0.2),
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Text(
                          '${localCameras.length} Local Cameras',
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 12,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
            const SizedBox(height: 20),

            // Camera Grid
            Expanded(
              child: GridView.builder(
                itemCount: allCameras.length,
                gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                  crossAxisCount: 2,
                  crossAxisSpacing: 16,
                  mainAxisSpacing: 16,
                  childAspectRatio: 1.2,
                ),
                itemBuilder: (context, index) {
                  final camera = allCameras[index];
                  final isStreaming = _streamingStates[camera.id] == true;
                  final isLocalCamera = localCameras.any((c) => c.id == camera.id);
                  
                  return CameraCard(
                    camera: camera,
                    isStreaming: isStreaming,
                    lastFrame: _lastFrames[camera.id],
                    onToggleStream: _toggleStream,
                    onFullscreen: _showFullscreen,
                    isLocalCamera: isLocalCamera,
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
  final dynamic camera;
  final bool isStreaming;
  final Uint8List? lastFrame;
  final Function(String) onToggleStream;
  final Function(String) onFullscreen;
  final bool isLocalCamera;

  const CameraCard({
    super.key,
    required this.camera,
    required this.isStreaming,
    this.lastFrame,
    required this.onToggleStream,
    required this.onFullscreen,
    required this.isLocalCamera,
  });

  String get cameraName => camera.name ?? 'Unknown Camera';
  String get cameraLocation => camera.location ?? 'Unknown Location';

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: () => onFullscreen(camera.id),
      child: Container(
        decoration: BoxDecoration(
          color: const Color(0xFF1A2332),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: isStreaming 
                ? (isLocalCamera ? const Color(0xFF27AE60) : const Color(0xFF4AB1EB))
                : Colors.grey[700]!,
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
                              cameraName,
                              style: const TextStyle(
                                color: Colors.white,
                                fontSize: 16,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                            Text(
                              cameraLocation,
                              style: TextStyle(
                                color: Colors.grey[400],
                                fontSize: 12,
                              ),
                            ),
                            if (isLocalCamera)
                              Container(
                                margin: const EdgeInsets.only(top: 2),
                                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                decoration: BoxDecoration(
                                  color: const Color(0xFF27AE60).withOpacity(0.2),
                                  borderRadius: BorderRadius.circular(4),
                                  border: Border.all(
                                    color: const Color(0xFF27AE60),
                                    width: 1,
                                  ),
                                ),
                                child: Text(
                                  'LOCAL',
                                  style: TextStyle(
                                    color: const Color(0xFF27AE60),
                                    fontSize: 8,
                                    fontWeight: FontWeight.bold,
                                  ),
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
                              ? (isLocalCamera ? const Color(0xFF27AE60) : const Color(0xFF4AB1EB))
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
                                : (isLocalCamera ? const Color(0xFF27AE60) : const Color(0xFF4AB1EB)),
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
                        icon: Icon(
                          Icons.fullscreen,
                          color: isLocalCamera ? const Color(0xFF27AE60) : const Color(0xFF4AB1EB),
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
            isLocalCamera ? Icons.videocam : Icons.videocam_off,
            size: 48,
            color: isLocalCamera ? const Color(0xFF27AE60) : Colors.grey[600],
          ),
          const SizedBox(height: 8),
          Text(
            isLocalCamera ? 'Local Camera Ready' : 'Camera Stopped',
            style: TextStyle(
              color: isLocalCamera ? const Color(0xFF27AE60) : Colors.grey[600],
              fontSize: 14,
              fontWeight: FontWeight.w500,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            isLocalCamera 
                ? 'Click START to begin streaming'
                : 'Click START to begin streaming',
            style: TextStyle(
              color: isLocalCamera ? const Color(0xFF27AE60).withOpacity(0.7) : Colors.grey[500],
              fontSize: 12,
            ),
          ),
        ],
      ),
    );
  }
}

class CameraFullscreenView extends StatefulWidget {
  final dynamic camera;
  final bool isStreaming;
  final Uint8List? lastFrame;
  final Function(String) onToggleStream;
  final bool isLocalCamera;

  const CameraFullscreenView({
    super.key,
    required this.camera,
    required this.isStreaming,
    this.lastFrame,
    required this.onToggleStream,
    required this.isLocalCamera,
  });

  @override
  State<CameraFullscreenView> createState() => _CameraFullscreenViewState();
}

class _CameraFullscreenViewState extends State<CameraFullscreenView> {
  late bool _isStreaming;
  Uint8List? _lastFrame;
  StreamSubscription? _streamSubscription;
  Timer? _localCameraTimer;

  @override
  void initState() {
    super.initState();
    _isStreaming = widget.isStreaming;
    _lastFrame = widget.lastFrame;
    
    if (_isStreaming) {
      _startStream();
    }
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
    
    if (widget.isLocalCamera) {
      _startLocalCameraStream();
    } else {
      _startIpCameraStream();
    }
  }

  void _startLocalCameraStream() {
    // Start local camera stream
    final localCamera = widget.camera as LocalCameraConfig;
    localCamera.startStream();
    
    // Set up timer to update frames
    _localCameraTimer = Timer.periodic(const Duration(milliseconds: 200), (_) {
      if (_isStreaming) {
        final frame = localCamera.lastFrame;
        if (frame != null) {
          setState(() {
            _lastFrame = frame;
          });
        }
      }
    });
  }

  void _startIpCameraStream() {
    // Start IP camera stream
    final ipCamera = widget.camera as CameraConfig;
    final stream = MjpegService.createOptimalStream(
      ipCamera.url,
      timeout: const Duration(seconds: 10),
      refreshRate: const Duration(milliseconds: 100),
    );
    
    _streamSubscription = stream.listen(
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
    
    if (widget.isLocalCamera) {
      _stopLocalCameraStream();
    } else {
      _stopIpCameraStream();
    }
  }

  void _stopLocalCameraStream() {
    _localCameraTimer?.cancel();
    _localCameraTimer = null;
    
    final localCamera = widget.camera as LocalCameraConfig;
    localCamera.stopStream();
  }

  void _stopIpCameraStream() {
    _streamSubscription?.cancel();
    _streamSubscription = null;
  }

  @override
  void dispose() {
    _stopStream();
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
          if (widget.isLocalCamera)
            Container(
              margin: const EdgeInsets.only(right: 8),
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              decoration: BoxDecoration(
                color: const Color(0xFF27AE60).withOpacity(0.2),
                borderRadius: BorderRadius.circular(8),
                border: Border.all(
                  color: const Color(0xFF27AE60),
                  width: 1,
                ),
              ),
              child: Text(
                'LOCAL',
                style: TextStyle(
                  color: const Color(0xFF27AE60),
                  fontSize: 10,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
          Container(
            margin: const EdgeInsets.only(right: 16),
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
            decoration: BoxDecoration(
              color: _isStreaming 
                  ? (widget.isLocalCamera ? const Color(0xFF27AE60) : const Color(0xFF4AB1EB))
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
              color: _isStreaming 
                  ? const Color(0xFFE74C3C) 
                  : (widget.isLocalCamera ? const Color(0xFF27AE60) : const Color(0xFF4AB1EB)),
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
            widget.isLocalCamera ? Icons.videocam : Icons.videocam_off,
            size: 96,
            color: widget.isLocalCamera ? const Color(0xFF27AE60) : Colors.grey[600],
          ),
          const SizedBox(height: 24),
          Text(
            widget.isLocalCamera ? 'Local Camera Ready' : 'Camera Stopped',
            style: TextStyle(
              color: widget.isLocalCamera ? const Color(0xFF27AE60) : Colors.grey[600],
              fontSize: 28,
              fontWeight: FontWeight.w500,
            ),
          ),
          const SizedBox(height: 12),
          Text(
            'Click the play button to begin streaming',
            style: TextStyle(
              color: widget.isLocalCamera 
                  ? const Color(0xFF27AE60).withOpacity(0.7) 
                  : Colors.grey[500],
              fontSize: 16,
            ),
          ),
          const SizedBox(height: 32),
          ElevatedButton.icon(
            onPressed: _toggleStream,
            icon: const Icon(Icons.play_arrow),
            label: const Text('START STREAM'),
            style: ElevatedButton.styleFrom(
              backgroundColor: widget.isLocalCamera 
                  ? const Color(0xFF27AE60) 
                  : const Color(0xFF4AB1EB),
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


