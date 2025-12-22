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

# --- NEW Helper Class ---
class VehicleInfo(BaseModel):
    plate_number: Optional[str] = None
    vehicle_type: Optional[str] = None
    vehicle_model: Optional[str] = None
    owner_name: Optional[str] = None
    owner_phone: Optional[str] = None
    owner_email: Optional[str] = None
    owner_address: Optional[str] = None
    owner_nic: Optional[str] = None

# --- UPDATED DetectionResponse ---
class DetectionResponse(BaseModel):
    success: bool
    error: Optional[str] = None
    timestamp: str
    
    # Plate Detection Info
    plate_number: Optional[str] = None
    confidence: Optional[float] = None
    ocr_confidence: Optional[float] = None
    
    # --- NEW: Violation Info ---
    violation_type: Optional[str] = None 
    fine_amount: Optional[float] = None  
    # ---------------------------

    vehicle_info: Optional[VehicleInfo] = None
    notification_sent: bool = False
    violation_id: Optional[str] = None
    
    # Images (Base64)
    annotated_image: Optional[str] = None
    cropped_plate_image: Optional[str] = None
    
    model_type: Optional[str] = "yolov8"
    owner_info: Optional[Dict[str, Any]] = None