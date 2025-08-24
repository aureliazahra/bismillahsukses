
from fastapi import APIRouter
from ..models.config import AppConfig
from ..services.detector_service import load_app_config, save_app_config, detector_boot

router = APIRouter()

@router.get("/app", response_model=AppConfig)
def get_app_config():
    return load_app_config()

@router.put("/app", response_model=AppConfig)
def put_app_config(cfg: AppConfig):
    save_app_config(cfg); detector_boot(); return cfg
