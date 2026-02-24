from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks
from typing import Optional
import base64
import logging
from datetime import datetime
from app.services.plate_owner_service import plate_owner_service
from app.schemas.violation import DetectionResponse
import asyncio

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/detection", tags=["Detection"])

@router.post("/detect-plate", response_model=DetectionResponse)
async def detect_plate_from_image(
    image: Optional[UploadFile] = File(None),
    image_base64: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    camera_id: Optional[str] = Form(None),
    background_tasks: BackgroundTasks = None
):
    """
    Complete plate detection pipeline: Detect -> Identify -> Violation -> Notify
    """
    try:
        # Get image bytes
        image_bytes = None
        if image:
            image_bytes = await image.read()
        elif image_base64:
            try:
                if ',' in image_base64:
                    image_base64 = image_base64.split(',')[1]
                image_bytes = base64.b64decode(image_base64)
            except Exception as e:
                raise HTTPException(400, f"Invalid base64 image: {str(e)}")
        else:
            raise HTTPException(400, "No image provided")
        
        # Process detection
        result = await plate_owner_service.process_complete_detection(
            image_bytes=image_bytes,
            location=location,
            camera_id=camera_id
        )
        
        if not result['success']:
            return DetectionResponse(
                success=False,
                error=result.get('error', 'Detection failed'),
                timestamp=result.get('timestamp', datetime.now().isoformat())
            )
        
        # Map keys correctly
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
            vehicle_info=vehicle_info,
            notification_sent=result.get('notification_sent', False),
            violation_id=result.get('violation_id'),
            annotated_image=result.get('annotated_image'),
            cropped_plate_image=result.get('cropped_plate_image'),
            violation_type=result.get('violation_type', 'Unknown'),
            fine_amount=result.get('fine_amount', 0.0),
            model_type="yolov8-easyocr-srilanka",
            owner_info=result.get('owner_info'),
            timestamp=result.get('timestamp', datetime.now().isoformat())
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Detection error: {str(e)}")
        return DetectionResponse(
            success=False,
            error=str(e),
            timestamp=datetime.now().isoformat()
        )