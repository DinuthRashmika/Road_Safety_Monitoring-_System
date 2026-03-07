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
    current_admin=Depends(get_current_admin)
):
    """
    Admin Only: Register a new CCTV camera to the system.
    """
    if mongodb.db is None or mongodb.db.db is None:
        raise HTTPException(500, "Database not initialized")

    database = mongodb.db.db

    # ✅ FIX: pass camera_risk_class into camera_doc
    new_camera = camera_doc(
        name=camera_data.name,
        location=camera_data.location,
        camera_risk_class=camera_data.camera_risk_class  # ✅ NEW
    )

    result = await database.cameras.insert_one(new_camera)

    # ✅ FIX: response MUST include camera_risk_class
    return {
        "id": str(result.inserted_id),
        "name": new_camera["name"],
        "location": new_camera["location"],
        "status": new_camera["status"],
        "secret_key": new_camera["secret_key"],
        "camera_risk_class": new_camera.get("camera_risk_class", "low"),  # ✅ NEW
        "createdAt": new_camera["createdAt"]
    }


@router.get("/cameras", response_model=List[CameraOut])
async def list_cameras(current_admin=Depends(get_current_admin)):
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
            "name": cam.get("name", ""),
            "location": cam.get("location", ""),
            "status": cam.get("status", "active"),
            "secret_key": cam.get("secret_key", ""),
            "camera_risk_class": cam.get("camera_risk_class", "low"),  # ✅ NEW + fallback
            "createdAt": cam.get("createdAt")
        })

    return cameras