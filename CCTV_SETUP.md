# CCTV Real-Time Monitoring System Setup Guide

## Overview
This Flutter desktop application provides real-time monitoring of multiple CCTV cameras using MJPEG streaming protocol. The system is designed for security monitoring, surveillance, and remote camera management.

## Features
- **Multi-Camera Support**: Monitor multiple cameras simultaneously
- **Real-Time Streaming**: MJPEG protocol for low-latency video feeds
- **Fullscreen Mode**: Click any camera card to expand to fullscreen view
- **Start/Stop Controls**: Individual control for each camera stream
- **Responsive Design**: Optimized for desktop platforms (Windows, macOS, Linux)
- **Scalable Architecture**: Easy to add/remove cameras

## Prerequisites
- Flutter SDK 3.8.1 or higher
- Desktop platform support enabled
- Network access to MJPEG camera feeds

## Installation

### 1. Install Dependencies
```bash
flutter pub get
```

### 2. Enable Desktop Support
```bash
flutter config --enable-windows-desktop
flutter config --enable-macos-desktop
flutter config --enable-linux-desktop
```

### 3. Run the Application
```bash
# For Windows
flutter run -d windows

# For macOS
flutter run -d macos

# For Linux
flutter run -d linux
```

## Camera Configuration

### Adding New Cameras
Edit `lib/config/camera_config.dart` to add new cameras:

```dart
static const List<CameraConfig> defaultCameras = [
  // Existing cameras...
  CameraConfig(
    id: 'CAM-005',
    name: 'Security Office',
    url: 'http://192.168.1.104:8080/video.mjpg',
    location: 'Building A - Security Room',
    description: 'Security personnel monitoring',
  ),
];
```

### Supported Camera Brands
The system includes URL patterns for common camera brands:

- **Axis**: `http://{ip}:{port}/axis-cgi/mjpg/video.cgi`
- **Hikvision**: `http://{ip}:{port}/ISAPI/Streaming/channels/101/httpPreview`
- **Dahua**: `http://{ip}:{port}/cgi-bin/magicBox.cgi?action=getSystemInfo`
- **Generic**: `http://{ip}:{port}/video.mjpg`
- **IP Camera**: `http://{ip}:{port}/mjpeg/1/media.amp`

### Programmatically Adding Cameras
```dart
final newCamera = CameraPresets.addCamera(
  id: 'CAM-006',
  name: 'Warehouse',
  ip: '192.168.1.105',
  port: '8080',
  location: 'Building B - Storage Area',
  pattern: 'Generic',
  description: 'Inventory monitoring',
);
```

## Camera URL Formats

### Standard MJPEG URLs
```
http://[camera-ip]:[port]/video.mjpg
http://[camera-ip]:[port]/mjpeg/1/media.amp
http://[camera-ip]:[port]/axis-cgi/mjpg/video.cgi
```

### Example URLs
```
http://192.168.1.100:8080/video.mjpg
http://10.0.0.50:554/mjpeg/1/media.amp
http://172.16.0.25:80/axis-cgi/mjpg/video.cgi
```

## Usage

### Main Interface
1. **Camera Grid**: View all cameras in a 2x2 grid layout
2. **Stream Controls**: Use START/STOP buttons to control individual streams
3. **Status Indicators**: Live status shows streaming state
4. **Fullscreen**: Click any camera card to expand

### Controls
- **START Button**: Initiates MJPEG stream connection
- **STOP Button**: Disconnects and stops the stream
- **Fullscreen Icon**: Expands camera view to fullscreen
- **Status Badge**: Shows LIVE/STOPPED status

### Fullscreen Mode
- **App Bar**: Camera name and streaming controls
- **Stream Toggle**: Start/stop stream from fullscreen view
- **Status Display**: Current streaming status
- **Return**: Use back button to return to grid view

## Performance Optimization

### Multiple Streams
- The system is optimized to handle multiple simultaneous MJPEG streams
- Each camera has its own stream controller for independent operation
- Memory management automatically cleans up stopped streams

### Network Considerations
- Ensure sufficient bandwidth for multiple camera feeds
- Consider camera resolution and frame rate impact on performance
- Use local network connections when possible for lowest latency

## Troubleshooting

### Common Issues

#### Stream Won't Start
1. Check camera IP address and port
2. Verify network connectivity to camera
3. Ensure camera supports MJPEG streaming
4. Check firewall settings

#### Poor Performance
1. Reduce camera resolution if possible
2. Check network bandwidth
3. Close unnecessary applications
4. Ensure adequate system resources

#### Camera Not Displaying
1. Verify MJPEG URL format
2. Test URL in web browser
3. Check camera authentication requirements
4. Verify camera is online and accessible

### Debug Information
Enable debug logging by checking the console output for:
- Connection errors
- Stream initialization status
- Performance metrics

## Security Considerations

### Network Security
- Use VPN for remote camera access
- Implement proper firewall rules
- Consider camera authentication
- Use HTTPS when available

### Access Control
- Implement user authentication
- Restrict camera access by role
- Log access and streaming activities
- Regular security audits

## Future Enhancements

### Planned Features
- **Recording**: Save video streams to local storage
- **Motion Detection**: Alert on detected movement
- **Multi-View**: Customizable grid layouts
- **Camera Groups**: Organize cameras by location/function
- **API Integration**: REST API for external control
- **Mobile Support**: iOS and Android applications

### Scalability
- **Database Integration**: Store camera configurations
- **User Management**: Multi-user access control
- **Remote Management**: Web-based administration
- **Cloud Storage**: Off-site video storage

## Support

### Documentation
- Check inline code comments for implementation details
- Review Flutter documentation for platform-specific issues
- Consult MJPEG camera manufacturer documentation

### Development
- The codebase follows Flutter best practices
- Uses setState for simple state management
- Modular architecture for easy maintenance
- Comprehensive error handling and logging

## License
This project is part of the bismillahsukses application suite.
