#!/usr/bin/env python3
"""
Simple FastAPI backend for Flutter CCTV Management integration
This provides basic CRUD operations for cameras and real-time status updates
"""

import json
import os
import time
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Camera data model
class CameraCreate(BaseModel):
    name: str
    location: str
    status: str
    source: str
    width: int = 640
    height: int = 480

class CameraUpdate(BaseModel):
    status: Optional[str] = None
    name: Optional[str] = None
    location: Optional[str] = None

class CameraResponse(BaseModel):
    id: str
    name: str
    location: str
    status: str
    last_updated: str
    source: str
    width: int
    height: int

# Initialize FastAPI app
app = FastAPI(title="Obserra CCTV API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# File paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CAMERAS_FILE = os.path.join(BASE_DIR, "cameras.json")
CAMERAS_BACKUP = os.path.join(BASE_DIR, "cameras_backup.json")

# In-memory camera storage (fallback if file doesn't exist)
cameras_db = []

def load_cameras() -> List[dict]:
    """Load cameras from JSON file or create default ones"""
    global cameras_db
    
    if os.path.exists(CAMERAS_FILE):
        try:
            with open(CAMERAS_FILE, 'r', encoding='utf-8') as f:
                cameras_db = json.load(f)
                # Ensure each camera has an ID
                for camera in cameras_db:
                    if 'id' not in camera:
                        camera['id'] = f"CAM-{len(cameras_db):03d}"
                    if 'last_updated' not in camera:
                        camera['last_updated'] = datetime.now().isoformat()
        except Exception as e:
            print(f"Error loading cameras.json: {e}")
            cameras_db = []
    
    # If no cameras loaded, create default ones
    if not cameras_db:
        cameras_db = [
            {
                "id": "CAM-001",
                "name": "Kamera CCTV 1",
                "location": "Gate A",
                "status": "Active",
                "last_updated": datetime.now().isoformat(),
                "source": "0",
                "width": 640,
                "height": 480,
            },
            {
                "id": "CAM-002", 
                "name": "IP Kamera Luar",
                "location": "Gate B",
                "status": "Active",
                "last_updated": datetime.now().isoformat(),
                "source": "rtsp://aatc:ke67bu@192.168.0.239:554/stream1",
                "width": 640,
                "height": 480,
            },
            {
                "id": "CAM-003",
                "name": "IP Kamera Dalam", 
                "location": "Gate C",
                "status": "Offline",
                "last_updated": datetime.now().isoformat(),
                "source": "rtsp://admin:admin@192.168.0.241:554/stream1",
                "width": 640,
                "height": 480,
            }
        ]
        save_cameras()
    
    return cameras_db

def save_cameras():
    """Save cameras to JSON file"""
    try:
        # Create backup first
        if os.path.exists(CAMERAS_FILE):
            with open(CAMERAS_FILE, 'r', encoding='utf-8') as f:
                backup_data = f.read()
            with open(CAMERAS_BACKUP, 'w', encoding='utf-8') as f:
                f.write(backup_data)
        
        # Save current data
        with open(CAMERAS_FILE, 'w', encoding='utf-8') as f:
            json.dump(cameras_db, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving cameras: {e}")
        return False

def generate_camera_id() -> str:
    """Generate unique camera ID"""
    existing_ids = [cam['id'] for cam in cameras_db]
    counter = 1
    while f"CAM-{counter:03d}" in existing_ids:
        counter += 1
    return f"CAM-{counter:03d}"

# Load cameras on startup
load_cameras()

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Obserra CCTV Management API",
        "version": "1.0.0",
        "endpoints": [
            "GET /cameras - List all cameras",
            "POST /cameras - Add new camera", 
            "PUT /cameras/{camera_id} - Update camera",
            "DELETE /cameras/{camera_id} - Delete camera",
            "GET /cameras/{camera_id}/status - Get camera status"
        ]
    }

@app.get("/cameras", response_model=List[CameraResponse])
async def get_cameras():
    """Get all cameras"""
    return cameras_db

@app.get("/cameras/{camera_id}", response_model=CameraResponse)
async def get_camera(camera_id: str):
    """Get specific camera by ID"""
    camera = next((cam for cam in cameras_db if cam['id'] == camera_id), None)
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    return camera

@app.post("/cameras", response_model=CameraResponse)
async def create_camera(camera: CameraCreate):
    """Create new camera"""
    new_camera = {
        "id": generate_camera_id(),
        "name": camera.name,
        "location": camera.location,
        "status": camera.status,
        "last_updated": datetime.now().isoformat(),
        "source": camera.source,
        "width": camera.width,
        "height": camera.height,
    }
    
    cameras_db.append(new_camera)
    if save_cameras():
        return new_camera
    else:
        raise HTTPException(status_code=500, detail="Failed to save camera")

@app.put("/cameras/{camera_id}", response_model=CameraResponse)
async def update_camera(camera_id: str, camera_update: CameraUpdate):
    """Update existing camera"""
    camera = next((cam for cam in cameras_db if cam['id'] == camera_id), None)
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    
    # Update fields
    if camera_update.status is not None:
        camera['status'] = camera_update.status
    if camera_update.name is not None:
        camera['name'] = camera_update.name
    if camera_update.location is not None:
        camera['location'] = camera_update.location
    
    camera['last_updated'] = datetime.now().isoformat()
    
    if save_cameras():
        return camera
    else:
        raise HTTPException(status_code=500, detail="Failed to save camera")

@app.delete("/cameras/{camera_id}")
async def delete_camera(camera_id: str):
    """Delete camera"""
    global cameras_db
    camera = next((cam for cam in cameras_db if cam['id'] == camera_id), None)
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    
    cameras_db = [cam for cam in cameras_db if cam['id'] != camera_id]
    if save_cameras():
        return {"message": f"Camera {camera_id} deleted successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to delete camera")

@app.get("/cameras/{camera_id}/status")
async def get_camera_status(camera_id: str):
    """Get camera status (for real-time updates)"""
    camera = next((cam for cam in cameras_db if cam['id'] == camera_id), None)
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    
    return {
        "id": camera_id,
        "status": camera['status'],
        "last_updated": camera['last_updated']
    }

@app.post("/cameras/{camera_id}/toggle")
async def toggle_camera_status(camera_id: str):
    """Toggle camera status between Active and Offline"""
    camera = next((cam for cam in cameras_db if cam['id'] == camera_id), None)
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    
    # Toggle status
    current_status = camera['status']
    new_status = "Offline" if current_status == "Active" else "Active"
    camera['status'] = new_status
    camera['last_updated'] = datetime.now().isoformat()
    
    if save_cameras():
        return {
            "id": camera_id,
            "old_status": current_status,
            "new_status": new_status,
            "last_updated": camera['last_updated']
        }
    else:
        raise HTTPException(status_code=500, detail="Failed to update camera status")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "cameras_count": len(cameras_db)
    }

if __name__ == "__main__":
    print("Starting Obserra CCTV API...")
    print(f"Cameras loaded: {len(cameras_db)}")
    print("API will be available at: http://localhost:8000")
    print("Press Ctrl+C to stop")
    
    uvicorn.run(
        "simple_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
