// Camera configuration file for easy management of CCTV cameras
// Add or modify cameras here to scale the application

class CameraConfig {
  final String id;
  final String name;
  final String url;
  final String location;
  final String? description;
  final Map<String, dynamic>? additionalSettings;

  const CameraConfig({
    required this.id,
    required this.name,
    required this.url,
    required this.location,
    this.description,
    this.additionalSettings,
  });

  // Factory method to create camera from JSON (useful for API integration)
  factory CameraConfig.fromJson(Map<String, dynamic> json) {
    return CameraConfig(
      id: json['id'] as String,
      name: json['name'] as String,
      url: json['url'] as String,
      location: json['location'] as String,
      description: json['description'] as String?,
      additionalSettings: json['additionalSettings'] as Map<String, dynamic>?,
    );
  }

  // Convert to JSON (useful for API integration)
  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'url': url,
      'location': location,
      'description': description,
      'additionalSettings': additionalSettings,
    };
  }

  @override
  String toString() {
    return 'CameraConfig(id: $id, name: $name, location: $location)';
  }
}

// Predefined camera configurations
class CameraPresets {
  // Example camera configurations - modify these URLs to match your actual cameras
  static const List<CameraConfig> defaultCameras = [
    CameraConfig(
      id: 'CAM-001',
      name: 'Main Entrance',
      url: 'http://192.168.1.100:8080/video.mjpg',
      location: 'Building A - Front Door',
      description: 'Primary entrance monitoring with facial recognition',
    )
    // CameraConfig(
    //   id: 'CAM-002',
    //   name: 'Parking Lot',
    //   url: 'http://192.168.1.101:8080/video.mjpg',
    //   location: 'Building A - Parking Area',
    //   description: 'Vehicle monitoring and license plate recognition',
    // ),
    // CameraConfig(
    //   id: 'CAM-003',
    //   name: 'Back Entrance',
    //   url: 'http://192.168.1.102:8080/video.mjpg',
    //   location: 'Building A - Rear Door',
    //   description: 'Secondary entrance and delivery area monitoring',
    // ),
    // CameraConfig(
    //   id: 'CAM-004',
    //   name: 'Loading Dock',
    //   url: 'http://192.168.1.103:8080/video.mjpg',
    //   location: 'Building A - Loading Zone',
    //   description: 'Cargo and delivery monitoring',
    // ),
  ];

  // Common MJPEG camera URL patterns for different brands
  static const Map<String, String> urlPatterns = {
    'Axis': 'http://{ip}:{port}/axis-cgi/mjpg/video.cgi',
    'Hikvision': 'http://{ip}:{port}/ISAPI/Streaming/channels/101/httpPreview',
    'Dahua': 'http://{ip}:{port}/cgi-bin/magicBox.cgi?action=getSystemInfo',
    'Generic': 'http://{ip}:{port}/video.mjpg',
    'IP Camera': 'http://{ip}:{port}/mjpeg/1/media.amp',
  };

  // Helper method to generate camera URL
  static String generateUrl({
    required String ip,
    required String port,
    required String pattern,
    Map<String, String>? parameters,
  }) {
    String url = pattern.replaceAll('{ip}', ip).replaceAll('{port}', port);
    
    if (parameters != null) {
      final queryParams = parameters.entries
          .map((e) => '${e.key}=${e.value}')
          .join('&');
      url += '?$queryParams';
    }
    
    return url;
  }

  // Example of how to add a new camera programmatically
  static CameraConfig addCamera({
    required String id,
    required String name,
    required String ip,
    required String port,
    required String location,
    String pattern = 'Generic',
    String? description,
  }) {
    final url = generateUrl(ip: ip, port: port, pattern: urlPatterns[pattern]!);
    
    return CameraConfig(
      id: id,
      name: name,
      url: url,
      location: location,
      description: description,
    );
  }
}
