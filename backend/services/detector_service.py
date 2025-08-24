
import os, json, logging
from typing import List
from ..models.config import AppConfig
from ..models.detection import Detection
from .logger_service import app_logger

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

try:
    from ..core import detector as partner_detector
    _detector_mod = partner_detector
except Exception:
    _detector_mod = None
    logging.warning("[detector_service] core/detector.py tidak ditemukan; pakai dummy.")

_known_faces = []
_cfg: AppConfig | None = None
_initialized = False

def _cfg_path(): return os.path.join(DATA_DIR, "app_config.json")
def _faces_dir(): return os.path.join(DATA_DIR, "target_faces")
def _ensure_dirs():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(_faces_dir(), exist_ok=True)
    os.makedirs(os.path.join(DATA_DIR, "logs"), exist_ok=True)

def load_app_config() -> AppConfig:
    _ensure_dirs()
    p = _cfg_path()
    if os.path.exists(p):
        with open(p, "r", encoding="utf-8") as f: return AppConfig(**json.load(f))
    cfg = AppConfig()
    with open(p, "w", encoding="utf-8") as f: json.dump(cfg.model_dump(), f, indent=2, ensure_ascii=False)
    return cfg

def save_app_config(cfg: AppConfig):
    with open(_cfg_path(), "w", encoding="utf-8") as f:
        json.dump(cfg.model_dump(), f, indent=2, ensure_ascii=False)

def detector_boot():
    global _initialized, _cfg, _known_faces
    _cfg = load_app_config()
    if _detector_mod is None:
        _initialized = True; app_logger.info("Detector dummy aktif."); return
    use_gpu = str(_cfg.device).upper() == "GPU"
    try:
        _detector_mod.initialize(use_gpu=use_gpu, detector_backend=_cfg.detector_backend)
        if _cfg.antispoof_backend == "minifasnet":
            _detector_mod.load_antispoof_model(_cfg.antispoof_model_path, use_gpu=use_gpu)
        _detector_mod.set_antispoof_params(
            live_index=None if _cfg.antispoof_live_index in (-1, None) else int(_cfg.antispoof_live_index),
            thresholds=_cfg.antispoof_thresholds, mode=_cfg.antispoof_mode,
            preprocess=_cfg.antispoof_preprocess, smooth_k=_cfg.antispoof_smooth_k,
        )
        _known_faces = _detector_mod.load_known_faces(_faces_dir())
        _initialized = True; app_logger.info("Detector initialized. known_faces=%d", len(_known_faces))
    except Exception:
        app_logger.exception("Detector init failed"); _initialized = False

def reload_known_faces():
    global _known_faces
    if _detector_mod is None: _known_faces = []
    else: _known_faces = _detector_mod.load_known_faces(_faces_dir())
    app_logger.info("Reloaded known faces: %d", len(_known_faces))
    return len(_known_faces)

def process_frame(bgr_frame) -> List[Detection]:
    if bgr_frame is None or not _initialized: return []
    if _detector_mod is None: return []
    import cv2
    try:
        rgb = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
        anns = _detector_mod.process_frame_for_faces(
            rgb, _known_faces,
            match_threshold=_cfg.match_threshold if _cfg else 0.6,
            require_human_check=_cfg.require_human_check if _cfg else True,
            exposure_enabled=True, exposure_gain=1.4, min_luminance=60,
            antispoof_backend=_cfg.antispoof_backend if _cfg else "off",
            min_live_face_size=_cfg.min_live_face_size if _cfg else 90,
            min_interocular_px=_cfg.min_interocular_px if _cfg else 38,
            suppress_small_faces_when_antispoof=_cfg.suppress_small_faces_when_antispoof if _cfg else True,
        ) or []
        out = []
        for a in anns:
            try:
                out.append(Detection(
                    bbox=tuple(map(int, a.get("bbox",(0,0,0,0)))),
                    name=a.get("name","unknown"),
                    match=bool(a.get("match",False)),
                    score=float(a.get("score",0.0)),
                    antispoof_checked=bool(a.get("antispoof_checked", False)),
                    antispoof_live=bool(a.get("antispoof_live", True)),
                    best_name=a.get("best_name")
                ))
            except Exception: continue
        return out
    except Exception:
        app_logger.exception("partner detector failed"); return []
