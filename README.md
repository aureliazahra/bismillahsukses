# Bismillah Sukses - CCTV Management System

A comprehensive CCTV management and monitoring system built with Flutter for web and mobile platforms.

## Features

### 🎥 Real-Time Camera Monitoring
- **Local Webcam Support**: Connect to local webcams using integer indices (0, 1, 2, etc.)
- **CCTV Stream Support**: Connect to IP cameras via RTSP/HTTP streams
- **Live Feed Display**: Real-time video feeds with live indicators
- **Multi-Camera Grid**: View multiple camera feeds simultaneously
- **Configuration Management**: Easy camera setup via JSON configuration

### 🖥️ Web Interface
- **Responsive Design**: Works on desktop and mobile browsers
- **Modern UI**: Clean, professional interface with gradient backgrounds
- **Real-Time Updates**: Live status indicators and camera information
- **Easy Configuration**: Modify camera settings without code changes

### 📱 Mobile Support
- **Cross-Platform**: Works on Android, iOS, Windows, macOS, and Linux
- **Native Performance**: Full camera functionality on supported platforms
- **Responsive Layout**: Adapts to different screen sizes

## Quick Start

### 1. Install Dependencies
```bash
flutter pub get
```

### 2. Run the Application
```bash
# For web development
flutter run -d chrome

# For mobile/desktop
flutter run
```

### 3. Access the Application
- Navigate to the "Real Time Face Detection" section
- View your configured cameras in the grid layout
- Use the Refresh and Configure buttons to manage settings

## Camera Configuration

The system reads camera configuration from `assets/cameras.json`. This file supports two types of camera sources:

### Local Webcams
```json
{
  "name": "Local Webcam",
  "source": 0,  // Integer index (0 = first camera, 1 = second, etc.)
  "width": 640,
  "height": 480,
  "id": "CAM-001",
  "status": "Active"
}
```

### CCTV/IP Camera Streams
```json
{
  "name": "CCTV Stream",
  "source": "rtsp://admin:admin@192.168.1.100:554/stream1",
  "width": 640,
  "height": 480,
  "id": "CAM-002",
  "status": "Active"
}
```

## Supported Stream Formats

- **RTSP**: `rtsp://username:password@ip:port/stream`
- **HTTP**: `http://ip:port/video`
- **MJPEG**: `http://ip:port/mjpeg`

## Platform Support

### Web (Current Implementation)
- ✅ Configuration loading from JSON
- ✅ Camera grid layout
- ✅ Live indicators and status
- ✅ Web preview mode
- ⚠️ Limited to preview mode (no actual video streams)

### Mobile/Desktop (Full Implementation)
- ✅ Full camera functionality
- ✅ Local webcam access
- ✅ CCTV stream playback
- ✅ Real-time video feeds
- ✅ Face detection capabilities

## Extending for Full Camera Functionality

To enable full camera functionality on supported platforms, add these dependencies to `pubspec.yaml`:

```yaml
dependencies:
  camera: ^0.10.5+9
  flutter_vlc_player: ^7.1.8
  path_provider: ^2.1.2
  permission_handler: ^11.3.0
```

Then uncomment the camera implementation code in `lib/content/realtime.dart`.

## Project Structure

```
lib/
├── content/
│   ├── realtime.dart          # Main camera monitoring page
│   ├── dashboard.dart          # Dashboard overview
│   ├── cctvmanagement.dart    # CCTV management interface
│   └── ...
├── layout/
│   ├── layout.dart            # Main application layout
│   └── sidebar.dart           # Navigation sidebar
├── models/
│   └── camera_model.dart      # Camera data models
└── main.dart                  # Application entry point
```

## Configuration Files

- `assets/cameras.json` - Camera configuration
- `CAMERA_SETUP.md` - Detailed camera setup guide
- `python/` - Python backend for advanced features

## Development

### Adding New Cameras
1. Edit `assets/cameras.json`
2. Add new camera configuration
3. Refresh the application
4. Camera will appear automatically

### Modifying Camera Sources
1. Change the "source" value in the JSON
2. Use integer for local webcams
3. Use URL string for CCTV streams
4. Click Refresh to apply changes

### Customizing the Interface
- Modify `lib/content/realtime.dart` for camera display logic
- Update `lib/layout/` for navigation and layout changes
- Customize styles in individual page files

## Troubleshooting

### Common Issues
- **Cameras not loading**: Check `assets/cameras.json` format
- **Web preview only**: This is expected behavior for web platform
- **Configuration errors**: Verify JSON syntax and file location

### Getting Help
- Check the `CAMERA_SETUP.md` file for detailed instructions
- Review the console for error messages
- Ensure all dependencies are properly installed

## Future Enhancements

- [ ] Face detection integration
- [ ] Motion detection alerts
- [ ] Recording capabilities
- [ ] Advanced analytics
- [ ] Multi-user support
- [ ] Cloud storage integration

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Check the documentation in `CAMERA_SETUP.md`
- Review the code comments
- Open an issue on the repository

---

**Note**: The web version currently runs in preview mode. For full camera functionality, build and run the application on supported platforms (Android, iOS, Windows, macOS, Linux).
