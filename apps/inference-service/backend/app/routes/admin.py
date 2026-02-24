from fastapi import APIRouter, Depends, HTTPException
from typing import List
import app.db.mongodb as mongodb
from app.core.deps import get_current_admin
from app.schemas.camera import CameraCreateIn, CameraOut
from app.models.camera_model import camera_doc
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/admin", tags=["Admin Dashboard"])

@router.post("/cameras", response_model=CameraOut, status_code=201)
async def register_camera(
    camera_data: CameraCreateIn,
    current_admin = Depends(get_current_admin)
):
    """
    Admin Only: Register a new CCTV camera to the system.
    """
    if mongodb.db is None or mongodb.db.db is None:
        raise HTTPException(500, "Database not initialized")
    
    database = mongodb.db.db

    # Create document
    new_camera = camera_doc(
        name=camera_data.name,
        location=camera_data.location
    )

    result = await database.cameras.insert_one(new_camera)
    
    return {
        "id": str(result.inserted_id),
        "name": new_camera["name"],
        "location": new_camera["location"],
        "status": new_camera["status"],
        "secret_key": new_camera["secret_key"],
        "createdAt": new_camera["createdAt"]
    }

@router.get("/cameras", response_model=List[CameraOut])
async def list_cameras(current_admin = Depends(get_current_admin)):
    """
    Admin Only: List all registered cameras.
    """
    if mongodb.db is None or mongodb.db.db is None:
        raise HTTPException(500, "Database not initialized")
    
    database = mongodb.db.db
    cameras = []
    
    cursor = database.cameras.find({})
    async for cam in cursor:
        cameras.append({
            "id": str(cam["_id"]),
            "name": cam["name"],
            "location": cam["location"],
            "status": cam["status"],
            "secret_key": cam.get("secret_key", ""),
            "createdAt": cam["createdAt"]
        })
        
    return cameras