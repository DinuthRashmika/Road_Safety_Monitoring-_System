from datetime import datetime
from bson import ObjectId
from typing import Optional

def notification_doc(
    *,
    owner_id: str,
    vehicle_plate: str,
    violation_id: str,
    message: str,
    location: str,
    violation_type: str,
    fine_amount: float,
    violation_image: Optional[str] = None # <--- NEW FIELD
):
    now = datetime.utcnow()
    return {
        "_id": ObjectId(),
        "ownerId": ObjectId(owner_id),
        "vehiclePlate": vehicle_plate,
        "violationId": ObjectId(violation_id),
        "message": message,
        "location": location,
        
        # Detailed Info for App
        "violationType": violation_type,
        "fineAmount": fine_amount,
        "violationImage": violation_image, # <--- Stores relative path (e.g. "detections/2026-01-07/img.jpg")
        
        "isRead": False,
        "type": "violation_alert",
        "createdAt": now,
        "updatedAt": now
    }