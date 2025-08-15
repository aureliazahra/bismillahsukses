import os, sys, io, json, time, csv, traceback
from typing import List, Generator, Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

import threading
import datetime
import cv2

# allow import local modules located one level above backend/
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

# try import gui/logger (optional fallback)
try:
    from gui import CameraThread, read_cameras_config, write_cameras_config
    from logger import init_logger, log_detection
    init_logger()
    LOCAL_MODULES_AVAILABLE = True
except Exception as e:
    print("Warning: local modules import failed:", e)
    LOCAL_MODULES_AVAILABLE = False

    def read_cameras_config(path=None):
        path = path or os.path.join(BASE_DIR, "cameras.json")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    def write_cameras_config(data, path=None):
        path = path or os.path.join(BASE_DIR, "cameras.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True

    def log_detection(*args, **kwargs):
        print("log_detection fallback", args, kwargs)

app = FastAPI(title="Obserra Backend API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ROOT = os.path.dirname(os.path.abspath(__file__))  # python/ directory
CAMERAS_PATH = os.path.join(ROOT, "cameras.json")
LOGS_DIR = os.path.join(ROOT, "logs")
LOG_CSV = os.path.join(LOGS_DIR, "log.csv")
ADMIN_JSON = os.path.join(ROOT, "admin.json")

# Threads & caches
CAM_THREADS: dict[int, "CameraThread"] = {}
_CAM_LOCK = threading.Lock()
_LAST_JPEG: dict[int, bytes] = {}  # per-camera last encoded JPEG


def ensure_logs():
    os.makedirs(LOGS_DIR, exist_ok=True)
    if not os.path.exists(LOG_CSV):
        with open(LOG_CSV, "w", newline="", encoding="utf-8") as f:
            # FIX: double dot -> single dot
            csv.writer(f).writerow(["timestamp", "kamera", "nama", "hasil", "skor"])


def read_cameras():
    try:
        return read_cameras_config(CAMERAS_PATH)
    except Exception:
        if os.path.exists(CAMERAS_PATH):
            with open(CAMERAS_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        return []


def write_cameras(cams):
    try:
        return write_cameras_config(cams, CAMERAS_PATH)
    except Exception:
        with open(CAMERAS_PATH, "w", encoding="utf-8") as f:
            json.dump(cams, f, indent=2, ensure_ascii=False)
        return True


def _encode_jpeg(frame_bgr) -> Optional[bytes]:
    try:
        ok, buf = cv2.imencode(".jpg", frame_bgr)
        if ok:
            return buf.tobytes()
    except Exception:
        traceback.print_exc()
    return None


def _draw_annotations_from_thread(thr: "CameraThread", frame_bgr):
    """
    Gambar anotasi dari thr.last_annotations ke frame_bgr.
    Auto-scale bila ukuran bbox tidak sesuai ukuran frame.
    """
    try:
        with thr.annotations_lock:
            annotations = [dict(a) for a in (thr.last_annotations or [])]
    except Exception:
        annotations = []

    H, W = frame_bgr.shape[:2]
    # Dimensi referensi (deteksi/drawing di thread)
    refW = int(getattr(thr, "width", W) or W)
    refH = int(getattr(thr, "height", H) or H)
    sx = (W / refW) if refW > 0 else 1.0
    sy = (H / refH) if refH > 0 else 1.0

    for ann in annotations:
        try:
            if ann.get("skipped") and ann.get("skip_reason") == "blur" and (not getattr(thr, "show_skipped_blur", False)):
                continue
            x1, y1, x2, y2 = ann["bbox"]
            # scale jika ukuran berbeda
            if sx != 1.0 or sy != 1.0:
                x1, y1, x2, y2 = int(x1 * sx), int(y1 * sy), int(x2 * sx), int(y2 * sy)

            match = bool(ann.get("match"))
            color = (0, 255, 0) if match else (0, 0, 255)
            if match:
                label = f"{ann.get('name','unknown')} ({ann.get('score',0.0):.2f})"
            else:
                if ann.get("skipped"):
                    label = f"SKIP:{ann.get('skip_reason','skip')}"
                else:
                    label = ann.get("name", "tidak cocok")
            if ann.get("antispoof_checked") and (not ann.get("antispoof_live", True)):
                color = (0, 0, 255)
                label = "FAKE"
            cv2.rectangle(
                frame_bgr,
                (max(0, int(x1)), max(0, int(y1))),
                (min(W, int(x2)), min(H, int(y2))),
                color,
                2,
            )
            cv2.putText(
                frame_bgr,
                label,
                (max(0, int(x1)), max(15, int(y1) - 5)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                2,
            )
        except Exception:
            continue
    return frame_bgr


# ---------- Cameras CRUD ----------
@app.get("/api/cameras")
def api_get_cameras():
    cams = read_cameras()
    out = []
    with _CAM_LOCK:
        for i, c in enumerate(cams):
            status = "running" if i in CAM_THREADS and getattr(CAM_THREADS[i], "running", False) else "stopped"
            out.append({**c, "_idx": i, "_status": status})
    return out


@app.post("/api/cameras")
def api_add_camera(payload: dict):
    cams = read_cameras()
    cams.append(payload)
    write_cameras(cams)
    return {"ok": True}


@app.put("/api/cameras/{idx}")
def api_update_camera(idx: int, payload: dict):
    cams = read_cameras()
    if idx < 0 or idx >= len(cams):
        raise HTTPException(404, "camera not found")
    cams[idx].update(payload)
    write_cameras(cams)
    return {"ok": True}


@app.delete("/api/cameras/{idx}")
def api_delete_camera(idx: int):
    cams = read_cameras()
    if idx < 0 or idx >= len(cams):
        raise HTTPException(404, "camera not found")
    cams.pop(idx)
    write_cameras(cams)
    with _CAM_LOCK:
        thr = CAM_THREADS.pop(idx, None)
    if thr:
        try:
            thr.stop()
        except Exception:
            pass
    _LAST_JPEG.pop(idx, None)
    return {"ok": True}


# ---------- Camera control ----------
@app.get("/api/camera/test")
def api_test_cameras():
    """Test available cameras on the system"""
    available_cameras = []
    
    for i in range(5):  # Test first 5 camera indices
        try:
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret and frame is not None:
                    height, width = frame.shape[:2]
                    available_cameras.append({
                        "index": i,
                        "resolution": f"{width}x{height}",
                        "status": "available"
                    })
                else:
                    available_cameras.append({
                        "index": i,
                        "status": "opened_but_no_frame"
                    })
            else:
                available_cameras.append({
                    "index": i,
                    "status": "not_available"
                })
            cap.release()
        except Exception as e:
            available_cameras.append({
                "index": i,
                "status": "error",
                "error": str(e)
            })
    
    return {
        "available_cameras": available_cameras,
        "total_tested": len(available_cameras)
    }

@app.post("/api/camera/{idx}/start")
def api_start_camera(idx: int):
    cams = read_cameras()
    if idx < 0 or idx >= len(cams):
        raise HTTPException(404, "camera not found")
    with _CAM_LOCK:
        if idx in CAM_THREADS and getattr(CAM_THREADS[idx], "running", False):
            return {"ok": True, "msg": "already running"}
        cfg = cams[idx]
        if not LOCAL_MODULES_AVAILABLE:
            raise HTTPException(500, "CameraThread not available (local modules missing).")
        try:
            thr = CameraThread(
                cfg.get("name", f"cam{idx}"),
                cfg.get("source"),
                [],  # known_faces bisa ditambahkan jika perlu
                width=cfg.get("width", 480),
                height=cfg.get("height", 320),
                display_interval_ms=cfg.get("display_interval_ms", 50),
                detect_interval_frames=cfg.get("detect_interval_frames", 3),
                reconnect_delay=cfg.get("reconnect_delay", 10),
                match_threshold=cfg.get("match_threshold", 0.5),
                min_sharpness_percent=cfg.get("min_sharpness_percent", 20),
                sharpness_var_max=cfg.get("sharpness_var_max", 1000),
                require_human_check=bool(cfg.get("require_human_check", False)),
                exposure_enabled=bool(cfg.get("exposure_enabled", True)),
                exposure_gain=float(cfg.get("exposure_gain", 1.4)),
                min_luminance=float(cfg.get("min_luminance", 60)),
                frame_buffer=int(cfg.get("frame_buffer", 1)),
                antispoof_enabled=bool(cfg.get("antispoof_enabled", False)),
                antispoof_interval=int(cfg.get("antispoof_interval", 15)),
                antispoof_model_path=str(cfg.get("antispoof_model_path", "")),
                antispoof_threshold=float(cfg.get("antispoof_threshold", 0.5)),
                show_skipped_blur=bool(cfg.get("show_skipped_blur", False)),
                blur_backoff_trigger=int(cfg.get("blur_backoff_trigger", 3)),
                blur_backoff_frames=int(cfg.get("blur_backoff_frames", 5)),
            )
            thr.start_camera_and_thread()
            CAM_THREADS[idx] = thr
            _LAST_JPEG.pop(idx, None)
            return {"ok": True}
        except Exception as e:
            traceback.print_exc()
            raise HTTPException(500, f"start failed: {e}")


@app.post("/api/camera/{idx}/stop")
def api_stop_camera(idx: int):
    with _CAM_LOCK:
        thr = CAM_THREADS.get(idx)
    if thr:
        try:
            thr.stop()
        except Exception:
            pass
        with _CAM_LOCK:
            CAM_THREADS.pop(idx, None)
        _LAST_JPEG.pop(idx, None)
        return {"ok": True}
    return {"ok": False, "msg": "not running"}


@app.get("/api/camera/{idx}/status")
def api_camera_status(idx: int):
    """
    Tambahan informasi ukuran untuk membantu overlay di front-end:
    - frame_width/frame_height: ukuran aktual frame terakhir
    - ref_width/ref_height: ukuran referensi (config) saat deteksi/drawing
    """
    with _CAM_LOCK:
        thr = CAM_THREADS.get(idx)
    if not thr:
        return {"running": False}

    # salin anotasi terakhir
    try:
        with thr.annotations_lock:
            anns = [dict(a) for a in (thr.last_annotations or [])]
    except Exception:
        anns = []

    # ukur dimensi aktual frame terakhir jika tersedia
    frame_w = frame_h = None
    try:
        if getattr(thr, "camera", None):
            frame = thr.camera.get_frame()
            if frame is not None:
                frame_h, frame_w = frame.shape[:2]
    except Exception:
        pass

    # dimensi referensi (ukuran yang dipakai thread)
    ref_w = int(getattr(thr, "width", 0) or 0)
    ref_h = int(getattr(thr, "height", 0) or 0)

    return {
        "running": True,
        "last_annotations": anns,
        "frame_width": frame_w,
        "frame_height": frame_h,
        "ref_width": ref_w,
        "ref_height": ref_h,
    }


# ---------- Frames ----------
@app.get("/api/camera/{idx}/snapshot")
def api_camera_snapshot(idx: int):
    """
    Snapshot stabil:
    - Jika thread kamera ada: JANGAN buka capture kedua. Tunggu frame sebentar lalu pakai.
      Kalau belum ada frame, kirim last JPEG (kalau ada) untuk hindari freeze.
    - Jika thread tidak ada: baru fallback buka capture sekali.
    """
    cams = read_cameras()
    if idx < 0 or idx >= len(cams):
        raise HTTPException(404, "camera not found")
    cfg = cams[idx]

    with _CAM_LOCK:
        thr = CAM_THREADS.get(idx)

    # 1) Thread aktif: gunakan frame dari thread saja
    if thr and getattr(thr, "camera", None):
        # Tunggu hingga 600ms untuk dapat frame
        frame = None
        deadline = time.time() + 0.6
        while time.time() < deadline:
            frame = thr.camera.get_frame()
            if frame is not None:
                break
            time.sleep(0.02)

        if frame is not None:
            frame_drawn = _draw_annotations_from_thread(thr, frame.copy())
            buf = _encode_jpeg(frame_drawn)
            if buf:
                _LAST_JPEG[idx] = buf
                return StreamingResponse(io.BytesIO(buf), media_type="image/jpeg")

        # Tidak ada frame baru → kirim last good JPEG kalau tersedia
        last = _LAST_JPEG.get(idx)
        if last:
            return StreamingResponse(io.BytesIO(last), media_type="image/jpeg")

        # Tidak ada last JPEG → 503 (bukan 500) agar client bisa retry
        raise HTTPException(503, "no frame available yet")

    # 2) Thread tidak aktif: fallback buka capture sekali
    source = cfg.get("source")
    cap = None
    try:
        if isinstance(source, (int, float)) or (isinstance(source, str) and str(source).isdigit()):
            cap = cv2.VideoCapture(int(source))
        else:
            cap = cv2.VideoCapture(str(source))
        
        # Check if camera opened successfully
        if not cap.isOpened():
            raise HTTPException(503, f"cannot open camera source: {source}")
        
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, int(cfg.get("width", 480)))
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, int(cfg.get("height", 320)))
        
        # Try to read frame with timeout
        ok, frame = cap.read()
        if not ok or frame is None:
            raise HTTPException(503, "no frame from capture")
        
        buf = _encode_jpeg(frame)
        if not buf:
            raise HTTPException(500, "imencode failed")
        _LAST_JPEG[idx] = buf
        return StreamingResponse(io.BytesIO(buf), media_type="image/jpeg")
    except HTTPException:
        raise
    except Exception as e:
        print(f"Camera snapshot error: {e}")
        raise HTTPException(503, f"camera error: {str(e)}")
    finally:
        try:
            if cap:
                cap.release()
        except Exception:
            pass


@app.get("/api/camera/{idx}/mjpeg")
def api_camera_mjpeg(idx: int):
    cams = read_cameras()
    if idx < 0 or idx >= len(cams):
        raise HTTPException(404, "camera not found")
    with _CAM_LOCK:
        thr = CAM_THREADS.get(idx)
    if not thr or not getattr(thr, "camera", None):
        raise HTTPException(409, "camera not started")

    boundary = "frameboundary"

    def gen() -> Generator[bytes, None, None]:
        while True:
            try:
                frame = thr.camera.get_frame()
                if frame is None:
                    # kirim last JPEG bila ada agar stream tidak stagnan
                    last = _LAST_JPEG.get(idx)
                    if last:
                        yield (
                            b"--" + boundary.encode() + b"\r\n"
                            b"Content-Type: image/jpeg\r\n"
                            b"Content-Length: " + str(len(last)).encode() + b"\r\n\r\n"
                            + last + b"\r\n"
                        )
                        time.sleep(0.05)
                        continue
                    time.sleep(0.02)
                    continue
                frame_drawn = _draw_annotations_from_thread(thr, frame.copy())
                buf = _encode_jpeg(frame_drawn)
                if buf:
                    _LAST_JPEG[idx] = buf
                    yield (
                        b"--" + boundary.encode() + b"\r\n"
                        b"Content-Type: image/jpeg\r\n"
                        b"Content-Length: " + str(len(buf)).encode() + b"\r\n\r\n"
                        + buf + b"\r\n"
                    )
                time.sleep(max(0.0, float(getattr(thr, "display_interval_ms", 40)) / 1000.0))
            except GeneratorExit:
                break
            except Exception:
                traceback.print_exc()
                time.sleep(0.05)

    return StreamingResponse(gen(), media_type=f"multipart/x-mixed-replace; boundary={boundary}")


# ---------- Reports ----------
@app.get("/api/reports")
def api_get_reports():
    ensure_logs()
    rows = []
    with open(LOG_CSV, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        _ = next(reader, None)  # header
        for r in reader:
            rows.append(r)
    return {"rows": rows}


# ---------- Admin ----------
@app.get("/api/admin")
def api_get_admin():
    if not os.path.exists(ADMIN_JSON):
        with open(ADMIN_JSON, "w", encoding="utf-8") as f:
            json.dump({"users": [{"username": "admin", "email": "admin@example.com", "password": ""}]}, f, indent=2)
    with open(ADMIN_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


@app.post("/api/admin")
def api_post_admin(payload: dict):
    with open(ADMIN_JSON, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    return {"ok": True}


# ---------- Dashboard ----------
@app.get("/api/dashboard")
def api_dashboard():
    cams = read_cameras()
    ensure_logs()
    total_cams = len(cams)
    with _CAM_LOCK:
        active = sum(1 for i in range(total_cams) if i in CAM_THREADS and getattr(CAM_THREADS[i], "running", False))
    matched_today = matched_week = matched_month = 0
    try:
        today = datetime.date.today()
        if os.path.exists(LOG_CSV):
            with open(LOG_CSV, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                next(reader, None)
                for row in reader:
                    try:
                        ts = datetime.datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S")
                        days = (today - ts.date()).days
                        if days == 0:
                            matched_today += 1
                        if days <= 7:
                            matched_week += 1
                        if days <= 31:
                            matched_month += 1
                    except Exception:
                        continue
    except Exception:
        pass
    return {
        "total_cameras": total_cams,
        "active_cameras": active,
        "matched_today": matched_today,
        "matched_week": matched_week,
        "matched_month": matched_month,
    }


# Optionally serve built frontend
FRONTEND_DIST = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend_build")
if os.path.exists(FRONTEND_DIST):
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")
