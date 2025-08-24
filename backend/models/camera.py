
from pydantic import BaseModel, Field
from typing import Union

class Camera(BaseModel):
    name: str = Field("Camera")
    source: Union[int, str] = 0
    display_interval_ms: int = 50
    detect_interval_frames: int = 3
    reconnect_delay: int = 10
    frame_buffer: int = 1
    exposure_enabled: bool = True
    exposure_gain: float = 1.4
    min_luminance: int = 55
