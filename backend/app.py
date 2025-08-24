# backend/app.py — FastAPI MJPEG streaming + CCTV management CRUD + logs/captures + Missing People + upload + app-config endpoints
import os, cv2, time, json, threading, logging, csv, platform, subprocess, uuid, re, unicodedata
from typing import Dict, Any, List, Optional, Union
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# ==== Path dasar ====
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
APP_CONFIG_PATH = os.path.join(BASE_DIR, "app_config.json")
CAMERAS_JSON    = os.path.join(BASE_DIR, "cameras.json")
TARGET_FACES    = os.path.join(BASE_DIR, "target_faces")
CAPTURES_DIR    = os.path.join(BASE_DIR, "captures")
LOGS_DIR        = os.path.join(BASE_DIR, "logs")
LOG_CSV         = os.path.join(LOGS_DIR, "log.csv")
MISSING_JSON    = os.path.join(BASE_DIR, "missing_people.json")

os.makedirs(TARGET_FACES, exist_ok=True)
os.makedirs(CAPTURES_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)
if not os.path.isfile(MISSING_JSON):
    with open(MISSING_JSON, "w", encoding="utf-8") as f:
        json.dump([], f)

# ==== Import detector.py (sama persis seperti GUI PyQt) ====
from detector import (
    initialize as det_initialize,
    load_antispoof_model,
    set_antispoof_params,
    load_known_faces,
    process_frame_for_faces,
)



# ------------ Util JSON ------------
def read_json(path: str, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def write_json(path: str, data) -> bool:
    try:
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(tmp, path)
        return True
    except Exception:
        logging.exception("Failed writing %s", path)
        return False

# ------------ Filename helpers ------------
ALLOWED_EXTS = (".jpg", ".jpeg", ".png", ".webp", ".bmp")

def _slugify_name(s: str) -> str:
    s = str(s or "").strip()
    if not s:
        return "unknown"
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    s = re.sub(r"[^\w\s-]", "", s)
    s = s.strip().lower()
    s = re.sub(r"[\s_-]+", "-", s)
    s = s.strip("-")
    return s or "unknown"

def _unique_filename(base: str, ext: str):
    base = _slugify_name(base) or "unknown"
    ext = (ext or ".jpg").lower()
    if ext not in ALLOWED_EXTS:
        ext = ".jpg"
    fname = f"{base}{ext}"
    path = os.path.join(TARGET_FACES, fname)
    if not os.path.exists(path):
        return fname, path
    i = 1
    while True:
        cand = f"{base}-{i}{ext}"
        path2 = os.path.join(TARGET_FACES, cand)
        if not os.path.exists(path2):
            return cand, path2
        i += 1

def _rename_target_to_name(url: str, name: str) -> str:
    """
    Rename file di TARGET_FACES agar mengikuti 'name' (slugified).
    Mengembalikan URL baru jika sukses, atau URL lama jika gagal/tidak perlu.
    """
    try:
        if not url or not name:
            return url
        if not str(url).startswith("/static/target_faces/"):
            return url
        fname = os.path.basename(url)
        old_path = os.path.join(TARGET_FACES, fname)
        if not os.path.isfile(old_path):
            return url
        ext = os.path.splitext(fname)[1].lower() or ".jpg"
        base_now = os.path.splitext(fname)[0].lower()
        desired = _slugify_name(name)
        # Jika sudah sesuai (misal "john-doe.jpg" atau "john-doe-2.jpg"), skip
        if base_now.startswith(desired):
            return url
        new_fname, new_path = _unique_filename(desired, ext)
        os.replace(old_path, new_path)
        return f"/static/target_faces/{new_fname}"
    except Exception:
        logging.exception("rename target image failed")
        return url

# ------------ Bool helper aman (string/int/bool) ------------
def _as_bool(v) -> bool:
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return v != 0
    if isinstance(v, str):
        s = v.strip().lower()
        if s in ("1", "true", "yes", "y", "on", "active", "enabled", "aktif", "enable"):
            return True
        if s in ("0", "false", "no", "n", "off", "disabled", "nonaktif", "disable"):
            return False
    return False

def read_app_config() -> Dict[str, Any]:
    cfg = {
        "device": "CPU",
        "detector_backend": "insightface",
        "antispoof_backend": "off",           # "off" | "minifasnet"
        "antispoof_model_path": "",
        "match_threshold": 0.60,
        "red_cutoff_threshold": 0.40,
        "require_human_check": True,
        "box_thickness_max": 6,
        "antispoof_preprocess": "bgr_norm",
        "antispoof_live_index": 2,            # -1=auto
        "antispoof_mode": "medium",
        "antispoof_thresholds": {"low": 0.40, "medium": 0.55, "high": 0.70},
        "antispoof_smooth_k": 3,
        "min_live_face_size": 90,
        "min_interocular_px": 38,
        "suppress_small_faces_when_antispoof": True,

        # Settings → Logs
        "log_save_mode": "photo",             # "photo" | "video"
        "log_save_which": "green",            # "green" | "all"
        "log_interval_sec": 3,

        "debug": False,
        # MJPEG streaming tuneables
        "mjpeg_quality": 65,
        "mjpeg_max_width": 960,       # 0 = disabled (keep native width)
        "mjpeg_optimize": True,
        "mjpeg_adaptive": True,       # auto-lower quality if frame is too big
        "mjpeg_target_kb": 180,
    }
    cfg.update(read_json(APP_CONFIG_PATH, {}))
    return cfg

def read_cameras_raw() -> List[Dict[str, Any]]:
    lst = read_json(CAMERAS_JSON, [])
    return lst if isinstance(lst, list) else []

def write_cameras_raw(lst: List[Dict[str, Any]]) -> bool:
    return write_json(CAMERAS_JSON, lst)

def cams_for_worker() -> List[Dict[str, Any]]:
    cams = read_cameras_raw()
    out = []
    for c in cams:
        out.append({
            "name": c.get("name", c.get("location", c.get("id", "Camera"))),
            "source": c.get("source", 0),
            "display_interval_ms": int(c.get("display_interval_ms", 50)),
            "detect_interval_frames": int(c.get("detect_interval_frames", 3)),
            "reconnect_delay": int(c.get("reconnect_delay", 10)),
            "frame_buffer": int(c.get("frame_buffer", 1)),
            "exposure_enabled": _as_bool(c.get("exposure_enabled", True)),
            "exposure_gain": float(c.get("exposure_gain", 1.4)),
            "min_luminance": float(c.get("min_luminance", 60)),
        })
    return out

# ------------ Detector init ------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
CFG = read_app_config()
USE_GPU = str(CFG.get("device", "CPU")).upper() == "GPU"

DETECTOR_READY = True
try:
    logging.info("Initializing detector (gpu=%s, backend=%s)", USE_GPU, CFG.get("detector_backend"))
    det_initialize(use_gpu=USE_GPU, detector_backend=CFG.get("detector_backend", "insightface"))
    backend = str(CFG.get("antispoof_backend", "off")).lower()
    if backend == "minifasnet":
        try:
            load_antispoof_model(CFG.get("antispoof_model_path", ""), use_gpu=USE_GPU)
        except Exception:
            logging.exception("load_antispoof_model failed")
    def _apply_antispoof_from_cfg():
        try:
            live_idx = CFG.get("antispoof_live_index", 2)
            if isinstance(live_idx, int) and live_idx < 0:
                live_idx = None
            set_antispoof_params(
                live_index=live_idx,
                thresholds=CFG.get("antispoof_thresholds", {"low": 0.40, "medium": 0.55, "high": 0.70}),
                mode=CFG.get("antispoof_mode", "medium"),
                preprocess=CFG.get("antispoof_preprocess", "bgr_norm"),
                smooth_k=int(CFG.get("antispoof_smooth_k", 3)),
            )
        except Exception:
            logging.exception("set_antispoof_params failed")
    _apply_antispoof_from_cfg()
except Exception:
    DETECTOR_READY = False
    logging.exception("Detector initialization failed; API will still run.")

MATCH_TH = float(CFG.get("match_threshold", 0.60))
RED_CUTOFF = float(CFG.get("red_cutoff_threshold", 0.40))
BOX_THICK_MAX = int(CFG.get("box_thickness_max", 6))
KNOWN = load_known_faces(TARGET_FACES if os.path.isdir(TARGET_FACES) else None) if DETECTOR_READY else {}

# ------------ Worker per kamera ------------
class CameraWorker:
    def __init__(self, idx: int, cam_cfg: Dict[str, Any]):
        self.idx = idx
        self.name = cam_cfg["name"]
        src = cam_cfg["source"]
        self.source = int(src) if (isinstance(src, str) and str(src).isdigit()) else src
        self.display_interval_ms = int(cam_cfg.get("display_interval_ms", 50))
        self.detect_interval_frames = int(cam_cfg.get("detect_interval_frames", 3))
        self.reconnect_delay = int(cam_cfg.get("reconnect_delay", 10))
        self.frame_buffer = int(cam_cfg.get("frame_buffer", 1))
        self.exposure_enabled = _as_bool(cam_cfg.get("exposure_enabled", True))
        self.exposure_gain = float(cam_cfg.get("exposure_gain", 1.4))
        self.min_luminance = float(cam_cfg.get("min_luminance", 60))
        self._cap = None
        self._stop = threading.Event()
        self._thread = None
        self._last_jpeg: Optional[bytes] = None
        self._last_anns: List[Dict[str, Any]] = []
        self._frame_counter = 0

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        t = self._thread
        if t and t.is_alive():
            t.join(timeout=1.0)
        try:
            if self._cap: self._cap.release()
        except Exception:
            pass

    def _open(self):
        try:
            if isinstance(self.source, (int, str)) and str(self.source).isdigit():
                cap = cv2.VideoCapture(int(self.source))
            else:
                cap = cv2.VideoCapture(self.source, cv2.CAP_FFMPEG)
            try:
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            except Exception:
                pass
            if not cap.isOpened():
                cap.release()
                return None
            return cap
        except Exception:
            return None

    def _draw(self, bgr, ann):
        (x1, y1, x2, y2) = [int(v) for v in ann["bbox"]]
        is_live = ann.get("antispoof_live", True)
        matched = bool(ann.get("match", False))
        score = float(ann.get("score", 0.0))

        # Warna kotak
        if matched and is_live:
            color = (0, 255, 0)       # hijau
        elif is_live and score >= RED_CUTOFF:
            color = (0, 165, 255)     # oranye kandidat
        else:
            color = (0, 0, 255)       # merah

        thick = max(2, min(BOX_THICK_MAX, 3 + int(0.004 * max(bgr.shape[:2]))))
        cv2.rectangle(bgr, (x1, y1), (x2, y2), color, thick)

        # Label:
        label = ""
        if matched and is_live:
            nm = str(ann.get("name", "unknown"))
            label = f"{nm} ({score:.2f})"
        elif is_live and score >= RED_CUTOFF:
            cand = str(ann.get("best_name") or "unknown")
            label = f"{cand} ({score:.2f})"
        # merah → kosong

        if label:
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
            ytxt = max(0, y1 - 8)
            cv2.rectangle(bgr, (x1, ytxt - th - 6), (x1 + tw + 6, ytxt + 2), (0, 0, 0), -1)
            cv2.putText(bgr, label, (x1 + 3, ytxt - 2), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2, cv2.LINE_AA)

    def _process(self, frame_bgr):
        # Deteksi menggunakan resolusi native; UI boleh mengecilkan saat render.
        if not DETECTOR_READY:
            return []
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        anns = process_frame_for_faces(
            rgb,
            known_faces=KNOWN,
            match_threshold=float(CFG.get("match_threshold", 0.60)),
            require_human_check=bool(CFG.get("require_human_check", True)),
            exposure_enabled=self.exposure_enabled,
            exposure_gain=self.exposure_gain,
            min_luminance=self.min_luminance,
            antispoof_backend=str(CFG.get("antispoof_backend", "off")).lower(),
            min_live_face_size=int(CFG.get("min_live_face_size", 90)),
            min_interocular_px=int(CFG.get("min_interocular_px", 38)),
            suppress_small_faces_when_antispoof=bool(CFG.get("suppress_small_faces_when_antispoof", True)),
        )
        return anns

    def _encode_jpeg(self, img):
        # downscale if needed
        try:
            max_w = int(CFG.get("mjpeg_max_width", 960) or 0)
        except Exception:
            max_w = 0
        try:
            h, w = img.shape[:2]
        except Exception:
            return None
        if max_w > 0 and w > max_w:
            scale = max_w / float(w)
            nh, nw = int(h*scale), int(w*scale)
            try:
                img = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_AREA)
            except Exception:
                pass
        # base quality & flags
        try:
            q = int(CFG.get("mjpeg_quality", 65))
        except Exception:
            q = 65
        flags = [int(cv2.IMWRITE_JPEG_QUALITY), int(max(1, min(100, q)))]
        opt_flag = getattr(cv2, "IMWRITE_JPEG_OPTIMIZE", None)
        if opt_flag is not None and bool(CFG.get("mjpeg_optimize", True)):
            flags += [int(opt_flag), 1]
        ok, buf = cv2.imencode(".jpg", img, flags)
        if not ok:
            return None
        data = buf
        # adaptive step
        if bool(CFG.get("mjpeg_adaptive", True)):
            try:
                target = int(CFG.get("mjpeg_target_kb", 180)) * 1024
            except Exception:
                target = 180*1024
            if len(data) > target and q > 40:
                q2 = max(40, int(q - max(1, (len(data) - target) // 2048) * 5))
                ok2, buf2 = cv2.imencode(".jpg", img, [int(cv2.IMWRITE_JPEG_QUALITY), q2])
                if ok2:
                    data = buf2
        return bytes(data)

    def _loop(self):
        while not self._stop.is_set():
            cap = self._open()
            if cap is None:
                time.sleep(self.reconnect_delay); continue
            self._cap = cap
            self._frame_counter = 0
            while not self._stop.is_set():
                ok = cap.grab()
                if not ok:
                    time.sleep(0.02); continue
                for _ in range(max(0, self.frame_buffer - 1)):
                    cap.grab()
                ok, frame = cap.retrieve()
                if not ok or frame is None:
                    time.sleep(0.02); continue

                self._frame_counter += 1
                if (self._frame_counter % max(1, self.detect_interval_frames)) == 0:
                    try:
                        self._last_anns = self._process(frame)
                    except Exception:
                        logging.exception("detection failed")

                try:
                    vis = frame  # gunakan native size
                    for a in self._last_anns:
                        if a.get("skipped"):
                            continue
                        if a.get("antispoof_checked") and not a.get("antispoof_live", True):
                            continue
                        self._draw(vis, a)
                    jpg = self._encode_jpeg(vis)
                    if jpg:
                        self._last_jpeg = jpg
                except Exception:
                    logging.exception("encode jpg failed")
                time.sleep(0.005)
            try: cap.release()
            except Exception: pass
            self._cap = None

    def get_jpeg(self) -> Optional[bytes]:
        return getattr(self, "_last_jpeg", None)

    def mjpeg_generator(self):
        boundary = b"--frame"
        while not self._stop.is_set():
            jpg = self.get_jpeg()
            if jpg:
                yield boundary + b"\r\nContent-Type: image/jpeg\r\n\r\n" + jpg + b"\r\n"
            time.sleep(0.005)

# ------------ Registry ------------
WORKERS: Dict[int, CameraWorker] = {}

def ensure_worker(idx: int) -> CameraWorker:
    if idx in WORKERS:
        return WORKERS[idx]
    cams = cams_for_worker()
    if idx < 0 or idx >= len(cams):
        raise IndexError("camera index out of range")
    w = CameraWorker(idx, cams[idx])
    w.start()
    WORKERS[idx] = w
    return w

def stop_worker(idx: int):
    if idx in WORKERS:
        try: WORKERS[idx].stop()
        except Exception: pass
        WORKERS.pop(idx, None)

def stop_all_workers():
    for i in list(WORKERS.keys()):
        stop_worker(i)

# ------------ FastAPI app ------------
app = FastAPI(title="AURA API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Static mount untuk target faces
app.mount("/static/target_faces", StaticFiles(directory=TARGET_FACES), name="target_faces")

# --- import di bagian atas file ---
from routers.captures import router as captures_router

# --- setelah app = FastAPI(...) ---
app.include_router(captures_router)

# ===== Health =====
@app.get("/api/health")
def health():
    return {"ok": True}

# ===== App Config (Settings) =====
@app.get("/api/app-config")
def get_app_config():
    return read_app_config()

@app.put("/api/app-config")
def put_app_config(body: Dict[str, Any]):
    """
    Simpan patch config dan apply parameter runtime.
    """
    patch: Dict[str, Any] = {}

    if "device" in body:
        dv = str(body["device"]).strip().lower()
        patch["device"] = "GPU" if dv == "gpu" else "CPU"

    if "detector_backend" in body:
        patch["detector_backend"] = str(body["detector_backend"]).strip().lower()
    if "antispoof_backend" in body:
        ab = str(body["antispoof_backend"]).strip().lower()
        patch["antispoof_backend"] = "minifasnet" if ab in ("onnx", "minifasnet") else "off"
    if "antispoof_model_path" in body:
        patch["antispoof_model_path"] = str(body["antispoof_model_path"])

    for key in ("match_threshold", "red_cutoff_threshold"):
        if key in body:
            try: patch[key] = float(body[key])
            except Exception: pass
    if "require_human_check" in body:
        patch["require_human_check"] = bool(body["require_human_check"])
    if "box_thickness_max" in body:
        try: patch["box_thickness_max"] = int(body["box_thickness_max"])
        except Exception: pass

    if "antispoof_preprocess" in body:
        patch["antispoof_preprocess"] = str(body["antispoof_preprocess"])
    if "antispoof_live_index" in body:
        try: patch["antispoof_live_index"] = int(body["antispoof_live_index"])
        except Exception: pass
    if "antispoof_mode" in body:
        patch["antispoof_mode"] = str(body["antispoof_mode"])
    if "antispoof_smooth_k" in body:
        try: patch["antispoof_smooth_k"] = int(body["antispoof_smooth_k"])
        except Exception: pass
    if "antispoof_thresholds" in body and isinstance(body["antispoof_thresholds"], dict):
        thr = body["antispoof_thresholds"]
        out = {}
        for k in ("low", "medium", "high"):
            if k in thr:
                try: out[k] = float(thr[k])
                except Exception: pass
        if out: patch["antispoof_thresholds"] = out
    for key in ("min_live_face_size", "min_interocular_px"):
        if key in body:
            try: patch[key] = int(body[key])
            except Exception: pass
    if "suppress_small_faces_when_antispoof" in body:
        patch["suppress_small_faces_when_antispoof"] = bool(body["suppress_small_faces_when_antispoof"])

    if "log_save_mode" in body:
        patch["log_save_mode"] = "video" if str(body["log_save_mode"]).lower().startswith("video") else "photo"
    if "log_save_which" in body:
        patch["log_save_which"] = "all" if str(body["log_save_which"]).lower() == "all" else "green"
    if "log_interval_sec" in body:
        try: patch["log_interval_sec"] = int(body["log_interval_sec"])
        except Exception: pass

    if "debug" in body:
        patch["debug"] = bool(body["debug"])

    cur = read_json(APP_CONFIG_PATH, {})
    cur.update(patch)
    if not write_json(APP_CONFIG_PATH, cur):
        raise HTTPException(500, "Failed writing app_config.json")

    global CFG
    CFG.update(patch)
    # apply antispoof jika detector ready
    if DETECTOR_READY:
        try:
            live_idx = CFG.get("antispoof_live_index", 2)
            if isinstance(live_idx, int) and live_idx < 0:
                live_idx = None
            set_antispoof_params(
                live_index=live_idx,
                thresholds=CFG.get("antispoof_thresholds", {"low": 0.40, "medium": 0.55, "high": 0.70}),
                mode=CFG.get("antispoof_mode", "medium"),
                preprocess=CFG.get("antispoof_preprocess", "bgr_norm"),
                smooth_k=int(CFG.get("antispoof_smooth_k", 3)),
            )
        except Exception:
            logging.exception("set_antispoof_params failed (put)")
    return read_app_config()

# ===== Logs CSV =====
@app.get("/api/logs")
def get_logs():
    rows: List[Dict[str, Any]] = []
    if not os.path.isfile(LOG_CSV):
        return rows
    try:
        with open(LOG_CSV, "r", encoding="utf-8", newline="") as f:
            reader = csv.reader(f)
            first = next(reader, None)
            if first is None:
                return rows

            def push(r: List[str]):
                if not r:
                    return
                if len(r) >= 5:
                    date, time_s, camera, person, score_s = r[0], r[1], r[2], r[3], r[4]
                elif len(r) >= 4:
                    ts, camera, person, score_s = r[0], r[1], r[2], r[3]
                    if " " in ts:
                        date, time_s = ts.split(" ", 1)
                    else:
                        date, time_s = ts, ""
                else:
                    return
                try:
                    score = float(str(score_s).strip())
                except Exception:
                    score = 0.0
                rows.append({
                    "date": str(date).strip(),
                    "time": str(time_s).strip(),
                    "camera": str(camera).strip(),
                    "person": str(person).strip(),
                    "score": score,
                })

            header_tokens = [s.strip().lower() for s in first]
            if any(tok in ("date", "datetime", "time") for tok in header_tokens):
                for r in reader:
                    push(r)
            else:
                push(first)
                for r in reader:
                    push(r)
    except Exception:
        logging.exception("Failed reading log.csv")
        raise HTTPException(500, "Failed reading logs")
    return rows

# === helper aktif? ===
def _is_active_index(idx: int) -> bool:
    raw = read_cameras_raw()
    return 0 <= idx < len(raw) and _as_bool(raw[idx].get("active", False))

# ===== Realtime =====
@app.get("/api/realtime/cameras")
def list_cameras_rt():
    cams = cams_for_worker()
    out = []
    for i, c in enumerate(cams):
        name = c.get("name", f"Camera {i}")
        active = _is_active_index(i)
        running = bool(i in WORKERS)
        out.append({"index": i, "name": name, "active": active, "running": running})
    return out

@app.post("/api/realtime/start-all")
def start_all_rt():
    raw = read_cameras_raw()
    started = []
    for i, cam in enumerate(raw):
        if _as_bool(cam.get("active", False)):
            try:
                ensure_worker(i)
                started.append(i)
            except Exception:
                logging.exception("failed start cam %s", i)
    return {"ok": True, "started": started, "count": len(started)}

@app.get("/api/realtime/{idx}/snapshot.jpg")
def snapshot(idx: int):
    if not _is_active_index(idx):
        raise HTTPException(403, "camera is inactive")
    try:
        w = ensure_worker(idx)
    except IndexError:
        raise HTTPException(404, "camera not found")
    jpg = w.get_jpeg()
    if not jpg:
        raise HTTPException(503, "no frame yet")
    return Response(content=jpg, media_type="image/jpeg")

@app.get("/api/realtime/{idx}/stream")
def stream(idx: int):
    if not _is_active_index(idx):
        raise HTTPException(403, "camera is inactive")
    try:
        w = ensure_worker(idx)
    except IndexError:
        raise HTTPException(404, "camera not found")
    return StreamingResponse(w.mjpeg_generator(), media_type="multipart/x-mixed-replace; boundary=frame")

# ===== CCTV Management =====
class CameraCreate(BaseModel):
    id: str
    location: str
    source: Union[int, str]
    active: bool = True
    notes: Optional[str] = None

class CameraUpdate(BaseModel):
    id: Optional[str] = None
    location: Optional[str] = None
    source: Optional[Union[int, str]] = None
    active: Optional[bool] = None
    notes: Optional[str] = None

def _find_idx_by_id(raw: List[Dict[str, Any]], cam_id: str) -> int:
    for i, c in enumerate(raw):
        if str(c.get("id", c.get("name"))) == str(cam_id):
            return i
    return -1

def _row(i: int, c: Dict[str, Any]) -> Dict[str, Any]:
    running = bool(i in WORKERS)
    return {
        "id": str(c.get("id", c.get("name", f"CAM-{i+1}"))),
        "location": c.get("location", c.get("name", f"Camera {i+1}")),
        "status": "Active" if running else "Offline",
        "last": c.get("last", ""),
    }

@app.get("/api/cameras/manage")
def list_manage():
    raw = read_cameras_raw()
    return [_row(i, c) for i, c in enumerate(raw)]

@app.post("/api/cameras/manage")
def create_manage(payload: CameraCreate):
    raw = read_cameras_raw()
    if _find_idx_by_id(raw, payload.id) != -1:
        raise HTTPException(400, "Camera ID already exists")
    item = {
        "id": payload.id,
        "location": payload.location,
        "name": payload.location,
        "source": payload.source,
        "active": False,  # default dibuat mati
        "notes": payload.notes or "",
        "last": time.strftime("%Y-%m-%d %H:%M"),
    }
    raw.append(item)
    if not write_cameras_raw(raw):
        raise HTTPException(500, "Failed writing cameras.json")
    return _row(len(raw)-1, item)

@app.put("/api/cameras/manage/{cam_id}")
def update_manage(cam_id: str, payload: CameraUpdate):
    raw = read_cameras_raw()
    idx = _find_idx_by_id(raw, cam_id)
    if idx == -1:
        raise HTTPException(404, "Camera not found")
    cur = raw[idx]

    if payload.id is not None:
        if payload.id != cam_id and _find_idx_by_id(raw, payload.id) != -1:
            raise HTTPException(400, "Camera ID already exists")
        cur["id"] = payload.id
    if payload.location is not None:
        cur["location"] = payload.location
        cur["name"] = payload.location
    if payload.source is not None:
        cur["source"] = payload.source
    if payload.notes is not None:
        cur["notes"] = payload.notes

    if payload.active is not None:
        was_active = _as_bool(cur.get("active", False))
        cur["active"] = bool(payload.active)
        if was_active and not cur["active"]:
            stop_worker(idx)

    cur["last"] = time.strftime("%Y-%m-%d %H:%M")
    raw[idx] = cur
    if not write_cameras_raw(raw):
        raise HTTPException(500, "Failed writing cameras.json")
    return _row(idx, cur)

@app.delete("/api/cameras/manage/{cam_id}")
def delete_manage(cam_id: str):
    raw = read_cameras_raw()
    idx = _find_idx_by_id(raw, cam_id)
    if idx == -1:
        raise HTTPException(404, "Camera not found")
    stop_all_workers()
    del raw[idx]
    if not write_cameras_raw(raw):
        raise HTTPException(500, "Failed writing cameras.json")
    return {"ok": True}

@app.post("/api/cameras/manage/test")
def test_source(body: Dict[str, Any]):
    src = body.get("source", 0)
    try:
        cap = cv2.VideoCapture(int(src)) if (isinstance(src, str) and str(src).isdigit()) else cv2.VideoCapture(src, cv2.CAP_FFMPEG)
        ok = cap.isOpened()
        if ok: ok, _ = cap.read()
        cap.release()
        return {"ok": bool(ok)}
    except Exception:
        return {"ok": False}

@app.post("/api/cameras/manage/{cam_id}/start")
def start_cam(cam_id: str):
    raw = read_cameras_raw()
    idx = _find_idx_by_id(raw, cam_id)
    if idx == -1:
        raise HTTPException(404, "Camera not found")
    if not _as_bool(raw[idx].get("active", False)):
        raise HTTPException(403, "camera is inactive; enable it from settings first")
    try:
        ensure_worker(idx)
        return {"ok": True}
    except Exception:
        logging.exception("start worker failed")
        raise HTTPException(500, "Failed to start camera")

@app.post("/api/cameras/manage/{cam_id}/stop")
def stop_cam(cam_id: str):
    raw = read_cameras_raw()
    idx = _find_idx_by_id(raw, cam_id)
    if idx == -1:
        raise HTTPException(404, "Camera not found")
    stop_worker(idx)
    return {"ok": True}

# ===== Missing People =====
class MissingCreate(BaseModel):
    full_name: str
    target_image_url: str
    status: str = "missing"   # "missing" | "found"
    notes: Optional[str] = ""
    approval: str = "pending" # "pending" | "approved" | ...

class MissingUpdate(BaseModel):
    full_name: Optional[str] = None
    target_image_url: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    approval: Optional[str] = None

def read_missing() -> List[Dict[str, Any]]:
    data = read_json(MISSING_JSON, [])
    return data if isinstance(data, list) else []

def write_missing(data: List[Dict[str, Any]]) -> bool:
    return write_json(MISSING_JSON, data)

def _missing_find_idx(lst: List[Dict[str, Any]], _id: str) -> int:
    for i, r in enumerate(lst):
        if str(r.get("id")) == str(_id):
            return i
    return -1

@app.get("/api/missing")
def missing_list():
    return read_missing()

@app.get("/api/missing/{item_id}")
def missing_get(item_id: str):
    lst = read_missing()
    idx = _missing_find_idx(lst, item_id)
    if idx == -1:
        raise HTTPException(404, "Not found")
    return lst[idx]

@app.post("/api/missing")
def missing_create(payload: MissingCreate):
    # Rename file to match name (if possible)
    final_url = _rename_target_to_name(payload.target_image_url, payload.full_name)

    lst = read_missing()
    item = {
        "id": str(uuid.uuid4()),
        "full_name": payload.full_name.strip() or "Unknown",
        "target_image_url": final_url,
        "status": payload.status or "missing",
        "notes": payload.notes or "",
        "approval": payload.approval or "pending",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    lst.insert(0, item)
    if not write_missing(lst):
        raise HTTPException(500, "Failed writing missing_people.json")
    return item

@app.put("/api/missing/{item_id}")
def missing_update(item_id: str, payload: MissingUpdate):
    lst = read_missing()
    idx = _missing_find_idx(lst, item_id)
    if idx == -1:
        raise HTTPException(404, "Not found")
    cur = lst[idx]
    for k in ("full_name", "target_image_url", "status", "notes", "approval"):
        v = getattr(payload, k)
        if v is not None:
            cur[k] = v

    # Keep filename aligned with current full_name (safe no-op if already aligned)
    cur["target_image_url"] = _rename_target_to_name(cur.get("target_image_url", ""), cur.get("full_name", ""))

    lst[idx] = cur
    if not write_missing(lst):
        raise HTTPException(500, "Failed writing missing_people.json")
    return cur

@app.delete("/api/missing/{item_id}")
def missing_delete(item_id: str):
    lst = read_missing()
    idx = _missing_find_idx(lst, item_id)
    if idx == -1:
        raise HTTPException(404, "Not found")
    del lst[idx]
    if not write_missing(lst):
        raise HTTPException(500, "Failed writing missing_people.json")
    return {"ok": True}

# ===== Upload target face =====
@app.post("/api/targets/upload")
async def upload_target(
    file: UploadFile = File(...),
    name: Optional[str] = Form(None),
    qname: Optional[str] = Query(None),
):
    """
    Upload file ke TARGET_FACES.
    - Jika 'name' diberikan (FormData atau query), file dinamai mengikuti name (slugified).
    - Jika tidak, pakai nama file asli (slugified).
    - Tetap dijamin unik (john-doe.jpg, john-doe-1.jpg, dst).
    """
    try:
        base_name = name or qname
        # Tentukan ekstensi
        base, ext = os.path.splitext(file.filename or "")
        ext = ext.lower() if ext else ".jpg"
        if ext not in ALLOWED_EXTS:
            ext = ".jpg"
        # Tentukan base filename
        if not base_name:
            base_name = base or "image"
        base_name = _slugify_name(base_name)
        fname, out_path = _unique_filename(base_name, ext)

        with open(out_path, "wb") as f:
            f.write(await file.read())
        url = f"/static/target_faces/{fname}"
        return {"url": url, "path": out_path}
    except Exception:
        logging.exception("Upload failed")
        raise HTTPException(500, "Upload failed")

# ======== DASHBOARD SUMMARY (sinkron dengan page Cameras) ========
def _count_logs_today() -> int:
    """
    Hitung jumlah baris log CSV untuk tanggal hari ini (YYYY-MM-DD).
    """
    if not os.path.isfile(LOG_CSV):
        return 0
    today = time.strftime("%Y-%m-%d")
    count = 0
    try:
        with open(LOG_CSV, "r", encoding="utf-8", newline="") as f:
            reader = csv.reader(f)
            first = next(reader, None)
            if first is None:
                return 0

            header_tokens = [s.strip().lower() for s in first]
            has_header = any(tok in ("date", "datetime", "time") for tok in header_tokens)

            def is_today_row(cols: List[str]) -> bool:
                if not cols:
                    return False
                if len(cols) >= 5:
                    date = str(cols[0]).strip()
                    return date.startswith(today)
                elif len(cols) >= 4:
                    ts = str(cols[0]).strip()
                    return ts.startswith(today)
                return False

            if has_header:
                for r in reader:
                    if is_today_row(r):
                        count += 1
            else:
                if is_today_row(first):
                    count += 1
                for r in reader:
                    if is_today_row(r):
                        count += 1
    except Exception:
        logging.exception("Failed counting today's logs")
        return 0
    return count

@app.get("/api/dashboard-summary")
def dashboard_summary():
    """
    Ringkasan angka untuk Dashboard.jsx:
    - missingNotFound & missingFounded → dari missing_people.json
    - activeCameras → JUMLAH baris dengan status 'Active' dari /api/cameras/manage (sinkron dgn page Cameras)
    - totalCameras → jumlah kamera terdaftar (panjang cameras.json)
    - detectionsToday → hitung dari logs/log.csv (baris bertanggal hari ini)
    - possibleMatches → sementara = detectionsToday
    - confirmedMissing → jumlah missing dengan approval == 'approved'
    """
    # total dari file (tetap)
    cams_raw = read_cameras_raw()
    total_cams = len(cams_raw)

    # sinkron dgn page Cameras: gunakan status dari list_manage()
    try:
        manage_rows = list_manage()
        active_cams = sum(1 for r in manage_rows if str(r.get("status", "")).lower() == "active")
    except Exception:
        # fallback aman
        active_cams = 0

    # Missing
    missing = read_missing()
    missing_not_found = 0
    missing_founded = 0
    confirmed_approved = 0
    for row in missing:
        status = str(row.get("status", "missing")).lower()
        approval = str(row.get("approval", "pending")).lower()
        if status == "found":
            missing_founded += 1
        else:
            missing_not_found += 1
        if approval == "approved":
            confirmed_approved += 1

    # Logs
    det_today = _count_logs_today()

    return {
        "missingNotFound": missing_not_found,
        "missingFounded": missing_founded,
        "activeCameras": active_cams,
        "totalCameras": total_cams,
        "detectionsToday": det_today,
        "possibleMatches": det_today,   # sementara sama
        "confirmedMissing": confirmed_approved,
    }
