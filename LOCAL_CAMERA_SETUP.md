# Local Camera Setup Guide for Webcam/Laptop Camera

## 🔹 **Overview**

This guide explains how to set up and use **local device cameras** (webcam/laptop camera) alongside **IP cameras** (MJPEG/RTSP) in your CCTV monitoring system.

## 🔹 **Key Differences**

| Feature | Local Camera (Webcam) | IP Camera (MJPEG/RTSP) |
|---------|----------------------|------------------------|
| **Connection** | Direct USB/Built-in | Network (HTTP/RTSP) |
| **Package** | `camera` package | Custom MJPEG service |
| **URL** | Not applicable | `http://ip:port/video.mjpg` |
| **Setup** | Device detection | Network configuration |
| **Use Case** | Local monitoring | Remote surveillance |

## 🔹 **Prerequisites**

### **Required Packages**
```yaml
dependencies:
  camera: ^0.10.5+9  # For local device cameras
  http: ^1.1.0       # For IP cameras (already included)
```

### **Platform Support**
- ✅ **Windows**: Full support
- ✅ **macOS**: Full support  
- ✅ **Linux**: Full support
- ⚠️ **Android**: Limited (requires permissions)
- ⚠️ **iOS**: Limited (requires permissions)

## 🔹 **Quick Start**

### **1. Install Dependencies**
```bash
flutter pub get
```

### **2. Initialize Camera Service**
```dart
import 'package:your_app/config/unified_camera_config.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  // Initialize unified camera manager
  await UnifiedCameraManager.initialize(
    initialCameras: UnifiedCameraPresets.getMixedSetup(),
  );
  
  runApp(MyApp());
}
```

### **3. Use in Your App**
```dart
// Get all cameras (both local and IP)
final allCameras = UnifiedCameraManager.getAllCameras();

// Get only local cameras
final localCameras = UnifiedCameraManager.getLocalCameras();

// Get only IP cameras
final ipCameras = UnifiedCameraManager.getIPCameras();
```

## 🔹 **Configuration Options**

### **Option 1: Mixed Setup (Recommended)**
```dart
// Both local webcam and IP cameras
final cameras = UnifiedCameraPresets.getMixedSetup();
```

### **Option 2: Local Only**
```dart
// Only webcam/laptop cameras
final cameras = UnifiedCameraPresets.getLocalOnlySetup();
```

### **Option 3: IP Only**
```dart
// Only IP cameras (MJPEG/RTSP)
final cameras = UnifiedCameraPresets.getIPOnlySetup();
```

### **Option 4: Custom Setup**
```dart
final cameras = UnifiedCameraPresets.createCustomMixedSetup(
  localCameras: [
    LocalCameraPresets.createCustomWebcam(
      id: 'WEBCAM-001',
      name: 'My Laptop Camera',
      location: 'Home Office',
      resolution: ResolutionPreset.ultraHigh,
    ),
  ],
  ipCameras: [
    CameraPresets.defaultCameras[0], // Your IP camera
  ],
);
```

## 🔹 **Local Camera Configuration**

### **Basic Webcam Setup**
```dart
final webcam = LocalCameraPresets.defaultWebcam;
```

### **Custom Webcam Configuration**
```dart
final customWebcam = LocalCameraPresets.createCustomWebcam(
  id: 'CUSTOM-001',
  name: 'Security Webcam',
  location: 'Front Door',
  lensDirection: CameraLensDirection.front,
  resolution: ResolutionPreset.high,
  deviceIndex: 0, // Specific camera device
);
```

### **Resolution Options**
```dart
ResolutionPreset.low      // 240p
ResolutionPreset.medium   // 480p
ResolutionPreset.high     // 720p
ResolutionPreset.veryHigh // 1080p
ResolutionPreset.ultraHigh // 1440p
ResolutionPreset.max      // Maximum available
```

### **Lens Direction Options**
```dart
CameraLensDirection.front   // Front-facing camera
CameraLensDirection.back    // Back-facing camera
CameraLensDirection.external // External USB camera
```

## 🔹 **Usage Examples**

### **Starting Local Camera Stream**
```dart
import 'package:your_app/config/local_camera_config.dart';

// Get webcam configuration
final webcam = LocalCameraPresets.defaultWebcam;

// Start streaming
final success = await webcam.startStream();
if (success) {
  print('Webcam stream started successfully');
} else {
  print('Failed to start webcam stream');
}
```

### **Checking Stream Status**
```dart
if (webcam.isStreaming) {
  print('Webcam is currently streaming');
  
  // Get last frame
  final frame = webcam.lastFrame;
  if (frame != null) {
    // Use frame data for display
    Image.memory(frame);
  }
} else {
  print('Webcam is not streaming');
}
```

### **Taking Photos**
```dart
// Take a photo from the webcam
final photo = await webcam.takePhoto();
if (photo != null) {
  // Save photo or process it
  print('Photo captured: ${photo.length} bytes');
}
```

### **Stopping Stream**
```dart
// Stop the webcam stream
await webcam.stopStream();
```

## 🔹 **Advanced Configuration**

### **Multiple Local Cameras**
```dart
// Setup multiple webcams
final webcams = LocalCameraPresets.quickWebcamSetup(
  baseName: 'Security Cam',
  baseLocation: 'Building A',
  resolution: ResolutionPreset.high,
);

// Initialize all webcams
for (final webcam in webcams) {
  await webcam.startStream();
}
```

### **Camera Selection by Device Index**
```dart
final specificWebcam = LocalCameraPresets.createCustomWebcam(
  id: 'WEBCAM-001',
  name: 'USB Camera 1',
  location: 'USB Port 1',
  deviceIndex: 0, // First available camera
  resolution: ResolutionPreset.high,
);
```

### **Error Handling**
```dart
try {
  final success = await webcam.startStream();
  if (!success) {
    print('Failed to start webcam stream');
    // Handle error (show user message, retry, etc.)
  }
} catch (e) {
  print('Error starting webcam: $e');
  // Handle exception
}
```

## 🔹 **Integration with Existing System**

### **Unified Camera Management**
```dart
// Initialize with mixed setup
await UnifiedCameraManager.initialize(
  initialCameras: UnifiedCameraPresets.getMixedSetup(),
);

// Get all cameras (local + IP)
final allCameras = UnifiedCameraManager.getAllCameras();

// Process each camera based on type
for (final camera in allCameras) {
  switch (camera.type) {
    case CameraType.local:
      // Handle local camera
      print('Local camera: ${camera.name}');
      break;
    case CameraType.ip:
      // Handle IP camera
      print('IP camera: ${camera.name}');
      break;
  }
}
```

### **Dynamic Camera Management**
```dart
// Add new local camera
final newWebcam = LocalCameraPresets.createCustomWebcam(
  id: 'NEW-001',
  name: 'New Webcam',
  location: 'New Location',
);
UnifiedCameraManager.addCamera(newWebcam.toUnified());

// Remove camera
UnifiedCameraManager.removeCamera('OLD-001');
```

## 🔹 **Troubleshooting**

### **Common Issues**

#### **1. Camera Not Found**
```bash
# Check available cameras
flutter run -d windows
# Look for camera initialization messages
```

**Solution**: Ensure camera is connected and not in use by other applications.

#### **2. Permission Denied**
```bash
# Windows: Check camera privacy settings
# macOS: Check camera permissions in System Preferences
# Linux: Check camera device permissions
```

**Solution**: Grant camera permissions to your application.

#### **3. Stream Not Starting**
```dart
// Check camera status
final info = webcam.cameraInfo;
print('Camera info: $info');

// Check if camera is initialized
if (info['isInitialized'] == true) {
  print('Camera is properly initialized');
} else {
  print('Camera initialization failed');
}
```

**Solution**: Ensure camera is not being used by another application.

#### **4. Poor Performance**
```dart
// Try lower resolution
final lowResWebcam = LocalCameraPresets.createCustomWebcam(
  id: 'LOW-001',
  name: 'Low Res Webcam',
  location: 'Location',
  resolution: ResolutionPreset.medium, // Lower resolution
);
```

**Solution**: Reduce resolution or check system resources.

### **Debug Information**
```dart
// Get status summary
final status = LocalCameraStreamService.getStatusSummary();
print('Camera status: $status');

// Get active camera IDs
final activeIds = LocalCameraStreamService.getActiveCameraIds();
print('Active cameras: $activeIds');
```

## 🔹 **Best Practices**

### **Performance Optimization**
1. **Resolution**: Use appropriate resolution for your use case
2. **Stream Management**: Stop unused streams to free resources
3. **Error Handling**: Implement proper error handling and user feedback
4. **Resource Cleanup**: Always dispose cameras when done

### **Security Considerations**
1. **Local Access**: Local cameras are only accessible on the device
2. **No Network Exposure**: Webcam streams don't go over the network
3. **Permission Management**: Request camera permissions appropriately
4. **User Awareness**: Inform users when camera is active

### **User Experience**
1. **Permission Requests**: Explain why camera access is needed
2. **Status Indicators**: Show camera status (streaming, stopped, error)
3. **Error Messages**: Provide clear error messages and solutions
4. **Loading States**: Show loading indicators during camera operations

## 🔹 **Example Implementation**

### **Complete Camera Setup**
```dart
class CameraSetupExample {
  static Future<void> setupCameras() async {
    try {
      // Initialize unified camera manager
      await UnifiedCameraManager.initialize(
        initialCameras: UnifiedCameraPresets.getMixedSetup(),
      );
      
      print('Camera setup completed successfully');
      print('Total cameras: ${UnifiedCameraManager.cameraCount}');
      print('Local cameras: ${UnifiedCameraManager.localCameraCount}');
      print('IP cameras: ${UnifiedCameraManager.ipCameraCount}');
      
    } catch (e) {
      print('Camera setup failed: $e');
    }
  }
  
  static Future<void> startAllLocalCameras() async {
    final localCameras = UnifiedCameraManager.getLocalCameras();
    
    for (final camera in localCameras) {
      if (camera.type == CameraType.local) {
        // Convert to LocalCameraConfig and start stream
        // Implementation depends on your specific setup
      }
    }
  }
}
```

## 🔹 **Next Steps**

1. **Test Basic Setup**: Start with a simple webcam configuration
2. **Add IP Cameras**: Integrate your existing MJPEG cameras
3. **Customize UI**: Adapt the interface for your specific needs
4. **Add Features**: Implement recording, motion detection, etc.
5. **Scale Up**: Add more cameras as needed

## 🔹 **Support**

For additional help:
- Check the `IMPLEMENTATION_SUMMARY.md` for overall system details
- Review inline code comments in configuration files
- Test with different camera configurations
- Monitor console output for error messages

The system now supports both **local device cameras** and **IP cameras**, giving you the flexibility to monitor both local and remote locations!
