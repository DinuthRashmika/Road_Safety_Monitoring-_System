from datetime import datetime
from typing import Optional
from bson import ObjectId

def vehicle_doc(
    *,
    ownerId,
    vehicleType: str,
    vehicleModel: str,
    registrationDate,
    plateNo: str,
    images: dict[str, Optional[str]] | None = None,
):
    now = datetime.utcnow()
    return {
        "_id": ObjectId(),
        "ownerId": ownerId,
        "vehicleType": vehicleType,
        "vehicleModel": vehicleModel,
        "registrationDate": registrationDate,
        "plateNo": plateNo.upper(),
        "status": "active",
        "images": images or {
            "front": None, "back": None, "right": None, "left": None, "plate": None
        },
        "createdAt": now,
        "updatedAt": now,
    }