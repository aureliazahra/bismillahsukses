from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class MissingPersonBase(BaseModel):
    full_name: str
    target_image_url: str
    status: Optional[str] = "missing"
    notes: Optional[str] = None
    approval: Optional[str] = "pending"

class MissingPersonCreate(MissingPersonBase):
    pass

class MissingPersonUpdate(BaseModel):
    full_name: Optional[str] = None
    target_image_url: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    approval: Optional[str] = None

class MissingPersonResponse(MissingPersonBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
