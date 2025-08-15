import cv2
import sys

def check_cameras():
    """Check available cameras on the system"""
    print("Checking available cameras...")
    print("=" * 50)
    
    # Try different camera indices
    for i in range(10):
        print(f"Testing camera index {i}...")
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret and frame is not None:
                height, width = frame.shape[:2]
                print(f"✓ Camera {i} is available - Resolution: {width}x{height}")
                # Try to get camera properties
                fps = cap.get(cv2.CAP_PROP_FPS)
                print(f"  FPS: {fps}")
            else:
                print(f"✗ Camera {i} opened but cannot read frames")
            cap.release()
        else:
            print(f"✗ Camera {i} is not available")
    
    print("\n" + "=" * 50)
    print("Camera check completed.")
    print("\nIf no cameras are found, try:")
    print("1. Check if your webcam is connected and working")
    print("2. Check Windows Camera app to see if camera works")
    print("3. Update camera drivers")
    print("4. Try using a different camera index in cameras.json")

if __name__ == "__main__":
    check_cameras()
