
import os, json
from typing import List
from fastapi import APIRouter, HTTPException
from ..models.camera import Camera
from ..services.camera_manager import manager

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
CAMERAS_JSON = os.path.join(DATA_DIR, "cameras.json")

router = APIRouter()

def _read_cams()->list:
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(CAMERAS_JSON):
        with open(CAMERAS_JSON, "w", encoding="utf-8") as f: json.dump([], f)
        return []
    with open(CAMERAS_JSON, "r", encoding="utf-8") as f:
        return json.load(f)

def _write_cams(data:list):
    with open(CAMERAS_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

@router.get("", response_model=List[Camera])
def list_cameras():
    return _read_cams()

@router.put("", response_model=List[Camera])
def replace_cameras(cams: List[Camera]):
    data=[c.model_dump() for c in cams]; _write_cams(data)
    manager.stop_all()
    for idx, c in enumerate(cams):
        manager.ensure(idx, c.name, c.source,
                       display_interval_ms=c.display_interval_ms,
                       detect_interval_frames=c.detect_interval_frames,
                       reconnect_delay=c.reconnect_delay,
                       frame_buffer=c.frame_buffer)
    return cams

@router.post("/{idx}/start")
def start_camera(idx:int):
    cams=[Camera(**c) for c in _read_cams()]
    if idx<0 or idx>=len(cams): raise HTTPException(404, "index out of range")
    c=cams[idx]
    manager.ensure(idx, c.name, c.source,
                   display_interval_ms=c.display_interval_ms,
                   detect_interval_frames=c.detect_interval_frames,
                   reconnect_delay=c.reconnect_delay,
                   frame_buffer=c.frame_buffer)
    return {"ok": True}

@router.post("/{idx}/stop")
def stop_camera(idx:int):
    manager.stop(idx); return {"ok": True}

@router.get("/status")
def status():
    out=[]
    for cid, w in manager.list().items():
        lat, drop = w.metrics()
        out.append({"id":cid,"name":w.name,"latency_ms":int(lat),"drop_pct":round(drop,1)})
    return out
