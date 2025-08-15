#!/usr/bin/env python3
"""
Camera Setup and Diagnostic Script for Obserra Backend
This script helps diagnose and fix camera access issues.
"""

import cv2
import json
import os
import sys
import time
from pathlib import Path

def check_opencv_version():
    """Check OpenCV version and capabilities"""
    print("=" * 60)
    print("OpenCV Version Check")
    print("=" * 60)
    print(f"OpenCV Version: {cv2.__version__}")
    print(f"Build Information: {cv2.getBuildInformation()}")
    
    # Check if MSMF backend is available
    build_info = cv2.getBuildInformation()
    if "Media Foundation" in build_info:
        print("✓ Media Foundation backend available")
    else:
        print("✗ Media Foundation backend not available")
    
    # Check available backends
    backends = [
        (cv2.CAP_ANY, "CAP_ANY"),
        (cv2.CAP_MSMF, "CAP_MSMF"),
        (cv2.CAP_DSHOW, "CAP_DSHOW"),
        (cv2.CAP_FFMPEG, "CAP_FFMPEG"),
    ]
    
    print("\nTesting backends:")
    for backend_id, backend_name in backends:
        try:
            cap = cv2.VideoCapture(0, backend_id)
            if cap.isOpened():
                print(f"✓ {backend_name} works")
                cap.release()
            else:
                print(f"✗ {backend_name} failed")
        except Exception as e:
            print(f"✗ {backend_name} error: {e}")

def test_camera_indices():
    """Test different camera indices"""
    print("\n" + "=" * 60)
    print("Camera Index Test")
    print("=" * 60)
    
    available_cameras = []
    
    for i in range(10):
        print(f"\nTesting camera index {i}...")
        cap = None
        try:
            # Try with default backend
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret and frame is not None:
                    height, width = frame.shape[:2]
                    fps = cap.get(cv2.CAP_PROP_FPS)
                    print(f"✓ Camera {i} is available")
                    print(f"  Resolution: {width}x{height}")
                    print(f"  FPS: {fps}")
                    available_cameras.append({
                        "index": i,
                        "resolution": f"{width}x{height}",
                        "fps": fps,
                        "status": "available"
                    })
                else:
                    print(f"✗ Camera {i} opened but cannot read frames")
                    available_cameras.append({
                        "index": i,
                        "status": "opened_but_no_frame"
                    })
            else:
                print(f"✗ Camera {i} is not available")
                available_cameras.append({
                    "index": i,
                    "status": "not_available"
                })
        except Exception as e:
            print(f"✗ Camera {i} error: {e}")
            available_cameras.append({
                "index": i,
                "status": "error",
                "error": str(e)
            })
        finally:
            if cap:
                cap.release()
    
    return available_cameras

def test_different_backends():
    """Test cameras with different backends"""
    print("\n" + "=" * 60)
    print("Backend Compatibility Test")
    print("=" * 60)
    
    backends = [
        (cv2.CAP_ANY, "CAP_ANY"),
        (cv2.CAP_MSMF, "CAP_MSMF"),
        (cv2.CAP_DSHOW, "CAP_DSHOW"),
        (cv2.CAP_FFMPEG, "CAP_FFMPEG"),
    ]
    
    results = {}
    
    for backend_id, backend_name in backends:
        print(f"\nTesting {backend_name}...")
        backend_results = []
        
        for i in range(3):  # Test first 3 indices
            try:
                cap = cv2.VideoCapture(i, backend_id)
                if cap.isOpened():
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        height, width = frame.shape[:2]
                        print(f"  ✓ Camera {i}: {width}x{height}")
                        backend_results.append({
                            "index": i,
                            "resolution": f"{width}x{height}",
                            "status": "available"
                        })
                    else:
                        print(f"  ✗ Camera {i}: opened but no frame")
                        backend_results.append({
                            "index": i,
                            "status": "opened_but_no_frame"
                        })
                else:
                    print(f"  ✗ Camera {i}: not available")
                    backend_results.append({
                        "index": i,
                        "status": "not_available"
                    })
                cap.release()
            except Exception as e:
                print(f"  ✗ Camera {i}: error - {e}")
                backend_results.append({
                    "index": i,
                    "status": "error",
                    "error": str(e)
                })
        
        results[backend_name] = backend_results
    
    return results

def update_camera_config(available_cameras):
    """Update camera configuration based on available cameras"""
    print("\n" + "=" * 60)
    print("Camera Configuration Update")
    print("=" * 60)
    
    # Find the best available camera
    best_camera = None
    for cam in available_cameras:
        if cam.get("status") == "available":
            best_camera = cam
            break
    
    if not best_camera:
        print("No available cameras found!")
        return False
    
    print(f"Best available camera: Index {best_camera['index']}")
    print(f"Resolution: {best_camera['resolution']}")
    
    # Read current config
    config_path = Path("cameras.json")
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
    else:
        config = []
    
    # Update or add camera configuration
    if config:
        # Update first camera
        config[0]["source"] = best_camera["index"]
        config[0]["name"] = f"Kamera CCTV 1 (Auto-detected)"
        print(f"Updated existing camera config to use index {best_camera['index']}")
    else:
        # Create new camera config
        new_camera = {
            "name": f"Kamera CCTV 1 (Auto-detected)",
            "source": best_camera["index"],
            "width": 640,
            "height": 480,
            "display_interval_ms": 50,
            "detect_interval_frames": 3,
            "reconnect_delay": 10,
            "match_threshold": 0.6,
            "min_sharpness_percent": 8,
            "sharpness_var_max": 1000,
            "require_human_check": True,
            "exposure_enabled": True,
            "exposure_gain": 1.4,
            "min_luminance": 55,
            "frame_buffer": 1,
            "antispoof_enabled": True,
            "antispoof_interval": 10,
            "antispoof_model_path": "",
            "antispoof_threshold": 0.5,
            "show_skipped_blur": False,
            "blur_backoff_trigger": 3,
            "blur_backoff_frames": 4,
            "id": "CAM-AUTO",
            "last_updated": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "status": "Active"
        }
        config.append(new_camera)
        print(f"Created new camera config with index {best_camera['index']}")
    
    # Write updated config
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print(f"Configuration saved to {config_path}")
    return True

def main():
    """Main diagnostic function"""
    print("Obserra Camera Setup and Diagnostic Tool")
    print("=" * 60)
    
    # Check OpenCV
    check_opencv_version()
    
    # Test camera indices
    available_cameras = test_camera_indices()
    
    # Test different backends
    backend_results = test_different_backends()
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    available_count = sum(1 for cam in available_cameras if cam.get("status") == "available")
    print(f"Available cameras: {available_count}")
    
    if available_count == 0:
        print("\n❌ NO CAMERAS FOUND!")
        print("\nTroubleshooting steps:")
        print("1. Check if your webcam is connected and working")
        print("2. Test your camera in Windows Camera app")
        print("3. Update camera drivers")
        print("4. Check Windows privacy settings for camera access")
        print("5. Try running as administrator")
        print("6. Check if another application is using the camera")
        return False
    
    # Update configuration
    success = update_camera_config(available_cameras)
    
    if success:
        print("\n✅ Camera setup completed successfully!")
        print("You can now run the backend with: python start_backend.bat")
    else:
        print("\n❌ Camera setup failed!")
    
    return success

if __name__ == "__main__":
    try:
        success = main()
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nSetup interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nSetup failed with error: {e}")
        sys.exit(1)
