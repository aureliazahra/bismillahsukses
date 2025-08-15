# gui.py
"""
GUI pipeline: responsive display + async detection + antispoof pool.
Revisions:
- Fix blur false positives by checking variance (Laplacian) on face crops (when bbox available).
- Keep full-frame sharpness percent check for initial conditions.
- Adaptive backoff preserved.
- Respect show_skipped_blur and BLUR-SKIP indicator.
- Does not change existing bounding-box color logic.
"""

import os
import time
import json
import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from PyQt5.QtWidgets import QLabel, QWidget, QVBoxLayout
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import QThread, pyqtSignal, Qt
import cv2

from detector import (
    load_known_faces, process_frame_for_faces,
    load_antispoof_model, apply_exposure_correction, antispoof_crop_predict,
    compute_sharpness
)
from logger import log_detection

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CAMERAS_CONFIG = os.path.join(BASE_DIR, "cameras.json")
APP_CONFIG = os.path.join(BASE_DIR, "app_config.json")

CPU_COUNT = os.cpu_count() or 2
GLOBAL_FACE_WORKER_POOL = ThreadPoolExecutor(max_workers=max(1, CPU_COUNT - 1))
ANTI_SPOOF_POOL = ThreadPoolExecutor(max_workers=1)

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
    cfg = {"device": "CPU", "debug": False}
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
    except Exception:
        logging.exception("Failed reading app_config.json")
    return cfg

def write_app_config(cfg, path=APP_CONFIG):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        logging.exception("Failed writing app_config.json")
        return False

class RTSPCamera:
    def __init__(self, source, width=320, height=240, reconnect_delay=5, backend=cv2.CAP_FFMPEG, frame_buffer=1):
        self.source = source
        self.width = int(width)
        self.height = int(height)
        self.reconnect_delay = int(reconnect_delay)
        self.backend = backend
        self.frame_buffer = max(1, int(frame_buffer))
        self.capture = None
        self.frame = None
        self.lock = threading.Lock()
        self._stop = threading.Event()
        self._thread = None
        self.running = False

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
            if isinstance(self.source, (int,str)) and str(self.source).isdigit():
                cap = cv2.VideoCapture(int(self.source))
            else:
                cap = cv2.VideoCapture(self.source, self.backend)
            try:
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
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
                logging.warning(f"[RTSPCamera] cannot open {self.source}, retry {self.reconnect_delay}s")
                time.sleep(self.reconnect_delay)
                continue
            self.capture = cap
            bad = 0
            while not self._stop.is_set():
                try:
                    ok = cap.grab()
                    if not ok:
                        bad += 1
                    else:
                        for _ in range(self.frame_buffer - 1):
                            cap.grab()
                        ret, frame = cap.retrieve()
                        if not ret or frame is None:
                            bad += 1
                        else:
                            bad = 0
                            if frame.shape[1] != self.width or frame.shape[0] != self.height:
                                frame = cv2.resize(frame, (self.width, self.height))
                            with self.lock:
                                self.frame = frame
                    if bad > 10:
                        logging.warning(f"[RTSPCamera] many failed reads {self.source}")
                        break
                except Exception:
                    logging.exception(f"[RTSPCamera] error {self.source}")
                    break
                time.sleep(0.002)
            try:
                cap.release()
            except Exception:
                pass
            self.capture = None
            if not self._stop.is_set():
                time.sleep(self.reconnect_delay)
        self.running = False
        logging.info(f"[RTSPCamera] stopped {self.source}")

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

    def __init__(self, camera_name, source, known_faces,
                 width=320, height=240, display_interval_ms=50, detect_interval_frames=4,
                 reconnect_delay=5, backend=cv2.CAP_FFMPEG, match_threshold=0.5,
                 min_sharpness_percent=20, sharpness_var_max=1000, min_sharpness_var=None,
                 require_human_check=False, exposure_enabled=True, exposure_gain=1.4,
                 min_luminance=60, frame_buffer=1,
                 antispoof_enabled=False, antispoof_interval=15, antispoof_model_path="", antispoof_threshold=0.5,
                 show_skipped_blur=False, blur_backoff_trigger=3, blur_backoff_frames=5):
        super().__init__()
        self.camera_name = camera_name
        self.source = source
        self.width = int(width)
        self.height = int(height)
        self.display_interval_ms = max(1, int(display_interval_ms))
        self.detect_interval_frames = max(1, int(detect_interval_frames))
        self.reconnect_delay = int(reconnect_delay)
        self.backend = backend
        self.match_threshold = float(match_threshold)

        # settings
        # keep the old percent-based value for full-frame checks
        self.min_sharpness_percent = float(min_sharpness_percent)
        # max variance used for percent normalisation
        self.sharpness_var_max = float(sharpness_var_max)
        # optionally supplied: absolute variance threshold for crop checks
        self.min_sharpness_var = None
        if min_sharpness_var is not None:
            try:
                self.min_sharpness_var = float(min_sharpness_var)
            except Exception:
                self.min_sharpness_var = None

        self.require_human_check = bool(require_human_check)
        self.exposure_enabled = bool(exposure_enabled)
        self.exposure_gain = float(exposure_gain)
        self.min_luminance = float(min_luminance)
        self.frame_buffer = max(1, int(frame_buffer))

        # antispoof
        self.antispoof_enabled = bool(antispoof_enabled)
        self.antispoof_interval = max(1, int(antispoof_interval))
        self.antispoof_model_path = str(antispoof_model_path)
        self.antispoof_threshold = float(antispoof_threshold)

        self.known_faces = known_faces or []
        self._stop_requested = False
        self._frame_counter = 0
        self.camera = RTSPCamera(source, width=self.width, height=self.height,
                                 reconnect_delay=self.reconnect_delay, backend=self.backend,
                                 frame_buffer=self.frame_buffer)

        if self.antispoof_enabled and self.antispoof_model_path:
            try:
                load_antispoof_model(self.antispoof_model_path)
            except Exception:
                logging.exception("Failed to load antispoof model")

        self.last_annotations = []
        self.annotations_lock = threading.Lock()

        self._pending_tasks = 0
        self._pending_lock = threading.Lock()
        # choose conservative _max_pending to avoid overload
        self._max_pending = max(1, (os.cpu_count() or 2) - 1)

        # new: control drawing of skipped blur bounding boxes
        self.show_skipped_blur = bool(show_skipped_blur)

        # adaptive backoff params
        self.blur_backoff_trigger = int(blur_backoff_trigger)    # consecutive blur checks to trigger backoff
        self.blur_backoff_frames = int(blur_backoff_frames)      # frames to skip after trigger

        # runtime counters/state
        self._consec_blur_count = 0
        self._blur_backoff_remaining = 0
        self._last_precheck_skipped = False

    def start_camera_and_thread(self):
        self.camera.start()
        self.start()

    def sharpness_percent_from_gray(self, gray):
        try:
            var = compute_sharpness(gray)
            percent = min(100.0, max(0.0, (var / float(max(1.0, self.sharpness_var_max))) * 100.0))
            return percent
        except Exception:
            return 0.0

    def _crop_variance(self, crop_bgr):
        """Return Laplacian variance (float) for a crop in BGR."""
        try:
            gray = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2GRAY)
            return compute_sharpness(gray)
        except Exception:
            return 0.0

    def _effective_min_sharpness_var(self):
        """
        Determine the effective absolute variance threshold to use for crop checks:
        - If self.min_sharpness_var provided in config, use it.
        - Else, compute from percent * sharpness_var_max to keep backward compatibility.
        """
        if self.min_sharpness_var is not None:
            return self.min_sharpness_var
        # fallback: compute variance threshold from percent
        try:
            perc = float(self.min_sharpness_percent)
            return (perc / 100.0) * float(max(1.0, self.sharpness_var_max))
        except Exception:
            return 50.0  # safe fallback

    def should_submit_detection(self, frame_bgr):
        """Revised pre-check:
        - If previous annotations exist -> check crop variance (absolute) against min_sharpness_var (or computed fallback).
        - If no previous annotations -> check full-frame percent as before.
        - Maintain adaptive backoff.
        Sets _last_precheck_skipped when detection is skipped by precheck/backoff.
        """
        self._last_precheck_skipped = False

        # honor active backoff
        if self._blur_backoff_remaining > 0:
            self._blur_backoff_remaining -= 1
            self._last_precheck_skipped = True
            logging.debug(f"[{self.camera_name}] pre-check: in backoff, remaining={self._blur_backoff_remaining}")
            return False

        try:
            with self.annotations_lock:
                last_anns = list(self.last_annotations or [])
        except Exception:
            last_anns = []

        H, W = frame_bgr.shape[:2]

        # If we have previous bounding boxes, check crops using absolute variance
        if last_anns:
            any_sharp = False
            var_threshold = self._effective_min_sharpness_var()
            for a in last_anns:
                try:
                    bbox = a.get("bbox")
                    if not bbox:
                        continue
                    x1,y1,x2,y2 = bbox
                    x1c,y1c = max(0,int(x1)), max(0,int(y1))
                    x2c,y2c = min(W,int(x2)), min(H,int(y2))
                    if x2c <= x1c or y2c <= y1c:
                        continue
                    crop = frame_bgr[y1c:y2c, x1c:x2c]
                    if crop is None or crop.size == 0:
                        continue
                    # apply exposure correction if too dark before variance check
                    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
                    if float(gray.mean()) < self.min_luminance and self.exposure_enabled:
                        crop_corr = apply_exposure_correction(crop, exposure_gain=self.exposure_gain, apply_clahe=True)
                        var_val = self._crop_variance(crop_corr)
                    else:
                        var_val = self._crop_variance(crop)
                    if var_val >= var_threshold:
                        any_sharp = True
                        break
                except Exception:
                    continue
            if any_sharp:
                self._consec_blur_count = 0
                return True
            else:
                # all previous crops were below variance threshold
                self._consec_blur_count += 1
                logging.debug(f"[{self.camera_name}] pre-check: all previous crops blurry (consec={self._consec_blur_count})")
                if self._consec_blur_count >= self.blur_backoff_trigger:
                    self._blur_backoff_remaining = self.blur_backoff_frames
                    logging.info(f"[{self.camera_name}] pre-check: triggering blur backoff for {self._blur_backoff_remaining} frames")
                    self._consec_blur_count = 0
                self._last_precheck_skipped = True
                return False

        # no previous annotations -> check whole frame using percent
        try:
            gray_full = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
            sp_full = self.sharpness_percent_from_gray(gray_full)
            if sp_full >= self.min_sharpness_percent:
                self._consec_blur_count = 0
                return True
            else:
                self._consec_blur_count += 1
                logging.debug(f"[{self.camera_name}] pre-check: full frame blurry sp={sp_full:.2f} (consec={self._consec_blur_count})")
                if self._consec_blur_count >= self.blur_backoff_trigger:
                    self._blur_backoff_remaining = self.blur_backoff_frames
                    logging.info(f"[{self.camera_name}] pre-check: triggering blur backoff for {self._blur_backoff_remaining} frames")
                    self._consec_blur_count = 0
                self._last_precheck_skipped = True
                return False
        except Exception:
            logging.exception(f"[{self.camera_name}] sharpness pre-check failed")
            return True  # be permissive on error

    def submit_detection(self, rgb_copy):
        with self._pending_lock:
            if self._pending_tasks >= self._max_pending:
                logging.debug(f"[{self.camera_name}] submit skipped (pending {self._pending_tasks} >= max {self._max_pending})")
                return False
            self._pending_tasks += 1

        future = GLOBAL_FACE_WORKER_POOL.submit(
            process_frame_for_faces, rgb_copy, self.known_faces, self.match_threshold,
            self.min_sharpness_percent, self.sharpness_var_max, self.require_human_check,
            self.exposure_enabled, self.exposure_gain, self.min_luminance,
            False, 0.5
        )

        def cb(fut):
            try:
                annotations = fut.result()
            except Exception:
                logging.exception("detector worker failed")
                annotations = []
            for ann in annotations:
                ann.setdefault("antispoof_checked", False)
                ann.setdefault("antispoof_score", None)
            with self.annotations_lock:
                # update last_annotations which will be used for next pre-check crop list
                self.last_annotations = annotations
            for ann in annotations:
                if ann.get("skipped"):
                    logging.debug(f"[{self.camera_name}] annotation skipped: {ann.get('skip_reason')}")
                else:
                    if ann.get("match"):
                        log_detection(self.camera_name, ann.get("name", "unknown"), "cocok", ann.get("score", 0.0))
                    else:
                        log_detection(self.camera_name, "tidak dikenal", "tidak cocok", ann.get("score", 0.0))
            with self._pending_lock:
                self._pending_tasks = max(0, self._pending_tasks - 1)

        future.add_done_callback(cb)
        return True

    def submit_antispoof_for_annotation(self, ann, frame_bgr):
        if ann.get("antispoof_checked"):
            return

        def job():
            try:
                x1,y1,x2,y2 = ann['bbox']
                h,w = frame_bgr.shape[:2]
                x1c,y1c = max(0,int(x1)), max(0,int(y1))
                x2c,y2c = min(w,int(x2)), min(h,int(y2))
                if x2c <= x1c or y2c <= y1c:
                    return None
                crop = frame_bgr[y1c:y2c, x1c:x2c]
                gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
                if float(gray.mean()) < self.min_luminance and self.exposure_enabled:
                    crop = apply_exposure_correction(crop, exposure_gain=self.exposure_gain, apply_clahe=True)
                is_live, score = antispoof_crop_predict(crop)
                return (is_live, score)
            except Exception:
                logging.exception("antispoof job exception")
                return None

        def cb(fut):
            try:
                res = fut.result()
            except Exception:
                res = None
            if res is None:
                return
            is_live, score = res
            with self.annotations_lock:
                for a in self.last_annotations:
                    if a.get('bbox') == ann.get('bbox'):
                        a['antispoof_checked'] = True
                        a['antispoof_score'] = float(score) if score is not None else None
                        a['antispoof_live'] = bool(is_live)
                        if not is_live:
                            a['skipped'] = True
                            a['skip_reason'] = 'antispoof'
                        break

        future = ANTI_SPOOF_POOL.submit(job)
        future.add_done_callback(cb)

    def run(self):
        logging.info(f"[{self.camera_name}] CameraThread started")
        no_frame = 0
        MAX_NO_FRAME = 300
        fps_time = time.time()
        fps_counter = 0

        while not self._stop_requested:
            frame_bgr = self.camera.get_frame()
            if frame_bgr is None:
                no_frame += 1
                if no_frame % 10 == 0:
                    self.status_update.emit("reconnecting")
                if no_frame > MAX_NO_FRAME:
                    logging.error(f"[{self.camera_name}] too many empty frames; stopping")
                    break
                time.sleep(0.2)
                continue
            no_frame = 0
            self._frame_counter += 1

            # detection submit with pre-check & adaptive backoff
            if (self._frame_counter % self.detect_interval_frames) == 0:
                try:
                    should_submit = self.should_submit_detection(frame_bgr)
                    if should_submit:
                        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
                        submitted = self.submit_detection(rgb)
                        if not submitted:
                            logging.debug(f"[{self.camera_name}] detection submission skipped to avoid backlog")
                        self._last_precheck_skipped = False
                    else:
                        # mark that precheck skipped this frame (used for UI indicator)
                        with self.annotations_lock:
                            self.last_annotations = []  # clear stuck bounding boxes on blur skip
                        logging.debug(f"[{self.camera_name}] detection skipped due to pre-detection blur/backoff")
                        self._last_precheck_skipped = True
                except Exception:
                    logging.exception("submit detection failed")

            with self.annotations_lock:
                annotations = [dict(a) for a in self.last_annotations]

            # antispoof scheduling
            if self.antispoof_enabled and (self._frame_counter % self.antispoof_interval == 0):
                for ann in annotations:
                    if ann.get("skipped"):
                        continue
                    if not ann.get("antispoof_checked", False):
                        self.submit_antispoof_for_annotation(ann, frame_bgr)

            # draw annotations (respect show_skipped_blur) and BLUR-SKIP indicator
            for ann in annotations:
                try:
                    # hide blur-skipped boxes unless configured to show
                    if ann.get("skipped") and ann.get("skip_reason") == "blur" and (not self.show_skipped_blur):
                        continue

                    x1,y1,x2,y2 = ann['bbox']
                    color = (0,255,0) if ann.get("match") else (0,0,255)
                    if ann.get("match"):
                        label = f"{ann.get('name','unknown')} ({ann.get('score',0.0):.2f})"
                    else:
                        if ann.get("skipped"):
                            label = f"SKIP:{ann.get('skip_reason','skip')}"
                        else:
                            label = ann.get("name","tidak cocok")
                    if ann.get("antispoof_checked") and (not ann.get("antispoof_live", True)):
                        color = (0,0,255)
                        label = "FAKE"
                    cv2.rectangle(frame_bgr, (int(x1),int(y1)), (int(x2),int(y2)), color, 2)
                    cv2.putText(frame_bgr, label, (int(x1), max(15,int(y1)-5)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                except Exception:
                    continue

            # show BLUR-SKIP indicator if pre-check skipped detection this frame
            try:
                if self._last_precheck_skipped:
                    h, w = frame_bgr.shape[:2]
                    # draw semi-transparent rectangle behind text for readability
                    try:
                        overlay = frame_bgr.copy()
                        cv2.rectangle(overlay, (5, h-40), (220, h-5), (0,0,0), -1)
                        alpha = 0.45
                        cv2.addWeighted(overlay, alpha, frame_bgr, 1 - alpha, 0, frame_bgr)
                    except Exception:
                        pass
                    cv2.putText(frame_bgr, "BLUR-SKIP", (10, h - 12),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            except Exception:
                logging.exception("Failed drawing BLUR-SKIP indicator")

            # emit frame to UI
            try:
                rgb_out = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
                h,w,ch = rgb_out.shape
                bytes_per_line = ch * w
                qimg = QImage(rgb_out.data, w, h, bytes_per_line, QImage.Format_RGB888)
                self.frame_ready.emit(qimg)
            except Exception:
                logging.exception("QImage conversion failed")

            fps_counter += 1
            if time.time() - fps_time > 1.0:
                logging.debug(f"[{self.camera_name}] FPS:{fps_counter} pending:{self._pending_tasks} consec_blur:{self._consec_blur_count} backoff_left:{self._blur_backoff_remaining}")
                fps_counter = 0
                fps_time = time.time()

            time.sleep(self.display_interval_ms / 1000.0)

        try:
            self.camera.stop()
        except Exception:
            pass
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
    def __init__(self, camera_config):
        super().__init__()
        self.config = camera_config.copy()
        self.name = self.config.get("name","Camera")
        self.source = self.config.get("source",0)
        self.width = int(self.config.get("width",320))
        self.height = int(self.config.get("height",240))
        self.display_interval_ms = int(self.config.get("display_interval_ms",50))
        self.detect_interval_frames = int(self.config.get("detect_interval_frames", self.config.get("interval",4)))
        self.reconnect_delay = int(self.config.get("reconnect_delay",5))
        self.match_threshold = float(self.config.get("match_threshold",0.5))

        # per-camera settings
        # keep backward-compatible keys:
        self.min_sharpness_percent = float(self.config.get("min_sharpness_percent",20.0))
        self.sharpness_var_max = float(self.config.get("sharpness_var_max",1000.0))
        # optional absolute variance threshold (preferred)
        self.min_sharpness_var = self.config.get("min_sharpness_var", None)
        if self.min_sharpness_var is None:
            # allow old key name in cameras.json if present (compat)
            self.min_sharpness_var = self.config.get("min_sharpness_var", None)

        self.require_human_check = bool(self.config.get("require_human_check", False))
        self.exposure_enabled = bool(self.config.get("exposure_enabled", True))
        self.exposure_gain = float(self.config.get("exposure_gain", 1.4))
        self.min_luminance = float(self.config.get("min_luminance", 60.0))
        self.frame_buffer = int(self.config.get("frame_buffer", 1))
        self.antispoof_enabled = bool(self.config.get("antispoof_enabled", False))
        self.antispoof_interval = int(self.config.get("antispoof_interval", 15))
        self.antispoof_model_path = str(self.config.get("antispoof_model_path", ""))
        self.antispoof_threshold = float(self.config.get("antispoof_threshold", 0.5))
        self.show_skipped_blur = bool(self.config.get("show_skipped_blur", False))
        # adaptive backoff options (optional in config)
        self.blur_backoff_trigger = int(self.config.get("blur_backoff_trigger", 3))
        self.blur_backoff_frames = int(self.config.get("blur_backoff_frames", 5))

        layout = QVBoxLayout()
        self.setLayout(layout)
        self.preview = QLabel(f"Memuat {self.name}...")
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setFixedSize(self.width, self.height)
        layout.addWidget(self.preview)

        self.status = QLabel("status: starting...")
        layout.addWidget(self.status)

        self.known_faces = load_known_faces()
        # pass min_sharpness_var so CameraThread can use absolute variance threshold for crop checks
        self.thread = CameraThread(
            self.name, self.source, self.known_faces,
            width=self.width, height=self.height,
            display_interval_ms=self.display_interval_ms,
            detect_interval_frames=self.detect_interval_frames,
            reconnect_delay=self.reconnect_delay,
            backend=cv2.CAP_FFMPEG,
            match_threshold=self.match_threshold,
            min_sharpness_percent=self.min_sharpness_percent,
            sharpness_var_max=self.sharpness_var_max,
            min_sharpness_var=self.min_sharpness_var,
            require_human_check=self.require_human_check,
            exposure_enabled=self.exposure_enabled,
            exposure_gain=self.exposure_gain,
            min_luminance=self.min_luminance,
            frame_buffer=self.frame_buffer,
            antispoof_enabled=self.antispoof_enabled,
            antispoof_interval=self.antispoof_interval,
            antispoof_model_path=self.antispoof_model_path,
            antispoof_threshold=self.antispoof_threshold,
            show_skipped_blur=self.show_skipped_blur,
            blur_backoff_trigger=self.blur_backoff_trigger,
            blur_backoff_frames=self.blur_backoff_frames
        )
        self.thread.frame_ready.connect(self.on_frame)
        self.thread.status_update.connect(self.on_status)
        self.thread.start_camera_and_thread()

    def on_frame(self, qimg):
        self.preview.setPixmap(QPixmap.fromImage(qimg))
        self.status.setText("status: running")

    def on_status(self, text):
        self.status.setText(f"status: {text}")

    def stop(self):
        try:
            self.thread.stop()
        except Exception:
            pass