from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any

class ViolationOut(BaseModel):
    id: str
    vehicleId: str
    plateNumber: str
    detectionTime: datetime
    location: Optional[str] = None
    cameraId: Optional[str] = None
    confidence: float
    ocr_confidence: Optional[float] = None
    imageUrl: Optional[str] = None
    croppedImageUrl: Optional[str] = None
    notified: bool = False
    notificationSentAt: Optional[datetime] = None
    ownerDetails: Optional[Dict[str, Any]] = None
    
class PlateDetectionRequest(BaseModel):
    plate_number: str = Field(..., min_length=3)
    confidence: float = Field(..., ge=0, le=1)
    ocr_confidence: Optional[float] = Field(None, ge=0, le=1)
    image_base64: Optional[str] = None
    location: Optional[str] = None
    camera_id: Optional[str] = None
    
class PlateDetectionResponse(BaseModel):
    success: bool
    message: str
    violation_id: Optional[str] = None
    vehicle_owner: Optional[dict] = None
    notification_sent: bool = False

class DetectionResponse(BaseModel):
    success: bool
    plate_number: Optional[str] = None
    confidence: Optional[float] = None
    ocr_confidence: Optional[float] = None
    vehicle_info: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: str
    notification_sent: Optional[bool] = False
    violation_id: Optional[str] = None
    annotated_image: Optional[str] = None
    cropped_plate_image: Optional[str] = None
    model_type: Optional[str] = None
    owner_info: Optional[Dict[str, Any]] = None