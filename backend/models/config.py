
from pydantic import BaseModel
from typing import Dict

class AppConfig(BaseModel):
    device: str = "GPU"
    debug: bool = False
    detector_backend: str = "insightface"
    antispoof_backend: str = "heuristic_high"
    antispoof_model_path: str = "models/antispoof/minifasnet/minifasnet.onnx"
    match_threshold: float = 0.6
    red_cutoff_threshold: float = 0.4
    require_human_check: bool = True
    box_thickness_max: int = 2
    save_mode: str = "photo"
    save_which: str = "green"
    log_interval_seconds: int = 3
    antispoof_preprocess: str = "bgr_norm"
    antispoof_live_index: int | None = 2
    antispoof_mode: str = "high"
    antispoof_thresholds: Dict[str, float] = {"low":0.4,"medium":0.55,"high":0.7}
    antispoof_smooth_k: int = 3
    min_live_face_size: int = 90
    min_interocular_px: int = 38
    suppress_small_faces_when_antispoof: bool = True
