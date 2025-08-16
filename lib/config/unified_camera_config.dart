// Unified Camera Configuration
// This file allows you to configure both local device cameras (webcam) and IP cameras (MJPEG/RTSP)
// You can mix both types in your monitoring system

import 'package:camera/camera.dart'; // ✅ untuk CameraLensDirection & ResolutionPreset
import 'camera_config.dart';
import 'local_camera_config.dart';

// Enum to distinguish between camera types
enum CameraType {
  local,    // Webcam/Laptop camera
  ip,       // IP camera (MJPEG/RTSP)
}

// Base camera configuration that can be either local or IP
abstract class UnifiedCameraConfig {
  final String id;
  final String name;
  final String location;
  final String? description;
  final CameraType type;

  const UnifiedCameraConfig({
    required this.id,
    required this.name,
    required this.location,
    this.description,
    required this.type,
  });

  // Factory method to create from JSON
  factory UnifiedCameraConfig.fromJson(Map<String, dynamic> json) {
    final type = CameraType.values.firstWhere(
      (e) => e.name == json['type'],
      orElse: () => CameraType.ip,
    );

    if (type == CameraType.local) {
      final local = LocalCameraConfig.fromJson(json);
      return _UnifiedLocalCameraConfig(
        id: local.id,
        name: local.name,
        location: local.location,
        description: local.description,
        lensDirection: local.lensDirection,
        resolution: local.resolution,
        deviceIndex: local.deviceIndex,
      );
    } else {
      final ip = CameraConfig.fromJson(json);
      return _UnifiedIPCameraConfig(
        id: ip.id,
        name: ip.name,
        location: ip.location,
        description: ip.description,
        url: ip.url,
        additionalSettings: ip.additionalSettings,
      );
    }
  }

  // Convert to JSON
  Map<String, dynamic> toJson();

  @override
  String toString() {
    return 'UnifiedCameraConfig(id: $id, name: $name, type: ${type.name})';
  }
}

// Extension to make existing configs compatible
extension UnifiedCameraConfigExtension on CameraConfig {
  UnifiedCameraConfig toUnified() {
    return _UnifiedIPCameraConfig(
      id: id,
      name: name,
      url: url,
      location: location,
      description: description,
      additionalSettings: additionalSettings,
    );
  }
}

extension LocalCameraConfigExtension on LocalCameraConfig {
  UnifiedCameraConfig toUnified() {
    return _UnifiedLocalCameraConfig(
      id: id,
      name: name,
      location: location,
      description: description,
      lensDirection: lensDirection,
      resolution: resolution,
      deviceIndex: deviceIndex,
    );
  }
}

// Internal implementation for IP cameras
class _UnifiedIPCameraConfig extends UnifiedCameraConfig {
  final String url;
  final Map<String, dynamic>? additionalSettings;

  const _UnifiedIPCameraConfig({
    required super.id,
    required super.name,
    required super.location,
    super.description,
    required this.url,
    this.additionalSettings,
  }) : super(type: CameraType.ip);

  @override
  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'url': url,
      'location': location,
      'description': description,
      'type': type.name,
      'additionalSettings': additionalSettings,
    };
  }
}

// Internal implementation for local cameras
class _UnifiedLocalCameraConfig extends UnifiedCameraConfig {
  final CameraLensDirection lensDirection;
  final ResolutionPreset resolution;
  final int? deviceIndex;

  const _UnifiedLocalCameraConfig({
    required super.id,
    required super.name,
    required super.location,
    super.description,
    required this.lensDirection,
    required this.resolution,
    this.deviceIndex,
  }) : super(type: CameraType.local);

  @override
  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'location': location,
      'description': description,
      'type': type.name,
      'lensDirection': lensDirection.name,
      'resolution': resolution.name,
      'deviceIndex': deviceIndex,
    };
  }
}

// Unified camera presets that combine both types
class UnifiedCameraPresets {
  // Mixed camera setup with both local and IP cameras
  static List<UnifiedCameraConfig> getMixedSetup() {
    return [
      // Local cameras
      LocalCameraPresets.defaultWebcam.toUnified(),
      LocalCameraPresets.externalWebcam.toUnified(),

      // IP cameras
      CameraPresets.defaultCameras[0].toUnified(),
      CameraPresets.defaultCameras[1].toUnified(),
    ];
  }

  // Local-only setup
  static List<UnifiedCameraConfig> getLocalOnlySetup() {
    return LocalCameraPresets.getAllPresets()
        .map((camera) => camera.toUnified())
        .toList();
  }

  // IP-only setup
  static List<UnifiedCameraConfig> getIPOnlySetup() {
    return CameraPresets.defaultCameras
        .map((camera) => camera.toUnified())
        .toList();
  }

  // Custom mixed setup
  static List<UnifiedCameraConfig> createCustomMixedSetup({
    List<LocalCameraConfig> localCameras = const [],
    List<CameraConfig> ipCameras = const [],
  }) {
    final cameras = <UnifiedCameraConfig>[];

    // Add local cameras
    cameras.addAll(localCameras.map((camera) => camera.toUnified()));

    // Add IP cameras
    cameras.addAll(ipCameras.map((camera) => camera.toUnified()));

    return cameras;
  }

  // Quick setup for common scenarios
  static List<UnifiedCameraConfig> quickSetup({
    bool includeLocal = true,
    bool includeIP = true,
    int localCount = 2,
    int ipCount = 2,
  }) {
    final cameras = <UnifiedCameraConfig>[];

    if (includeLocal) {
      final localCameras = LocalCameraPresets.quickWebcamSetup();
      cameras.addAll(localCameras.take(localCount).map((c) => c.toUnified()));
    }

    if (includeIP) {
      final ipCameras = CameraPresets.defaultCameras;
      cameras.addAll(ipCameras.take(ipCount).map((c) => c.toUnified()));
    }

    return cameras;
  }
}

// Helper class to manage unified camera configurations
class UnifiedCameraManager {
  static List<UnifiedCameraConfig> _cameras = [];
  static bool _isInitialized = false;

  /// Initialize the camera manager
  static Future<void> initialize({
    List<UnifiedCameraConfig>? initialCameras,
  }) async {
    if (_isInitialized) return;

    // Initialize local camera service
    try {
      await LocalCameraService.initialize();
    } catch (e) {
      print('Warning: Local camera service initialization failed: $e');
    }

    // Set initial cameras
    if (initialCameras != null) {
      _cameras = List.from(initialCameras);
    } else {
      _cameras = UnifiedCameraPresets.getMixedSetup();
    }

    _isInitialized = true;
    print('Unified camera manager initialized with ${_cameras.length} cameras');
  }

  /// Get all configured cameras
  static List<UnifiedCameraConfig> getAllCameras() {
    if (!_isInitialized) {
      throw StateError('Camera manager not initialized. Call initialize() first.');
    }
    return List.unmodifiable(_cameras);
  }

  /// Get cameras by type
  static List<UnifiedCameraConfig> getCamerasByType(CameraType type) {
    return getAllCameras().where((camera) => camera.type == type).toList();
  }

  /// Get local cameras only
  static List<UnifiedCameraConfig> getLocalCameras() {
    return getCamerasByType(CameraType.local);
  }

  /// Get IP cameras only
  static List<UnifiedCameraConfig> getIPCameras() {
    return getCamerasByType(CameraType.ip);
  }

  /// Add a new camera
  static void addCamera(UnifiedCameraConfig camera) {
    if (!_isInitialized) {
      throw StateError('Camera manager not initialized. Call initialize() first.');
    }
    _cameras.add(camera);
  }

  /// Remove a camera by ID
  static bool removeCamera(String id) {
    if (!_isInitialized) {
      throw StateError('Camera manager not initialized. Call initialize() first.');
    }
    final initialLength = _cameras.length;
    _cameras.removeWhere((camera) => camera.id == id);
    return _cameras.length < initialLength;
  }

  /// Find camera by ID
  static UnifiedCameraConfig? findCameraById(String id) {
    try {
      return getAllCameras().firstWhere((camera) => camera.id == id);
    } catch (e) {
      return null;
    }
  }

  /// Get camera count
  static int get cameraCount => _cameras.length;

  /// Get local camera count
  static int get localCameraCount => getLocalCameras().length;

  /// Get IP camera count
  static int get ipCameraCount => getIPCameras().length;

  /// Check if manager is initialized
  static bool get isInitialized => _isInitialized;

  /// Dispose the manager
  static void dispose() {
    _cameras.clear();
    _isInitialized = false;
    LocalCameraService.dispose();
  }
}
