# Camera Setup Guide for Flutter Web App

This guide explains how to set up and configure the camera system in your Flutter web application.

## Overview

The Flutter web app can handle two types of camera sources:
1. **Local Webcams** - Using integer indices (0, 1, 2, etc.)
2. **CCTV/IP Camera Streams** - Using RTSP/HTTP URLs

## Configuration File

The app reads camera configuration from `assets/cameras.json`. This file contains an array of camera objects with the following structure:

```json
{
  "name": "Camera Name",
  "source": 0,  // Integer for local webcam, URL string for CCTV
  "width": 640,
  "height": 480,
  "id": "CAM-001",
  "status": "Active"
}
```

### Source Types

- **Integer (e.g., 0)**: Opens the local webcam at that index
  - 0 = First available camera
  - 1 = Second available camera
  - etc.

- **String URL**: Connects to a CCTV/IP camera stream
  - RTSP: `rtsp://username:password@ip:port/stream`
  - HTTP: `http://ip:port/video`
  - MJPEG: `http://ip:port/mjpeg`

## Example Configuration

```json
[
  {
    "name": "Local Webcam",
    "source": 0,
    "width": 640,
    "height": 480,
    "id": "CAM-001",
    "status": "Active"
  },
  {
    "name": "CCTV Stream 1",
    "source": "rtsp://admin:admin@192.168.1.100:554/stream1",
    "width": 640,
    "height": 480,
    "id": "CAM-002",
    "status": "Active"
  },
  {
    "name": "CCTV Stream 2",
    "source": "http://192.168.1.101:8080/video",
    "width": 640,
    "height": 480,
    "id": "CAM-003",
    "status": "Active"
  }
]
```

## Features

### Live Indicators
- **Red "LIVE" badge** in the top-right corner of each active camera
- **Status indicator** in the top-left showing camera status (Active/Inactive)
- **Camera name** displayed at the bottom-left

### Camera Management
- **Refresh button**: Reloads camera configuration
- **Configure button**: Shows configuration help dialog
- **Automatic fallback**: Uses default configuration if JSON file is missing

### Error Handling
- Graceful fallback to default configuration
- Error messages displayed when camera initialization fails
- Automatic retry for connection issues

## Setup Instructions

### 1. Install Dependencies

The following packages are required and should be in your `pubspec.yaml`:

```yaml
dependencies:
  camera: ^0.10.5+9
  flutter_vlc_player: ^7.1.8
  path_provider: ^2.1.2
  permission_handler: ^11.3.0
  http: ^1.1.0
```

### 2. Configure Cameras

1. Edit `assets/cameras.json` with your camera configuration
2. For local webcams, use integer indices (0, 1, 2, etc.)
3. For CCTV streams, use the full URL with credentials if required

### 3. Build and Run

```bash
flutter pub get
flutter run -d chrome
```

## Switching Camera Sources

To change camera sources without modifying code:

1. **Edit the JSON file**: Change the "source" value in `assets/cameras.json`
2. **Refresh the app**: Click the "Refresh" button or reload the page
3. **Automatic detection**: The app will automatically detect the source type and use the appropriate player

### Example: Switch from Local Webcam to CCTV

**Before:**
```json
{
  "name": "Local Webcam",
  "source": 0,
  "id": "CAM-001"
}
```

**After:**
```json
{
  "name": "CCTV Stream",
  "source": "rtsp://admin:admin@192.168.1.100:554/stream1",
  "id": "CAM-001"
}
```

## Troubleshooting

### Local Webcam Issues
- Ensure camera permissions are granted
- Check if the camera index exists (0, 1, 2, etc.)
- Verify camera is not being used by another application

### CCTV Stream Issues
- Verify network connectivity to the camera
- Check URL format and credentials
- Ensure the camera supports the specified protocol (RTSP/HTTP)
- Test the stream URL in VLC media player first

### General Issues
- Check browser console for error messages
- Verify `cameras.json` is properly formatted JSON
- Ensure all required dependencies are installed

## Security Considerations

- **Credentials in URLs**: Store sensitive credentials securely
- **Network Access**: Ensure proper firewall rules for CCTV streams
- **HTTPS**: Use HTTPS for HTTP camera streams in production

## Performance Tips

- **Resolution**: Use appropriate width/height for your use case
- **Frame Rate**: Adjust `display_interval_ms` for performance vs. smoothness
- **Connection Limits**: Limit the number of simultaneous CCTV connections

## Future Enhancements

The system is designed to be easily extensible for:
- Face detection integration
- Recording capabilities
- Motion detection
- Multiple layout options
- Camera grouping and organization
