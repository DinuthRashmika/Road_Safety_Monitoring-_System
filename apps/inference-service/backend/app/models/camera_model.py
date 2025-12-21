from datetime import datetime
from bson import ObjectId
import uuid

def camera_doc(
    *,
    name: str,
    location: str,
):
    now = datetime.utcnow()
    return {
        "_id": ObjectId(),
        "name": name,
        "location": location,
        "status": "active",
        "secret_key": uuid.uuid4().hex, # Auto-generate a key for the camera
        "createdAt": now,
        "updatedAt": now,
    }