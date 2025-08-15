#!/usr/bin/env python3
"""
Quick Camera Fix Script
This script quickly tests different camera indices and updates the configuration.
"""

import cv2
import json
import os
import sys

def quick_camera_test():
    """Quick test to find working camera"""
    print("Quick Camera Test - Finding working camera...")
    
    # Test camera indices 0-5
    for i in range(6):
        print(f"Testing camera {i}...")
        try:
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret and frame is not None:
                    print(f"✓ Camera {i} works!")
                    cap.release()
                    return i
                else:
                    print(f"✗ Camera {i} opened but no frame")
            else:
                print(f"✗ Camera {i} not available")
            cap.release()
        except Exception as e:
            print(f"✗ Camera {i} error: {e}")
    
    return None

def update_camera_config(camera_index):
    """Update cameras.json with working camera index"""
    config_path = "cameras.json"
    
    # Read current config
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
    else:
        config = []
    
    # Update first camera or create new one
    if config:
        config[0]["source"] = camera_index
        config[0]["name"] = f"Kamera CCTV 1 (Fixed)"
        print(f"Updated camera config to use index {camera_index}")
    else:
        new_camera = {
            "name": f"Kamera CCTV 1 (Fixed)",
            "source": camera_index,
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
            "id": "CAM-FIXED",
            "status": "Active"
        }
        config.append(new_camera)
        print(f"Created new camera config with index {camera_index}")
    
    # Write updated config
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print(f"Configuration saved to {config_path}")

def main():
    """Main function"""
    print("Quick Camera Fix Tool")
    print("=" * 40)
    
    # Find working camera
    working_camera = quick_camera_test()
    
    if working_camera is not None:
        print(f"\n✅ Found working camera at index {working_camera}")
        update_camera_config(working_camera)
        print("\n✅ Camera configuration updated!")
        print("You can now run the backend.")
        return True
    else:
        print("\n❌ No working cameras found!")
        print("\nTry these steps:")
        print("1. Connect a webcam")
        print("2. Check Windows Camera app")
        print("3. Update camera drivers")
        print("4. Check Windows privacy settings")
        print("5. Try running as administrator")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
