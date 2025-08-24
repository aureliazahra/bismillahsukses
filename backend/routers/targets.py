
import os, shutil
from typing import List
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from ..services.detector_service import reload_known_faces

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
TARGET_DIR = os.path.join(DATA_DIR, "target_faces")

router = APIRouter()

@router.post("/upload")
async def upload_targets(name: str = Form(...), files: List[UploadFile] = File(...)):
    if not name.strip(): raise HTTPException(400, "name required")
    safe = name.strip().replace("/", "_").replace("\\", "_")
    dest = os.path.join(TARGET_DIR, safe)
    os.makedirs(dest, exist_ok=True)
    saved=0
    for f in files:
        ext = os.path.splitext(f.filename or "")[1].lower()
        if ext not in [".jpg",".jpeg",".png",".bmp",".webp"]: continue
        i=0; base=os.path.splitext(os.path.basename(f.filename or "img"))[0]
        out=os.path.join(dest, f"{base}{ext}")
        while os.path.exists(out):
            i+=1; out=os.path.join(dest, f"{base}_{i}{ext}")
        with open(out, "wb") as w: w.write(await f.read())
        saved+=1
    nfaces = reload_known_faces()
    return {"ok": True, "saved": saved, "known_faces": nfaces}

@router.get("")
def list_targets():
    res=[]
    if os.path.isdir(TARGET_DIR):
        for d in os.listdir(TARGET_DIR):
            p=os.path.join(TARGET_DIR,d)
            if os.path.isdir(p):
                imgs=[fn for fn in os.listdir(p) if os.path.splitext(fn)[1].lower() in (".jpg",".jpeg",".png",".bmp",".webp")]
                res.append({"name":d,"count":len(imgs)})
    return res

@router.delete("/{name}")
def delete_target(name:str):
    safe = name.strip().replace("/", "_").replace("\\", "_")
    p=os.path.join(TARGET_DIR, safe)
    if not os.path.isdir(p): raise HTTPException(404,"not found")
    shutil.rmtree(p)
    nfaces = reload_known_faces()
    return {"ok": True, "known_faces": nfaces}
