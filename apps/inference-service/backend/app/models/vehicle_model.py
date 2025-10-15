from datetime import datetime
from typing import Optional

def vehicle_doc(
    *,
    ownerId,
    vehicleType: str,
    vehicleModel: str,
    registrationDate,  # ISO string
    plateNo: str,
    images: dict[str, Optional[str]] | None = None,
):
    now = datetime.utcnow()
    return {
        "ownerId": ownerId,
        "vehicleType": vehicleType,
        "vehicleModel": vehicleModel,
        "registrationDate": registrationDate,
        "plateNo": plateNo.upper(),
        "images": images or {
            "front": None, "back": None, "right": None, "left": None, "plate": None
        },
        "createdAt": now,
        "updatedAt": now,
    }
