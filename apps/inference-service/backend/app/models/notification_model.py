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
    violation_type: str,  # New field
    fine_amount: float    # New field
):
    now = datetime.utcnow()
    return {
        "_id": ObjectId(),
        "ownerId": ObjectId(owner_id),      # Link to the user who gets the alert
        "vehiclePlate": vehicle_plate,
        "violationId": ObjectId(violation_id), # Link to the violation proof
        "message": message,
        "location": location,
        
        # Detailed Info for App
        "violationType": violation_type,
        "fineAmount": fine_amount,
        
        "isRead": False,                    # To show "New" badge in app
        "type": "violation_alert",
        "createdAt": now,
        "updatedAt": now
    }