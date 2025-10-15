from datetime import datetime
from bson import ObjectId

def event_doc(session_id: ObjectId, etype: str, conf: float):
    """
    One confirmed event row (after debouncing).
    """
    return {
        "sessionId": session_id,
        "type": etype,              # "seatbelt" | "phone"
        "confidence": float(conf),  # 0..1
        "createdAt": datetime.utcnow()
    }
