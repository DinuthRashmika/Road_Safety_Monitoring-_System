from datetime import datetime
from bson import ObjectId

def session_doc(owner_id: ObjectId, name: str):
    """
    New DMS session document.
    """
    return {
        "ownerId": owner_id,
        "name": name,
        "startedAt": datetime.utcnow(),
        "endedAt": None,
        "metrics": {
            "seatbelt": 0,  # count of seatbelt OFF events
            "phone": 0,     # count of phone-use events
        }
    }
