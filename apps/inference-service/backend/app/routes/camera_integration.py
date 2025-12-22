from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks
from typing import Optional
import logging
from bson import ObjectId
import app.db.mongodb as mongodb
from app.services.plate_owner_service import plate_owner_service
from app.schemas.violation import DetectionResponse
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/cctv", tags=["CCTV Integration"])

@router.post("/{camera_id}/upload-violation", response_model=DetectionResponse)
async def upload_violation_from_camera(
    camera_id: str,
    image: UploadFile = File(...),
    secret_key: Optional[str] = Form(None) 
):
    """
    Endpoint for Registered CCTV Cameras to upload violation images.
    """
    if mongodb.db is None or mongodb.db.db is None:
        raise HTTPException(500, "Database not initialized")
        
    database = mongodb.db.db

    # 1. Validate Camera and get Location
    try:
        camera = await database.cameras.find_one({"_id": ObjectId(camera_id)})
    except:
        raise HTTPException(400, "Invalid Camera ID format")

    if not camera:
        raise HTTPException(404, "Camera not registered in system")

    if secret_key and camera.get("secret_key") != secret_key:
        raise HTTPException(401, "Invalid Camera Secret Key")

    camera_location = camera["location"]
    camera_name = camera["name"]

    logger.info(f"Processing violation from Camera: {camera_name} at {camera_location}")

    # 2. Read Image
    try:
        image_bytes = await image.read()
    except Exception as e:
        raise HTTPException(400, "Failed to read image file")

    # 3. Process using service
    result = await plate_owner_service.process_complete_detection(
        image_bytes=image_bytes,
        location=camera_location,
        camera_id=str(camera["_id"])
    )

    # 4. Return standard response
    if not result['success']:
        return DetectionResponse(
            success=False,
            error=result.get('error', 'Detection failed'),
            timestamp=result.get('timestamp', datetime.now().isoformat())
        )

    # Map the vehicle info keys
    vehicle_info = None
    if result.get('owner_info'):
        owner = result['owner_info']['owner']
        vehicle = result['owner_info']['vehicle']
        
        vehicle_info = {
            "plate_number": vehicle.get('plateNo'),
            "vehicle_type": vehicle.get('type'),
            "vehicle_model": vehicle.get('model'),
            "owner_name": owner.get('name'),
            "owner_phone": owner.get('phone'),
            "owner_email": owner.get('email'),
            "owner_address": owner.get('address'),
            "owner_nic": owner.get('nic')
        }

    return DetectionResponse(
        success=True,
        plate_number=result.get('plate_number'),
        confidence=result.get('confidence'),
        ocr_confidence=result.get('ocr_confidence'),
        
        # --- NEW MAPPING HERE ---
        violation_type=result.get('violation_type', 'Unknown'), # Map from service result
        fine_amount=result.get('fine_amount', 0.0),             # Map from service result
        # ------------------------

        vehicle_info=vehicle_info,
        notification_sent=result.get('notification_sent', False),
        violation_id=result.get('violation_id'),
        annotated_image=result.get('annotated_image'),
        cropped_plate_image=result.get('cropped_plate_image'),
        model_type="cctv-integration",
        owner_info=result.get('owner_info'),
        timestamp=result.get('timestamp', datetime.now().isoformat())
    )