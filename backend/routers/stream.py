
import cv2
from fastapi import APIRouter, HTTPException
from starlette.responses import StreamingResponse
from ..services.camera_manager import manager

router = APIRouter()

@router.get("/mjpg/{idx}")
def mjpg(idx:int):
    cam = manager.get(idx)
    if cam is None: raise HTTPException(404, "camera not running")
    def gen():
        boundary=b"--frame"
        while True:
            fr = cam.snapshot_annotated()
            if fr is None:
                yield boundary + b"\r\nContent-Type: image/jpeg\r\n\r\n" + b"" + b"\r\n"; continue
            ok, jpg = cv2.imencode(".jpg", fr, [cv2.IMWRITE_JPEG_QUALITY, 80])
            if not ok: continue
            yield boundary + b"\r\nContent-Type: image/jpeg\r\n\r\n" + jpg.tobytes() + b"\r\n"
    return StreamingResponse(gen(), media_type="multipart/x-mixed-replace; boundary=frame")
