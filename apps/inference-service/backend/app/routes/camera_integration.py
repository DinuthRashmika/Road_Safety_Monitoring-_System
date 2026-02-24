from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import Optional
import logging
from bson import ObjectId
import app.db.mongodb as mongodb
# Make sure to import from the correct location based on your project structure
from app.services.plate_owner_service import plate_owner_service 
from app.schemas.violation import DetectionResponse, VehicleInfo
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

    # 1. Validate Camera
    try:
        camera = await database.cameras.find_one({"_id": ObjectId(camera_id)})
    except:
        raise HTTPException(400, "Invalid Camera ID format")

    if not camera:
        raise HTTPException(404, "Camera not registered in system")

    if secret_key and camera.get("secret_key") != secret_key:
        raise HTTPException(401, "Invalid Camera Secret Key")

    camera_location = camera.get("location", "Unknown Location")
    camera_name = camera.get("name", "Unknown Camera")

    logger.info(f"Processing violation from Camera: {camera_name} at {camera_location}")

    # 2. Read Image safely
    try:
        image_bytes = await image.read()
        # CRITICAL: Reset cursor in case downstream services need to read the file object again
        await image.seek(0) 
    except Exception as e:
        raise HTTPException(400, "Failed to read image file")

    # 3. Process using service
    try:
        result = await plate_owner_service.process_complete_detection(
            image_bytes=image_bytes,
            location=camera_location,
            camera_id=str(camera["_id"])
        )
    except Exception as e:
        logger.error(f"Service error: {e}")
        raise HTTPException(500, f"Internal processing error: {str(e)}")

    # 4. Handle Failure
    if not result.get('success'):
        return DetectionResponse(
            success=False,
            error=result.get('error', 'Detection failed'),
            timestamp=result.get('timestamp', datetime.now().isoformat())
        )

    # 5. Map Vehicle Info safely
    vehicle_info_obj = None
    if result.get('owner_info'):
        # Safe access using .get() to prevent 500 errors if keys are missing
        owner_data = result['owner_info'].get('owner', {})
        vehicle_data = result['owner_info'].get('vehicle', {})
        
        vehicle_info_obj = VehicleInfo(
            plate_number=vehicle_data.get('plateNo'),
            vehicle_type=vehicle_data.get('type'),
            vehicle_model=vehicle_data.get('model'),
            owner_name=owner_data.get('name'),
            owner_phone=owner_data.get('phone'),
            owner_email=owner_data.get('email'),
            owner_address=owner_data.get('address'),
            owner_nic=owner_data.get('nic')
        )

    # 6. Return Response
    return DetectionResponse(
        success=True,
        timestamp=result.get('timestamp', datetime.now().isoformat()),
        
        # Detection Data
        plate_number=result.get('plate_number'),
        confidence=result.get('confidence'),
        ocr_confidence=result.get('ocr_confidence'),
        
        # Violation Data
        violation_type=result.get('violation_type', 'Unknown'),
        fine_amount=result.get('fine_amount', 0.0),
        violation_id=str(result.get('violation_id')) if result.get('violation_id') else None,
        
        # Context
        vehicle_info=vehicle_info_obj,
        notification_sent=result.get('notification_sent', False),
        
        # Images
        annotated_image=result.get('annotated_image'),
        cropped_plate_image=result.get('cropped_plate_image'),
        
        model_type="cctv-integration",
        owner_info=result.get('owner_info')
    )