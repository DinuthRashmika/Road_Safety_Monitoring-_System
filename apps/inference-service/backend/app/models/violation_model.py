from datetime import datetime
from typing import Optional
from bson import ObjectId

def violation_doc(
    *,
    vehicleId,
    plateNumber: str,
    detectionTime: datetime,
    location: Optional[str] = None,
    cameraId: Optional[str] = None,
    confidence: float,
    ocr_confidence: Optional[float] = None,
    imagePath: Optional[str] = None,
    croppedImagePath: Optional[str] = None,
    
    # --- NEW FIELDS ---
    violationType: str = "Unspecified",
    fineAmount: float = 0.0,
    violationConfidence: float = 0.0,
    # ------------------
    
    notified: bool = False,
    notificationSentAt: Optional[datetime] = None,
    ownerId: Optional[str] = None,
):
    now = datetime.utcnow()
    return {
        "_id": ObjectId(),
        "vehicleId": vehicleId,
        "ownerId": ownerId,
        "plateNumber": plateNumber.upper(),
        "detectionTime": detectionTime,
        "location": location,
        "cameraId": cameraId,
        
        # Plate Details
        "confidence": confidence,
        "ocr_confidence": ocr_confidence,
        
        # Violation Details (New Fields)
        "violationType": violationType,
        "fineAmount": fineAmount,
        "violationConfidence": violationConfidence,

        # Images
        "imagePath": imagePath,
        "croppedImagePath": croppedImagePath,
        
        # Notification Status
        "notified": notified,
        "notificationSentAt": notificationSentAt,
        
        # Timestamps
        "createdAt": now,
        "updatedAt": now,
    }