# gui.py (rev2d: accept "mati semua"/none/off; fix minor indentation from prev; tracker unchanged)
import os
import time
import json
import math
import logging
import threading
import numpy as np
from concurrent.futures import ThreadPoolExecutor

from PyQt5.QtWidgets import QLabel, QWidget, QVBoxLayout, QSizePolicy, QHBoxLayout
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import QThread, pyqtSignal, Qt
import cv2

from detector import load_known_faces, process_frame_for_faces
from logger import log_detection

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CAMERAS_CONFIG = os.path.join(BASE_DIR, "cameras.json")
APP_CONFIG = os.path.join(BASE_DIR, "app_config.json")

CPU_COUNT = os.cpu_count() or 2
GLOBAL_FACE_WORKER_POOL = ThreadPoolExecutor(max_workers=max(1, CPU_COUNT - 1))


def read_cameras_config(path=CAMERAS_CONFIG):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logging.error("Failed to read cameras.json: %s", e)
        return []


def write_cameras_config(data, path=CAMERAS_CONFIG):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        logging.exception("Failed to write cameras.json")
        return False


def read_app_config(path=APP_CONFIG):
    cfg = {
        "device": "CPU",
        "debug": False,
        "detector_backend": "insightface",
        "antispoof_backend": "off",  # "off/none/mati" = mati semua
        "antispoof_model_path": "",
        "save_mode": "photo",
        "log_interval_seconds": 0,
        "match_threshold": 0.6,
        "red_cutoff_threshold": 0.4,
        "preview_width": 640,
        "preview_height": 480,
        "require_human_check": True,
        "box_thickness_max": 6,
        "save_which": "green",

        "antispoof_preprocess": "bgr_norm",
        "antispoof_live_index": 2,
        "antispoof_mode": "medium",
        "antispoof_thresholds": {"low": 0.40, "medium": 0.55, "high": 0.70},
        "antispoof_smooth_k": 3,
        "min_live_face_size": 90,
        "min_interocular_px": 38,
        "suppress_small_faces_when_antispoof": True,
    }
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                cfg.update(json.load(f))
    except Exception:
        logging.exception("Failed reading app_config.json")
    return cfg


class ClickableLabel(QLabel):
    double_clicked = pyqtSignal()
    def mouseDoubleClickEvent(self, event):
        try:
            self.double_clicked.emit()
        except Exception:
            pass
        super().mouseDoubleClickEvent(event)


def _iou(a, b):
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    iw, ih = max(0, ix2 - ix1), max(0, iy2 - iy1)
    inter = iw * ih
    if inter <= 0: return 0.0
    area_a = max(1, (ax2 - ax1) * (ay2 - ay1))
    area_b = max(1, (bx2 - bx1) * (by2 - by1))
    return float(inter) / float(area_a + area_b - inter)


# ---------- Simple face tracker (Lucas–Kanade optical flow + scale) ----------
class _LKTrack:
    __slots__ = ("bbox", "pts", "lost", "last_update_ts")
    def __init__(self, bbox, pts, ts):
        self.bbox = list(map(float, bbox))
        self.pts = pts  # Nx1x2 float32
        self.lost = 0
        self.last_update_ts = ts


class SimpleLKTracker:
    def __init__(self):
        self.tracks = []      # list[_LKTrack]
        self.prev_gray = None
        self._anns = []       # annotations diselaraskan
        self._version = 0

    def _gftt(self, gray, bbox, max_pts=60):
        x1, y1, x2, y2 = [int(round(v)) for v in bbox]
        x1 = max(0, min(gray.shape[1]-2, x1)); x2 = max(1, min(gray.shape[1]-1, x2))
        y1 = max(0, min(gray.shape[0]-2, y1)); y2 = max(1, min(gray.shape[0]-1, y2))
        if x2 <= x1 or y2 <= y1:
            return None
        roi = gray[y1:y2, x1:x2]
        if roi.size < 400:
            return None
        pts = cv2.goodFeaturesToTrack(
            roi, maxCorners=max_pts, qualityLevel=0.01, minDistance=3, blockSize=3
        )
        if pts is None:
            return None
        pts = pts.astype(np.float32)
        pts[:, 0, 0] += x1
        pts[:, 0, 1] += y1
        return pts

    def set_detections(self, annotations, gray, ts=None):
        new_tracks = []
        now = ts if ts is not None else time.time()

        for ann in annotations:
            if ann.get("skipped"):
                continue
            bb = ann["bbox"]
            best_iou, best_idx = 0.0, -1
            for i, old in enumerate(self.tracks):
                iou = _iou((int(old.bbox[0]), int(old.bbox[1]), int(old.bbox[2]), int(old.bbox[3])), bb)
                if iou > best_iou:
                    best_iou, best_idx = iou, i
            pts = self._gftt(gray, bb)
            if pts is None or len(pts) < 6:
                continue
            tr = _LKTrack(bb, pts, now)
            if best_idx >= 0 and best_iou >= 0.2:
                oldb = self.tracks[best_idx].bbox
                ax = 0.4
                tr.bbox = [
                    ax*oldb[0] + (1-ax)*bb[0],
                    ax*oldb[1] + (1-ax)*bb[1],
                    ax*oldb[2] + (1-ax)*bb[2],
                    ax*oldb[3] + (1-ax)*bb[3],
                ]
            new_tracks.append(tr)

        self.tracks = new_tracks
        self._anns = [dict(a) for a in annotations]
        self.prev_gray = gray.copy()
        self._version += 1

    def track(self, gray, ts=None):
        if self.prev_gray is None or not self.tracks:
            self.prev_gray = gray.copy()
            return
        now = ts if ts is not None else time.time()

        all_old = []
        tr_idx = []
        for i, tr in enumerate(self.tracks):
            if tr.pts is None or len(tr.pts) < 4:
                tr.lost += 1
                continue
            all_old.append(tr.pts)
            tr_idx.append(i)
        if not all_old:
            self.prev_gray = gray.copy()
            return

        old = np.vstack(all_old)
        new, st, err = cv2.calcOpticalFlowPyrLK(self.prev_gray, gray, old, None, winSize=(17, 17), maxLevel=3)
        if new is None or st is None:
            self.prev_gray = gray.copy()
            return

        off = 0
        H, W = gray.shape[:2]
        for idx in tr_idx:
            tr = self.tracks[idx]
            n = len(tr.pts)
            pts_old = old[off:off+n]; pts_new = new[off:off+n]; st_sub = st[off:off+n]
            off += n
            good = st_sub.reshape(-1) > 0
            if not np.any(good):
                tr.lost += 1
                continue

            disp = (pts_new[good, 0, :] - pts_old[good, 0, :])
            dx = float(np.median(disp[:, 0])); dy = float(np.median(disp[:, 1]))

            try:
                a = pts_old[good, 0, :]
                b = pts_new[good, 0, :]
                if len(a) >= 10:
                    idxs = np.random.choice(len(a), size=min(20, len(a)), replace=False)
                    ra = a[idxs]; rb = b[idxs]
                    ca = np.median(ra, axis=0); cb = np.median(rb, axis=0)
                    da = np.median(np.linalg.norm(ra - ca, axis=1)) + 1e-6
                    db = np.median(np.linalg.norm(rb - cb, axis=1)) + 1e-6
                    s = float(db / da)
                else:
                    s = 1.0
            except Exception:
                s = 1.0
            s = float(np.clip(s, 0.85, 1.20))

            x1, y1, x2, y2 = tr.bbox
            cx = 0.5*(x1 + x2) + dx
            cy = 0.5*(y1 + y2) + dy
            w = (x2 - x1) * s
            h = (y2 - y1) * s
            ar = w / (h + 1e-6)
            if ar < 0.6: w = h * 0.6
            if ar > 1.9: h = w / 1.9
            x1 = cx - 0.5*w; y1 = cy - 0.5*h; x2 = cx + 0.5*w; y2 = cy + 0.5*h

            x1 = max(0.0, min(W - 2.0, x1)); x2 = max(1.0, min(W - 1.0, x2))
            y1 = max(0.0, min(H - 2.0, y1)); y2 = max(1.0, min(H - 1.0, y2))
            tr.bbox = [x1, y1, x2, y2]

            tr.pts = pts_new[good]
            if len(tr.pts) < 10 or (now - tr.last_update_ts) > 0.6:
                new_pts = self._gftt(gray, tr.bbox)
                if new_pts is not None and len(new_pts) >= 6:
                    tr.pts = new_pts
                    tr.last_update_ts = now
            tr.lost = 0

        ai = 0
        for tr in self.tracks:
            while ai < len(self._anns) and self._anns[ai].get("skipped", False):
                ai += 1
            if ai >= len(self._anns):
                break
            self._anns[ai]["bbox"] = (int(round(tr.bbox[0])), int(round(tr.bbox[1])),
                                      int(round(tr.bbox[2])), int(round(tr.bbox[3])))
            ai += 1

        self.tracks = [t for t in self.tracks if t.lost <= 5]
        self.prev_gray = gray.copy()

    def annotations(self):
        return [dict(a) for a in self._anns]

    def has_tracks(self):
        return len(self.tracks) > 0


class RTSPCamera:
    def __init__(self, source, reconnect_delay=5, backend=cv2.CAP_FFMPEG, frame_buffer=1):
        self.source = source
        self.reconnect_delay = int(reconnect_delay)
        self.backend = backend
        self.frame_buffer = max(1, int(frame_buffer))
        self.capture = None
        self.frame = None
        self.lock = threading.Lock()
        self._stop = threading.Event()
        self._thread = None
        self.running = False

        self._metrics_lock = threading.Lock()
        self._ema_iat = None
        self._last_ts = None
        self._attempts = 0
        self._oks = 0
        self._win_start = time.time()
        self._latency_ms = 0.0
        self._drop_pct = 0.0

        self.ema_half_life_s = 0.8

    def start(self):
        if self.running:
            return
        self.running = True
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        logging.info(f"[RTSPCamera] started {self.source}")

    def _open(self):
        try:
            if isinstance(self.source, (int, str)) and str(self.source).isdigit():
                cap = cv2.VideoCapture(int(self.source))
            else:
                cap = cv2.VideoCapture(self.source, self.backend)
            try:
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            except Exception:
                pass
            if not cap.isOpened():
                try:
                    cap.release()
                except Exception:
                    pass
                return None
            return cap
        except Exception:
            return None

    def _loop(self):
        while not self._stop.is_set():
            cap = self._open()
            if cap is None:
                time.sleep(self.reconnect_delay)
                continue
            self.capture = cap
            while not self._stop.is_set():
                try:
                    self._attempts += 1
                    ok = cap.grab()
                    if not ok:
                        time.sleep(0.02)
                        continue
                    for _ in range(self.frame_buffer - 1):
                        cap.grab()
                    ret, frame = cap.retrieve()
                    if not ret or frame is None:
                        time.sleep(0.02)
                        continue

                    self._oks += 1
                    now = time.time()
                    if self._last_ts is not None:
                        iat = max(1e-3, now - self._last_ts)
                        if self._ema_iat is None:
                            self._ema_iat = iat
                        else:
                            tau = self.ema_half_life_s / math.log(2.0)
                            alpha = 1.0 - math.exp(-iat / max(1e-6, tau))
                            self._ema_iat = (1.0 - alpha) * self._ema_iat + alpha * iat
                    self._last_ts = now

                    with self.lock:
                        self.frame = frame

                    self._update_metrics_window(now)
                except Exception:
                    break

            try:
                cap.release()
            except Exception:
                pass
            self.capture = None
            if not self._stop.is_set():
                time.sleep(self.reconnect_delay)
        self.running = False

    def _update_metrics_window(self, now_ts: float):
        if (now_ts - self._win_start) >= 1.0:
            at, ok = self._attempts, self._oks
            drop = (float(at - ok) / float(at) * 100.0) if at > 0 else 100.0
            lat_ms = float(self._ema_iat * 1000.0) if self._ema_iat is not None else 0.0
            with self._metrics_lock:
                self._latency_ms = max(0.0, lat_ms)
                self._drop_pct = max(0.0, min(100.0, drop))
            self._attempts = 0
            self._oks = 0
            self._win_start = now_ts

    def get_metrics(self):
        with self._metrics_lock:
            return float(self._latency_ms), float(self._drop_pct)

    def get_frame(self):
        with self.lock:
            return None if self.frame is None else self.frame.copy()

    def stop(self):
        self._stop.set()
        try:
            if self._thread and self._thread.is_alive():
                self._thread.join(timeout=1.0)
        except Exception:
            pass
        try:
            if self.capture:
                self.capture.release()
        except Exception:
            pass
        self.running = False


class CameraThread(QThread):
    frame_ready = pyqtSignal(QImage)
    status_update = pyqtSignal(str)

    def __init__(
        self, camera_name, source, known_faces, display_interval_ms=50, detect_interval_frames=3,
        reconnect_delay=10, frame_buffer=1, exposure_enabled=True, exposure_gain=1.4, min_luminance=60.0
    ):
        super().__init__()
        self.camera_name = camera_name
        self.source = source
        self.display_interval_ms = max(1, int(display_interval_ms))
        self.detect_interval_frames = max(1, int(detect_interval_frames))
        self.reconnect_delay = int(reconnect_delay)
        self.frame_buffer = max(1, int(frame_buffer))

        cfg = read_app_config()
        self.match_threshold = float(cfg.get("match_threshold", 0.6))
        self.require_human_check = bool(cfg.get("require_human_check", True))
        self.box_thick_max = int(cfg.get("box_thickness_max", 6))
        self.save_mode = str(cfg.get("save_mode", "photo")).strip().lower()
        self.save_which = str(cfg.get("save_which", "green")).strip().lower()
        self.red_cutoff = float(cfg.get("red_cutoff_threshold", 0.4))
        self.antispoof_backend = str(cfg.get("antispoof_backend", "off")).strip().lower()
        # terima semua alias "mati semua"
        if self.antispoof_backend in {"none","disabled","disable","mati","mati_semua","no","false","0"}:
            self.antispoof_backend = "off"

        self.min_live_face_size = int(cfg.get("min_live_face_size", 90))
        self.min_interocular_px = float(cfg.get("min_interocular_px", 38))
        self.suppress_small_faces_when_antispoof = bool(cfg.get("suppress_small_faces_when_antispoof", True))

        self.exposure_enabled = bool(exposure_enabled)
        self.exposure_gain = float(exposure_gain)
        self.min_luminance = float(min_luminance)

        self.known_faces = known_faces or []
        self._stop_requested = False
        self._frame_counter = 0
        self.camera = RTSPCamera(source, reconnect_delay=self.reconnect_delay, frame_buffer=self.frame_buffer)
        self.camera.start()

        self.annotations_lock = threading.Lock()
        self.last_annotations = []
        self._ann_version = 0
        self._tracker_sync_version = -1

        self.log_interval_seconds = int(cfg.get("log_interval_seconds", 0))
        self._last_log_ts = 0.0

        self._last_native_bgr = None
        self._last_native_lock = threading.Lock()

        self._detect_busy = False

        self._tracker = SimpleLKTracker()

    def reload_known_faces(self):
        self.known_faces = load_known_faces()

    def submit_detection(self, native_rgb):
        if self._detect_busy:
            return False
        self._detect_busy = True

        future = GLOBAL_FACE_WORKER_POOL.submit(
            process_frame_for_faces,
            native_rgb,
            self.known_faces,
            self.match_threshold,
            self.require_human_check,
            self.exposure_enabled,
            self.exposure_gain,
            self.min_luminance,
            self.antispoof_backend,
            self.min_live_face_size,
            self.min_interocular_px,
            self.suppress_small_faces_when_antispoof,
        )

        def cb(fut):
            try:
                try:
                    annotations = fut.result()
                except Exception:
                    logging.exception("detector worker failed")
                    annotations = []
                with self.annotations_lock:
                    self.last_annotations = annotations
                    self._ann_version += 1
                try:
                    self._maybe_log_and_save(annotations)
                except Exception:
                    logging.exception("_maybe_log_and_save failed")
            finally:
                self._detect_busy = False

        future.add_done_callback(cb)
        return True

    def _draw_annotations(self, frame_bgr, annotations):
        for ann in annotations:
            try:
                if ann.get("skipped"):
                    continue
                if ann.get("antispoof_checked") and not ann.get("antispoof_live", True):
                    continue
                x1, y1, x2, y2 = ann["bbox"]
                is_live = ann.get("antispoof_live", True)
                sc = float(ann.get("score", 0.0))
                matched = bool(ann.get("match"))

                if matched and is_live:
                    color = (0, 255, 0)
                    label = f"{ann.get('name', 'unknown')} ({sc:.2f})"
                else:
                    if sc >= self.red_cutoff:
                        color = (0, 165, 255)  # orange
                        cand = ann.get("best_name") or "unknown"
                        label = f"{cand} ({sc:.2f})"
                    else:
                        color = (0, 0, 255)  # red
                        label = ""

                bw = max(1, int(x2) - int(x1))
                bh = max(1, int(y2) - int(y1))
                _max_side = max(bw, bh)
                _th = max(2, min(self.box_thick_max, int(150 / max(1, _max_side)) + 2))
                cv2.rectangle(frame_bgr, (int(x1), int(y1)), (int(x2), int(y2)), color, _th)
                if label:
                    cv2.putText(
                        frame_bgr,
                        label,
                        (int(x1), max(15, int(y1) - 5)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        color,
                        2,
                    )
            except Exception:
                continue
        return frame_bgr

    def _maybe_log_and_save(self, annotations):
        now = time.time()
        do_log = (self.log_interval_seconds <= 0) or ((now - self._last_log_ts) >= self.log_interval_seconds)
        chosen = None

        for ann in annotations:
            if ann.get("skipped"):
                continue
            if ann.get("antispoof_checked") and not ann.get("antispoof_live", True):
                continue
            is_live = ann.get("antispoof_live", True)
            sc = float(ann.get("score", 0.0))
            matched = bool(ann.get("match"))
            qualifies_green = matched and is_live
            qualifies_orange = (not matched) and (sc >= self.red_cutoff) and is_live

            if self.save_which == "green_orange":
                if qualifies_green or qualifies_orange:
                    chosen = ann; break
            else:
                if qualifies_green:
                    chosen = ann; break

        if do_log and annotations:
            try:
                match_ann = None
                for ann in annotations:
                    if ann.get("skipped"):
                        continue
                    if ann.get("antispoof_checked") and not ann.get("antispoof_live", True):
                        continue
                    if ann.get("match"):
                        match_ann = ann; break
                if match_ann is not None:
                    log_detection(self.camera_name, match_ann.get("name", "unknown"), float(match_ann.get("score", 0.0)))
                    self._last_log_ts = now
            except Exception:
                logging.exception("Failed to write detection log")

        if chosen is None:
            return

        name = chosen.get("name") if chosen.get("match") else (chosen.get("best_name") or "unknown")
        safe_name = str(name).strip().replace(os.sep, "_")
        out_dir = os.path.join(BASE_DIR, "captures", safe_name)
        try: os.makedirs(out_dir, exist_ok=True)
        except Exception: pass

        with self._last_native_lock:
            frame_bgr = None if self._last_native_bgr is None else self._last_native_bgr.copy()
        if frame_bgr is None:
            return

        try:
            x1, y1, x2, y2 = chosen["bbox"]
            color = (0, 255, 0) if chosen.get("match") else (0, 165, 255)
            sc = float(chosen.get("score", 0.0))
            label = f"{name} ({sc:.2f})"
            bw = max(1, int(x2) - int(x1))
            bh = max(1, int(y2) - int(y1))
            _max_side = max(bw, bh)
            _th = max(2, min(self.box_thick_max, int(150 / max(1, _max_side)) + 2))
            cv2.rectangle(frame_bgr, (int(x1), int(y1)), (int(x2), int(y2)), color, _th)
            if label:
                cv2.putText(
                    frame_bgr,
                    label,
                    (int(x1), max(15, int(y1) - 5)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    color,
                    2,
                )
        except Exception:
            pass

        ts = time.strftime("%Y%m%d_%H%M%S")
        if self.save_mode == "photo":
            out = os.path.join(out_dir, f"{ts}.jpg")
            try: cv2.imwrite(out, frame_bgr)
            except Exception: pass
        else:
            end_ts = time.time() + 3.0
            h, w = frame_bgr.shape[:2]
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            out = os.path.join(out_dir, f"{ts}.mp4")
            try:
                vw = cv2.VideoWriter(out, fourcc, 20.0, (w, h))
                while time.time() < end_ts:
                    with self._last_native_lock:
                        fr = None if self._last_native_bgr is None else self._last_native_bgr.copy()
                    if fr is None: break
                    vw.write(fr)
                    time.sleep(0.045)
                vw.release()
            except Exception:
                try: vw.release()
                except Exception: pass

    def run(self):
        logging.info(f"[{self.camera_name}] CameraThread started")
        while not self._stop_requested:
            frame_bgr_native = self.camera.get_frame()
            if frame_bgr_native is None:
                try: self.status_update.emit("reconnecting")
                except Exception: pass
                time.sleep(0.2); continue
            else:
                try: self.status_update.emit("running")
                except Exception: pass

            self._frame_counter += 1

            if (self._frame_counter % self.detect_interval_frames) == 0:
                try:
                    native_rgb = cv2.cvtColor(frame_bgr_native, cv2.COLOR_BGR2RGB)
                    self.submit_detection(native_rgb)
                except Exception:
                    logging.exception("submit detection failed")

            try:
                with self._last_native_lock:
                    self._last_native_bgr = frame_bgr_native.copy()
            except Exception:
                pass

            try:
                gray = cv2.cvtColor(frame_bgr_native, cv2.COLOR_BGR2GRAY)
            except Exception:
                gray = None

            if gray is not None:
                if self._tracker_sync_version != self._ann_version:
                    with self.annotations_lock:
                        anns = [dict(a) for a in self.last_annotations]
                    self._tracker.set_detections(anns, gray)
                    self._tracker_sync_version = self._ann_version
                else:
                    self._tracker.track(gray)

            try:
                if self._tracker.has_tracks():
                    annotations = self._tracker.annotations()
                else:
                    with self.annotations_lock:
                        annotations = [dict(a) for a in self.last_annotations]
            except Exception:
                with self.annotations_lock:
                    annotations = [dict(a) for a in self.last_annotations]

            try:
                preview_bgr = frame_bgr_native.copy()
                preview_bgr = self._draw_annotations(preview_bgr, annotations)
                rgb_out = cv2.cvtColor(preview_bgr, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb_out.shape
                bytes_per_line = ch * w
                qimg = QImage(rgb_out.data, w, h, bytes_per_line, QImage.Format_RGB888).copy()
                self.frame_ready.emit(qimg)
            except Exception:
                logging.exception("QImage conversion failed")

            time.sleep(self.display_interval_ms / 1000.0)

        try: self.camera.stop()
        except Exception: pass
        logging.info(f"[{self.camera_name}] CameraThread stopped")

    def stop(self):
        self._stop_requested = True
        try:
            self.wait(2000)
        except Exception:
            pass
        try:
            self.camera.stop()
        except Exception:
            pass


class CameraWidget(QWidget):
    full_toggle_requested = pyqtSignal(object)

    def __init__(self, camera_config):
        super().__init__()
        self.config = camera_config.copy()
        self.name = self.config.get("name", "Camera")
        self.source = self.config.get("source", 0)
        self.display_interval_ms = int(self.config.get("display_interval_ms", 50))
        self.detect_interval_frames = int(self.config.get("detect_interval_frames", 3))
        self.reconnect_delay = int(self.config.get("reconnect_delay", 10))
        self.frame_buffer = int(self.config.get("frame_buffer", 1))
        self.exposure_enabled = bool(self.config.get("exposure_enabled", True))
        self.exposure_gain = float(self.config.get("exposure_gain", 1.4))
        self.min_luminance = float(self.config.get("min_luminance", 60.0))

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        self.setLayout(layout)

        self.preview = ClickableLabel(f"{self.name}")
        self.preview.setAlignment(Qt.AlignCenter)
        self._last_qimage = None
        self.preview.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.preview.setMinimumSize(160, 120)
        layout.addWidget(self.preview)
        try:
            self.preview.double_clicked.connect(lambda: self.full_toggle_requested.emit(self))
        except Exception:
            pass

        self.status = QLabel(f"{self.name} : reconnecting - 0.0 FPS")
        self.net_dot = QLabel()
        self.net_dot.setFixedSize(15, 15)
        self.net_dot.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self._apply_dot_style("#e74c3c")
        self.net_dot.setToolTip("latency: -- ms | drop: --%")
        stat_row = QHBoxLayout()
        stat_row.setContentsMargins(6, 0, 6, 6)
        stat_row.setSpacing(6)
        stat_row.addWidget(self.net_dot)
        stat_row.addWidget(self.status, 1)
        layout.addLayout(stat_row)

        self._last_status = "reconnecting"
        self._fps = 0.0
        self._fps_cnt = 0
        self._fps_t0 = time.time()

        self.known_faces = load_known_faces()

        self.thread = CameraThread(
            self.name,
            self.source,
            self.known_faces,
            display_interval_ms=self.display_interval_ms,
            detect_interval_frames=self.detect_interval_frames,
            reconnect_delay=self.reconnect_delay,
            frame_buffer=self.frame_buffer,
            exposure_enabled=self.exposure_enabled,
            exposure_gain=self.exposure_gain,
            min_luminance=self.min_luminance,
        )
        self.thread.frame_ready.connect(self.on_frame)
        self.thread.status_update.connect(self.on_status)
        try:
            self.thread.fps_update.connect(self.on_fps)  # optional if exists
        except Exception:
            pass
        self.thread.start()

    def on_frame(self, qimg):
        self._last_qimage = qimg
        sz = self.preview.size()
        try:
            pix = QPixmap.fromImage(qimg)
            if sz.width() > 0 and sz.height() > 0:
                pix = pix.scaled(sz, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.preview.setPixmap(pix)
        except Exception:
            self.preview.setPixmap(QPixmap.fromImage(qimg))
        try:
            self._fps_cnt += 1
            now = time.time()
            if now - self._fps_t0 >= 1.0:
                self._fps = self._fps_cnt / (now - self._fps_t0)
                self._fps_cnt = 0
                self._fps_t0 = now
                self.status.setText(f"{self.name} : {self._last_status} - {self._fps:.1f} FPS")
                self._refresh_indicator()
        except Exception:
            pass

    def on_fps(self, fps):
        try:
            self._fps = float(fps)
            self.status.setText(f"{self.name} : {self._last_status} - {self._fps:.1f} FPS")
        except Exception:
            pass
        try:
            self._refresh_indicator(force_red_if_reconnecting=(self._last_status == "reconnecting"))
        except Exception:
            pass

    def on_status(self, text):
        self._last_status = str(text)
        try:
            self.status.setText(f"{self.name} : {self._last_status} - {self._fps:.1f} FPS")
        except Exception:
            pass

    def resizeEvent(self, event):
        try:
            if self._last_qimage is not None:
                sz = self.preview.size()
                pix = QPixmap.fromImage(self._last_qimage)
                if sz.width() > 0 and sz.height() > 0:
                    pix = pix.scaled(sz, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.preview.setPixmap(pix)
        except Exception:
            pass
        super().resizeEvent(event)

    def stop(self):
        try:
            self.thread.stop()
        except Exception:
            pass

    def _apply_dot_style(self, color_hex: str):
        self.net_dot.setStyleSheet(
            f"background-color: {color_hex}; border-radius: 5px; border: 1px solid rgba(0,0,0,0.25);"
        )

    def _refresh_indicator(self, force_red_if_reconnecting: bool = False):
        lat_ms, drop = self.thread.camera.get_metrics()
        if force_red_if_reconnecting:
            color = "#e74c3c"
        else:
            if (lat_ms < 120.0 and drop < 5.0):
                color = "#21ba45"
            elif (lat_ms > 300.0) or (drop > 15.0):
                color = "#e74c3c"
            else:
                color = "#f2994a"
        self._apply_dot_style(color)
        self.net_dot.setToolTip(f"latency: {int(round(lat_ms))} ms | drop: {drop:.1f}%")
