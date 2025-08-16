import 'dart:async';
import 'dart:typed_data';
import 'package:camera/camera.dart';
import '../config/local_camera_config.dart';

class LocalCameraStreamService {
  static final Map<String, CameraController> _controllers = {};
  static final Map<String, Timer> _frameTimers = {};
  static final Map<String, Uint8List?> _lastFrames = {};

  /// Default interval between snapshots in ms
  static const int _defaultIntervalMs = 200;

  /// Initialize a local camera
  static Future<CameraController?> initializeCamera(
    LocalCameraConfig config,
    CameraDescription cameraDescription,
  ) async {
    try {
      final controller = CameraController(
        cameraDescription,
        config.resolution,
        enableAudio: false,
        imageFormatGroup: ImageFormatGroup.jpeg,
      );

      await controller.initialize();

      _controllers[config.id] = controller;
      print('Local camera ${config.id} initialized successfully');

      return controller;
    } catch (e) {
      print('Failed to initialize local camera ${config.id}: $e');
      return null;
    }
  }

  /// Start streaming from a local camera (simulated by periodic snapshots)
  static Future<bool> startStream(LocalCameraConfig config) async {
    try {
      final cameras = await availableCameras();
      CameraDescription? targetCamera;

      if (config.deviceIndex != null && config.deviceIndex! < cameras.length) {
        targetCamera = cameras[config.deviceIndex!];
      } else {
        targetCamera = cameras.firstWhere(
          (camera) => camera.lensDirection == config.lensDirection,
          orElse: () => cameras.first,
        );
      }

      if (targetCamera == null) {
        print('No suitable camera found for ${config.id}');
        return false;
      }

      final controller = await initializeCamera(config, targetCamera);
      if (controller == null) return false;

      // Use default interval (200 ms) or override if config has a field
      final intervalMs = _defaultIntervalMs;

      // Take snapshots periodically
      final timer = Timer.periodic(
        Duration(milliseconds: intervalMs),
        (_) async {
          try {
            if (!controller.value.isInitialized) return;
            final picture = await controller.takePicture();
            final bytes = await picture.readAsBytes();
            _lastFrames[config.id] = bytes;
          } catch (e) {
            print('Error capturing frame for ${config.id}: $e');
          }
        },
      );

      _frameTimers[config.id] = timer;
      print('Local camera stream started for ${config.id}');
      return true;
    } catch (e) {
      print('Failed to start local camera stream for ${config.id}: $e');
      return false;
    }
  }

  /// Stop streaming from a local camera
  static Future<void> stopStream(String cameraId) async {
    try {
      // Stop periodic timer
      final timer = _frameTimers[cameraId];
      if (timer != null) {
        timer.cancel();
        _frameTimers.remove(cameraId);
      }

      // Stop controller
      final controller = _controllers[cameraId];
      if (controller != null) {
        await controller.dispose();
        _controllers.remove(cameraId);
      }

      // Clear last frame
      _lastFrames.remove(cameraId);

      print('Local camera stream stopped for $cameraId');
    } catch (e) {
      print('Error stopping local camera stream for $cameraId: $e');
    }
  }

  /// Get the last frame from a local camera
  static Uint8List? getLastFrame(String cameraId) {
    return _lastFrames[cameraId];
  }

  /// Check if a local camera is streaming
  static bool isStreaming(String cameraId) {
    return _controllers.containsKey(cameraId) &&
        _frameTimers.containsKey(cameraId);
  }

  /// Get camera controller
  static CameraController? getController(String cameraId) {
    return _controllers[cameraId];
  }

  /// Take a photo from the camera
  static Future<Uint8List?> takePhoto(String cameraId) async {
    try {
      final controller = _controllers[cameraId];
      if (controller == null) return null;

      final image = await controller.takePicture();
      return await image.readAsBytes();
    } catch (e) {
      print('Failed to take photo from camera $cameraId: $e');
      return null;
    }
  }

  /// Get camera info
  static Map<String, dynamic> getCameraInfo(String cameraId) {
    final controller = _controllers[cameraId];
    if (controller == null) return {};

    return {
      'isInitialized': controller.value.isInitialized,
      'isRecording': controller.value.isRecordingVideo,
      'isStreaming': isStreaming(cameraId),
      'hasError': controller.value.hasError,
      'errorDescription': controller.value.errorDescription,
    };
  }

  /// Get all active camera IDs
  static List<String> getActiveCameraIds() {
    return _controllers.keys.toList();
  }

  /// Dispose all cameras
  static Future<void> disposeAll() async {
    final cameraIds = List<String>.from(_controllers.keys);

    for (final cameraId in cameraIds) {
      await stopStream(cameraId);
    }

    _controllers.clear();
    _frameTimers.clear();
    _lastFrames.clear();

    print('All local camera streams disposed');
  }

  /// Get camera status summary
  static Map<String, dynamic> getStatusSummary() {
    return {
      'activeCameras': _controllers.length,
      'activeStreams': _frameTimers.length,
      'cameraIds': _controllers.keys.toList(),
      'streamingIds': _frameTimers.keys.toList(),
    };
  }
}

// Extension to add local camera functionality to LocalCameraConfig
extension LocalCameraConfigExtension on LocalCameraConfig {
  Future<bool> startStream() async {
    return await LocalCameraStreamService.startStream(this);
  }

  Future<void> stopStream() async {
    await LocalCameraStreamService.stopStream(id);
  }

  bool get isStreaming => LocalCameraStreamService.isStreaming(id);

  Uint8List? get lastFrame => LocalCameraStreamService.getLastFrame(id);

  Future<Uint8List?> takePhoto() async {
    return await LocalCameraStreamService.takePhoto(id);
  }

  Map<String, dynamic> get cameraInfo =>
      LocalCameraStreamService.getCameraInfo(id);
}
