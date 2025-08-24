
from pydantic import BaseModel
from typing import Tuple, Optional
BBox = Tuple[int, int, int, int]

class Detection(BaseModel):
    bbox: BBox
    name: str = "unknown"
    match: bool = False
    score: float = 0.0
    antispoof_checked: bool = False
    antispoof_live: bool = True
    best_name: Optional[str] = None
