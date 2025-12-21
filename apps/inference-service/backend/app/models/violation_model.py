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
        "confidence": confidence,
        "ocr_confidence": ocr_confidence,
        "imagePath": imagePath,
        "croppedImagePath": croppedImagePath,
        "notified": notified,
        "notificationSentAt": notificationSentAt,
        "createdAt": now,
        "updatedAt": now,
    }