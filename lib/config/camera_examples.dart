// Example camera configurations for different camera brands and setups
// Copy and modify these examples for your own cameras

import 'camera_config.dart';

class CameraExamples {
  // Example 1: Generic IP Camera
  static const CameraConfig genericCamera = CameraConfig(
    id: 'CAM-001',
    name: 'Generic IP Camera',
    url: 'http://192.168.1.100:8080/video.mjpg',
    location: 'Main Entrance',
    description: 'Standard MJPEG stream from generic IP camera',
  );

  // Example 2: Axis Camera
  static const CameraConfig axisCamera = CameraConfig(
    id: 'CAM-002',
    name: 'Axis Camera',
    url: 'http://192.168.1.101:80/axis-cgi/mjpg/video.cgi',
    location: 'Parking Lot',
    description: 'Axis camera with MJPEG streaming',
  );

  // Example 3: Hikvision Camera
  static const CameraConfig hikvisionCamera = CameraConfig(
    id: 'CAM-003',
    name: 'Hikvision Camera',
    url: 'http://192.168.1.102:80/ISAPI/Streaming/channels/101/httpPreview',
    location: 'Back Entrance',
    description: 'Hikvision camera with ISAPI streaming',
  );

  // Example 4: Dahua Camera
  static const CameraConfig dahuaCamera = CameraConfig(
    id: 'CAM-004',
    name: 'Dahua Camera',
    url: 'http://192.168.1.103:80/cgi-bin/mjpg/video.cgi',
    location: 'Loading Dock',
    description: 'Dahua camera with CGI streaming',
  );

  // Example 5: Local Network Camera
  static const CameraConfig localCamera = CameraConfig(
    id: 'CAM-005',
    name: 'Local Network Camera',
    url: 'http://10.0.0.50:554/mjpeg/1/media.amp',
    location: 'Security Office',
    description: 'Local network camera with MJPEG support',
  );

  // Example 6: Remote Camera (VPN/Internet)
  static const CameraConfig remoteCamera = CameraConfig(
    id: 'CAM-006',
    name: 'Remote Camera',
    url: 'http://203.0.113.10:8080/video.mjpg',
    location: 'Remote Location',
    description: 'Remote camera accessible via internet/VPN',
  );

  // Example 7: High-Resolution Camera
  static const CameraConfig hdCamera = CameraConfig(
    id: 'CAM-007',
    name: 'HD Security Camera',
    url: 'http://192.168.1.104:8080/hd_video.mjpg',
    location: 'Main Corridor',
    description: 'High-definition security camera',
  );

  // Example 8: PTZ Camera
  static const CameraConfig ptzCamera = CameraConfig(
    id: 'CAM-008',
    name: 'PTZ Camera',
    url: 'http://192.168.1.105:8080/ptz_video.mjpg',
    location: 'Outdoor Area',
    description: 'Pan-Tilt-Zoom camera with MJPEG streaming',
  );

  // Helper method to get all example cameras
  static List<CameraConfig> getAllExamples() {
    return [
      genericCamera,
      axisCamera,
      hikvisionCamera,
      dahuaCamera,
      localCamera,
      remoteCamera,
      hdCamera,
      ptzCamera,
    ];
  }

  // Helper method to get cameras by brand
  static List<CameraConfig> getByBrand(String brand) {
    switch (brand.toLowerCase()) {
      case 'axis':
        return [axisCamera];
      case 'hikvision':
        return [hikvisionCamera];
      case 'dahua':
        return [dahuaCamera];
      case 'generic':
        return [genericCamera, localCamera, remoteCamera, hdCamera, ptzCamera];
      default:
        return getAllExamples();
    }
  }

  // Helper method to create a custom camera
  static CameraConfig createCustomCamera({
    required String id,
    required String name,
    required String ip,
    required String port,
    required String location,
    String? description,
    String urlPattern = '/video.mjpg',
  }) {
    final url = 'http://$ip:$port$urlPattern';
    
    return CameraConfig(
      id: id,
      name: name,
      url: url,
      location: location,
      description: description,
    );
  }

  // Common URL patterns for different camera types
  static const Map<String, String> urlPatterns = {
    'Generic': '/video.mjpg',
    'Axis': '/axis-cgi/mjpg/video.cgi',
    'Hikvision': '/ISAPI/Streaming/channels/101/httpPreview',
    'Dahua': '/cgi-bin/mjpg/video.cgi',
    'IP Camera': '/mjpeg/1/media.amp',
    'Custom': '', // Empty for custom URLs
  };

  // Example of how to use the helper methods
  static void exampleUsage() {
    // Create a custom camera
    final customCamera = createCustomCamera(
      id: 'CAM-CUSTOM',
      name: 'My Custom Camera',
      ip: '192.168.1.200',
      port: '8080',
      location: 'Custom Location',
      description: 'This is my custom camera setup',
      urlPattern: '/custom/stream.mjpg',
    );

    // Get all example cameras
    final allExamples = getAllExamples();

    // Get cameras by brand
    final axisCameras = getByBrand('Axis');
    final genericCameras = getByBrand('Generic');

    print('Total example cameras: ${allExamples.length}');
    print('Axis cameras: ${axisCameras.length}');
    print('Generic cameras: ${genericCameras.length}');
    print('Custom camera: ${customCamera.name}');
  }
}
