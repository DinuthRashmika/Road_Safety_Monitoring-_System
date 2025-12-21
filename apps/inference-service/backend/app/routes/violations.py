from fastapi import APIRouter, HTTPException, Depends, Request
from datetime import datetime, timedelta
from typing import Optional
from bson import ObjectId
import app.db.mongodb as mongodb
from app.core.deps import get_current_owner
import base64
import logging

# Import schemas - check if they exist
try:
    from app.schemas.violation import ViolationOut, PlateDetectionRequest, PlateDetectionResponse
    SCHEMAS_AVAILABLE = True
except ImportError as e:
    logging.error(f"Failed to import schemas: {e}")
    # Create mock schemas if import fails
    from pydantic import BaseModel, Field
    from datetime import datetime
    from typing import Optional
    
    class ViolationOut(BaseModel):
        id: str
        vehicleId: str
        plateNumber: str
        detectionTime: datetime
        location: Optional[str]
        cameraId: Optional[str]
        confidence: float
        imageUrl: Optional[str]
        notified: bool
        ownerDetails: Optional[dict]
    
    class PlateDetectionRequest(BaseModel):
        plate_number: str = Field(..., min_length=3)
        confidence: float = Field(..., ge=0, le=1)
        image_base64: Optional[str] = None
        location: Optional[str] = None
        camera_id: Optional[str] = None
    
    class PlateDetectionResponse(BaseModel):
        success: bool
        message: str
        violation_id: Optional[str] = None
        vehicle_owner: Optional[dict] = None
        notification_sent: bool = False
    
    SCHEMAS_AVAILABLE = False

# Try to import detector, but provide a fallback
try:
    from app.services.plate_detector import detector
    PLATE_DETECTOR_AVAILABLE = True
except ImportError:
    PLATE_DETECTOR_AVAILABLE = False
    # Create a mock detector
    class MockDetector:
        def __init__(self):
            self.model = None
        
        def load_model(self, model_path):
            print(f"Mock: Would load model from {model_path}")
            return True
        
        def detect_plate(self, image_bytes):
            print("Mock: Detecting plate")
            return "ABC123", 0.85
        
        async def process_detection(self, plate_number, confidence, image_bytes=None, location=None):
            return {
                "success": True,
                "plate_number": plate_number,
                "confidence": confidence,
                "detection_time": datetime.now().isoformat()
            }
    
    detector = MockDetector()

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/violations", tags=["Violations"])

@router.post("/detect", response_model=PlateDetectionResponse)
async def process_plate_detection(detection: PlateDetectionRequest):
    """
    Process plate detection from CCTV system.
    """
    if mongodb.db is None or mongodb.db.db is None:
        raise HTTPException(500, "Database not initialized")
    
    database = mongodb.db.db
    
    try:
        # Convert base64 image to bytes if provided
        image_data = None
        if detection.image_base64:
            try:
                image_data = base64.b64decode(detection.image_base64)
            except:
                image_data = None
        
        # Process detection
        result = await detector.process_detection(
            plate_number=detection.plate_number,
            confidence=detection.confidence,
            image_bytes=image_data,
            location=detection.location
        )
        
        if result.get("success"):
            return PlateDetectionResponse(
                success=True,
                message="Detection processed successfully",
                violation_id=None,  # TODO: Add when storing in DB
                vehicle_owner=result.get("owner_info"),
                notification_sent=False
            )
        else:
            return PlateDetectionResponse(
                success=False,
                message=result.get("error", "Failed to process detection")
            )
            
    except Exception as e:
        logger.error(f"Error processing detection: {e}")
        raise HTTPException(500, f"Error processing detection: {str(e)}")

@router.get("/test")
async def test_violations():
    """Test endpoint"""
    return {
        "status": "working",
        "plate_detector_available": PLATE_DETECTOR_AVAILABLE,
        "schemas_available": SCHEMAS_AVAILABLE,
        "message": "Violations endpoint is working"
    }