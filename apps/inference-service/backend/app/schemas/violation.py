from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime

# --- Shared Models (Used by Detection & Response) ---

class VehicleInfo(BaseModel):
    plate_number: Optional[str] = None
    vehicle_type: Optional[str] = None
    vehicle_model: Optional[str] = None
    owner_name: Optional[str] = None
    owner_phone: Optional[str] = None
    owner_email: Optional[str] = None
    owner_address: Optional[str] = None
    owner_nic: Optional[str] = None

class DetectionResponse(BaseModel):
    # Fix for Pydantic warning: model_config protected_namespaces
    model_config = ConfigDict(protected_namespaces=()) 
    
    success: bool
    error: Optional[str] = None
    timestamp: str
    
    # Plate Detection Info
    plate_number: Optional[str] = None
    confidence: Optional[float] = None
    ocr_confidence: Optional[float] = None
    
    # Violation Info
    violation_type: Optional[str] = "Unknown"
    fine_amount: Optional[float] = 0.0
    violation_id: Optional[str] = None
    
    # Context
    vehicle_info: Optional[VehicleInfo] = None
    notification_sent: bool = False
    
    # Images (Base64)
    annotated_image: Optional[str] = None
    cropped_plate_image: Optional[str] = None
    
    # Renamed from 'model_type' to avoid Pydantic conflict, or handled by ConfigDict above
    model_type: Optional[str] = "yolov8" 
    owner_info: Optional[Dict[str, Any]] = None

# --- Legacy/Existing Models (Required by other routes) ---

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