from datetime import datetime
from bson import ObjectId
from typing import Optional

def protective_notification_doc(
    *,
    owner_id: str,
    vehicle_plate: str,
    message: str,
    location: str,
    violation_id: Optional[str] = None,
    violation_type: Optional[str] = None,
    violation_image: Optional[str] = None,
):
    now = datetime.utcnow()
    return {
        "_id": ObjectId(),
        "ownerId": ObjectId(owner_id),
        "vehiclePlate": vehicle_plate,
        "violationId": ObjectId(violation_id) if violation_id else None,

        "message": message,
        "location": location,

        # Details (fine = 0 for protective alerts)
        "violationType": violation_type or "Unknown",
        "fineAmount": 0.0,
        "violationImage": violation_image,

        "isRead": False,
        "type": "protective_alert",   # ✅ NEW notification type
        "createdAt": now,
        "updatedAt": now
    }