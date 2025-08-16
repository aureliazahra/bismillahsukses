// Demo camera configurations for testing the CCTV monitoring system
// Replace these URLs with your actual camera URLs

import 'camera_config.dart';

class DemoCameras {
  // Test cameras with publicly available MJPEG streams
  // These are examples - replace with your actual camera URLs
  
  static const List<CameraConfig> demoCameras = [
    CameraConfig(
      id: 'DEMO-001',
      name: 'Demo Camera 1',
      url: 'http://192.168.1.100:8080/video.mjpg',
      location: 'Test Location 1',
      description: 'Demo camera for testing - replace with your camera URL',
    ),
    CameraConfig(
      id: 'DEMO-002',
      name: 'Demo Camera 2',
      url: 'http://192.168.1.101:8080/video.mjpg',
      location: 'Test Location 2',
      description: 'Demo camera for testing - replace with your camera URL',
    ),
    CameraConfig(
      id: 'DEMO-003',
      name: 'Demo Camera 3',
      url: 'http://192.168.1.102:8080/video.mjpg',
      location: 'Test Location 3',
      description: 'Demo camera for testing - replace with your camera URL',
    ),
    CameraConfig(
      id: 'DEMO-004',
      name: 'Demo Camera 4',
      url: 'http://192.168.1.103:8080/video.mjpg',
      location: 'Test Location 4',
      description: 'Demo camera for testing - replace with your camera URL',
    ),
  ];

  // Quick setup method - just change these IP addresses and ports
  static List<CameraConfig> quickSetup({
    required String baseIp,
    String basePort = '8080',
    String urlPattern = '/video.mjpg',
  }) {
    return [
      CameraConfig(
        id: 'CAM-001',
        name: 'Main Entrance',
        url: 'http://$baseIp:$basePort$urlPattern',
        location: 'Building A - Front Door',
        description: 'Primary entrance monitoring',
      ),
      CameraConfig(
        id: 'CAM-002',
        name: 'Parking Lot',
        url: 'http://${baseIp.replaceAll(RegExp(r'\d+$'), '101')}:$basePort$urlPattern',
        location: 'Building A - Parking Area',
        description: 'Vehicle monitoring',
      ),
      CameraConfig(
        id: 'CAM-003',
        name: 'Back Entrance',
        url: 'http://${baseIp.replaceAll(RegExp(r'\d+$'), '102')}:$basePort$urlPattern',
        location: 'Building A - Rear Door',
        description: 'Secondary entrance',
      ),
      CameraConfig(
        id: 'CAM-004',
        name: 'Loading Dock',
        url: 'http://${baseIp.replaceAll(RegExp(r'\d+$'), '103')}:$basePort$urlPattern',
        location: 'Building A - Loading Zone',
        description: 'Cargo monitoring',
      ),
    ];
  }

  // Example usage:
  // Replace the cameras list in camera_config.dart with:
  // static const List<CameraConfig> defaultCameras = DemoCameras.quickSetup(
  //   baseIp: '192.168.1.100',
  //   basePort: '8080',
  //   urlPattern: '/video.mjpg',
  // );
}
