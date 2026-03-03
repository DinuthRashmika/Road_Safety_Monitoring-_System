from datetime import datetime
from bson import ObjectId
import uuid

def camera_doc(
    *,
    name: str,
    location: str,
    camera_risk_class: str = "low",   # ✅ NEW
):
    now = datetime.utcnow()
    return {
        "_id": ObjectId(),
        "name": name,
        "location": location,
        "status": "active",
        "secret_key": uuid.uuid4().hex,
        "camera_risk_class": camera_risk_class,  # ✅ NEW
        "createdAt": now,
        "updatedAt": now,
    }