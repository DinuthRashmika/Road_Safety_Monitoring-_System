from datetime import datetime
from bson import ObjectId
from app.schemas.session import SessionCreate


def session_doc(owner_id: ObjectId, name: str , payload: SessionCreate) -> dict:
    """
    New DMS session document.
    """
    return {
        "ownerId": owner_id,
        "name": name,
        "distanceKm": payload.distanceKm,
        "startedAt": datetime.utcnow(),
        "endedAt": None,
        "metrics": {
            "seatbelt": 0,  # count of seatbelt OFF events
            "phone": 0,     # count of phone-use events
        }
    }
