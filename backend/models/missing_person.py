from sqlalchemy import Column, Integer, String, Text, DateTime, func
from backend.config.database import Base

class MissingPerson(Base):
    __tablename__ = "missing_persons"

    id = Column(Integer, primary_key=True, autoincrement=True)
    full_name = Column(String(120), nullable=False)
    target_image_url = Column(Text, nullable=False)
    status = Column(String(16), nullable=True, server_default='missing')
    notes = Column(Text)
    approval = Column(String(16), nullable=False, server_default='pending')
    # PENTING: default=func.now() (client-side), bukan server_default
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
