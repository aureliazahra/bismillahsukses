// Local Camera Configuration for Webcam/Laptop Camera
// This uses the camera package to access local device cameras
// Different from MJPEG/RTSP which is for IP cameras

import 'package:camera/camera.dart';

class LocalCameraConfig {
  final String id;
  final String name;
  final String location;
  final String? description;
  final CameraLensDirection lensDirection;
  final ResolutionPreset resolution;
  final int? deviceIndex; // Specific camera device index

  const LocalCameraConfig({
    required this.id,
    required this.name,
    required this.location,
    this.description,
    this.lensDirection = CameraLensDirection.back,
    this.resolution = ResolutionPreset.high,
    this.deviceIndex,
  });

  // Factory method to create camera from JSON
  factory LocalCameraConfig.fromJson(Map<String, dynamic> json) {
    return LocalCameraConfig(
      id: json['id'] as String,
      name: json['name'] as String,
      location: json['location'] as String,
      description: json['description'] as String?,
      lensDirection: _parseLensDirection(json['lensDirection'] as String?),
      resolution: _parseResolution(json['resolution'] as String?),
      deviceIndex: json['deviceIndex'] as int?,
    );
  }

  // Convert to JSON
  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'location': location,
      'description': description,
      'lensDirection': lensDirection.name,
      'resolution': resolution.name,
      'deviceIndex': deviceIndex,
    };
  }

  // Helper method to parse lens direction
  static CameraLensDirection _parseLensDirection(String? direction) {
    switch (direction?.toLowerCase()) {
      case 'front':
        return CameraLensDirection.front;
      case 'back':
        return CameraLensDirection.back;
      case 'external':
        return CameraLensDirection.external;
      default:
        return CameraLensDirection.back;
    }
  }

  // Helper method to parse resolution
  static ResolutionPreset _parseResolution(String? resolution) {
    switch (resolution?.toLowerCase()) {
      case 'low':
        return ResolutionPreset.low;
      case 'medium':
        return ResolutionPreset.medium;
      case 'high':
        return ResolutionPreset.high;
      case 'veryhigh':
        return ResolutionPreset.veryHigh;
      case 'ultrahigh':
        return ResolutionPreset.ultraHigh;
      case 'max':
        return ResolutionPreset.max;
      default:
        return ResolutionPreset.high;
    }
  }

  @override
  String toString() {
    return 'LocalCameraConfig(id: $id, name: $name, location: $location, lens: ${lensDirection.name})';
  }
}

// Predefined local camera configurations
class LocalCameraPresets {
  // Default laptop webcam configuration
  static const LocalCameraConfig defaultWebcam = LocalCameraConfig(
    id: 'WEBCAM-001',
    name: 'Laptop Webcam',
    location: 'Built-in Camera',
    description: 'Default laptop webcam for local monitoring',
    lensDirection: CameraLensDirection.front,
    resolution: ResolutionPreset.high,
  );

  // External USB webcam configuration
  static const LocalCameraConfig externalWebcam = LocalCameraConfig(
    id: 'WEBCAM-002',
    name: 'External USB Camera',
    location: 'USB Connected Camera',
    description: 'External USB webcam for additional monitoring',
    lensDirection: CameraLensDirection.external,
    resolution: ResolutionPreset.high,
  );

  // High-resolution webcam for quality monitoring
  static const LocalCameraConfig hdWebcam = LocalCameraConfig(
    id: 'WEBCAM-003',
    name: 'HD Webcam',
    location: 'High-Definition Camera',
    description: 'High-resolution webcam for detailed monitoring',
    lensDirection: CameraLensDirection.back,
    resolution: ResolutionPreset.ultraHigh,
  );

  // Security-focused webcam configuration
  static const LocalCameraConfig securityWebcam = LocalCameraConfig(
    id: 'WEBCAM-004',
    name: 'Security Webcam',
    location: 'Security Monitoring',
    description: 'Webcam configured for security surveillance',
    lensDirection: CameraLensDirection.back,
    resolution: ResolutionPreset.high,
  );

  // Get all predefined local cameras
  static List<LocalCameraConfig> getAllPresets() {
    return [
      defaultWebcam,
      externalWebcam,
      hdWebcam,
      securityWebcam,
    ];
  }

  // Create custom local camera configuration
  static LocalCameraConfig createCustomWebcam({
    required String id,
    required String name,
    required String location,
    String? description,
    CameraLensDirection lensDirection = CameraLensDirection.back,
    ResolutionPreset resolution = ResolutionPreset.high,
    int? deviceIndex,
  }) {
    return LocalCameraConfig(
      id: id,
      name: name,
      location: location,
      description: description,
      lensDirection: lensDirection,
      resolution: resolution,
      deviceIndex: deviceIndex,
    );
  }

  // Quick setup for common webcam scenarios
  static List<LocalCameraConfig> quickWebcamSetup({
    String baseName = 'Webcam',
    String baseLocation = 'Local Device',
    ResolutionPreset resolution = ResolutionPreset.high,
  }) {
    return [
      LocalCameraConfig(
        id: 'WEBCAM-001',
        name: '$baseName 1',
        location: '$baseLocation - Primary',
        description: 'Primary webcam for local monitoring',
        lensDirection: CameraLensDirection.front,
        resolution: resolution,
      ),
      LocalCameraConfig(
        id: 'WEBCAM-002',
        name: '$baseName 2',
        location: '$baseLocation - Secondary',
        description: 'Secondary webcam for additional monitoring',
        lensDirection: CameraLensDirection.back,
        resolution: resolution,
      ),
    ];
  }
}

// Camera service for local devices
class LocalCameraService {
  static List<CameraDescription>? _availableCameras;
  static bool _isInitialized = false;

  /// Initialize the camera service
  static Future<void> initialize() async {
    if (_isInitialized) return;
    
    try {
      _availableCameras = await availableCameras();
      _isInitialized = true;
      print('Local camera service initialized. Found ${_availableCameras?.length ?? 0} cameras.');
    } catch (e) {
      print('Failed to initialize local camera service: $e');
      _availableCameras = [];
      _isInitialized = true;
    }
  }

  /// Get available camera descriptions
  static List<CameraDescription> getAvailableCameras() {
    if (!_isInitialized) {
      throw StateError('Local camera service not initialized. Call initialize() first.');
    }
    return _availableCameras ?? [];
  }

  /// Find camera by lens direction
  static CameraDescription? findCameraByDirection(CameraLensDirection direction) {
    final cameras = getAvailableCameras();
    try {
      return cameras.firstWhere((camera) => camera.lensDirection == direction);
    } catch (e) {
      return null;
    }
  }

  /// Get camera by index
  static CameraDescription? getCameraByIndex(int index) {
    final cameras = getAvailableCameras();
    if (index >= 0 && index < cameras.length) {
      return cameras[index];
    }
    return null;
  }

  /// Get all camera descriptions as a list
  static List<CameraDescription> getAllCameras() {
    return getAvailableCameras();
  }

  /// Check if camera service is available
  static bool get isAvailable => _isInitialized && (_availableCameras?.isNotEmpty ?? false);

  /// Get camera count
  static int get cameraCount => _availableCameras?.length ?? 0;

  /// Dispose the service
  static void dispose() {
    _availableCameras = null;
    _isInitialized = false;
  }
}

// Example usage:
// 
// 1. Initialize the service:
// await LocalCameraService.initialize();
//
// 2. Get available cameras:
// final cameras = LocalCameraService.getAvailableCameras();
//
// 3. Create custom webcam config:
// final customWebcam = LocalCameraPresets.createCustomWebcam(
//   id: 'CUSTOM-001',
//   name: 'My Webcam',
//   location: 'My Location',
//   resolution: ResolutionPreset.ultraHigh,
// );
//
// 4. Use in your app:
// final webcamConfigs = LocalCameraPresets.quickWebcamSetup(
//   baseName: 'Security Cam',
//   resolution: ResolutionPreset.high,
// );
