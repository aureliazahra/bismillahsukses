from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import os
from datetime import datetime

from ..config.database import get_db
from ..models.missing_person import MissingPerson
from ..models.schemas import MissingPersonCreate, MissingPersonUpdate, MissingPersonResponse

router = APIRouter()

@router.get("/", response_model=List[MissingPersonResponse])
def get_missing_persons(db: Session = Depends(get_db)):
    """Get all missing persons"""
    missing_persons = db.query(MissingPerson).all()
    return missing_persons

@router.get("/{missing_person_id}", response_model=MissingPersonResponse)
def get_missing_person(missing_person_id: int, db: Session = Depends(get_db)):
    """Get a specific missing person by ID"""
    missing_person = db.query(MissingPerson).filter(MissingPerson.id == missing_person_id).first()
    if not missing_person:
        raise HTTPException(status_code=404, detail="Missing person not found")
    return missing_person

@router.post("/", response_model=MissingPersonResponse, status_code=status.HTTP_201_CREATED)
def create_missing_person(missing_person: MissingPersonCreate, db: Session = Depends(get_db)):
    """Create a new missing person"""
    db_missing_person = MissingPerson(**missing_person.dict())
    db.add(db_missing_person)
    db.commit()
    db.refresh(db_missing_person)
    return db_missing_person

@router.put("/{missing_person_id}", response_model=MissingPersonResponse)
def update_missing_person(
    missing_person_id: int, 
    missing_person_update: MissingPersonUpdate, 
    db: Session = Depends(get_db)
):
    """Update a missing person"""
    db_missing_person = db.query(MissingPerson).filter(MissingPerson.id == missing_person_id).first()
    if not db_missing_person:
        raise HTTPException(status_code=404, detail="Missing person not found")
    
    update_data = missing_person_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_missing_person, field, value)
    
    db_missing_person.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_missing_person)
    return db_missing_person

@router.delete("/{missing_person_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_missing_person(missing_person_id: int, db: Session = Depends(get_db)):
    """Delete a missing person"""
    db_missing_person = db.query(MissingPerson).filter(MissingPerson.id == missing_person_id).first()
    if not db_missing_person:
        raise HTTPException(status_code=404, detail="Missing person not found")
    
    # Delete the image file if it exists
    if db_missing_person.target_image_url and os.path.exists(db_missing_person.target_image_url):
        try:
            os.remove(db_missing_person.target_image_url)
        except:
            pass  # Ignore errors when deleting files
    
    db.delete(db_missing_person)
    db.commit()
    return None
