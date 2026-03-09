import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=env_path)

MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_DB         = os.getenv("MONGODB_DB", "Research Project")
MONGODB_ALERTS_COLLECTION = os.getenv("MONGODB_ALERTS_COLLECTION", "alerts")
MONGODB_DETECTIONS_COLLECTION = os.getenv("MONGODB_DETECTIONS_COLLECTION", "detection_sessions")
MONGODB_CAMERAS_COLLECTION= os.getenv("MONGODB_CAMERAS_COLLECTION", "sources")

# Catch the localhost fallback before it causes confusion
if not MONGODB_URI or "localhost" in MONGODB_URI:
    print(f"[DB] WARNING: MONGODB_URI not loaded! Path tried: {env_path}")
else:
    print(f"[DB] ✓ URI loaded: {MONGODB_URI[:40]}...")


# Single client reused across the app lifetime
_client: AsyncIOMotorClient | None = None

def get_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(MONGODB_URI)
    return _client


# Fetch Collections
def get_alerts_collection():
    return get_client()[MONGODB_DB][MONGODB_ALERTS_COLLECTION]

def get_detections_collection():
    return get_client()[MONGODB_DB][MONGODB_DETECTIONS_COLLECTION]

# Save Alert docs
async def save_alert(payload: dict) -> str | None:
    """
    Save an alert payload to MongoDB.
    Returns the inserted document's _id as a string, or None on failure.
    """
    try:
        collection = get_alerts_collection()

        # Alert document structure
        doc = {
            "alert_id":           payload.get("alert_id"),
            "session_id":         payload.get("session_id"),
            "timestamp":          payload.get("timestamp"),
            "camera":             payload.get("camera"),
            "location":           payload.get("location"),
            "threat_level":       payload.get("threat_level"),
            "threat_score":       payload.get("threat_score"),
            "sustained_seconds":  payload.get("sustained_seconds"),
            "action":             payload.get("action"),
            "action_confidence":  payload.get("action_confidence"),
            "objects_detected":   payload.get("objects_detected", []),
            "action_contribution": payload.get("action_contribution"),
            "object_contribution": payload.get("object_contribution"),
            "synergy_bonus":      payload.get("synergy_bonus"),
            "reasoning":          payload.get("reasoning"),
            "human_summary":      payload.get("human_summary"),
            "frame_number":       payload.get("frame_number"),
            "alert_number":       payload.get("alert_number"),
            "has_weapon":         payload.get("has_weapon"),
            "required_sustain_s": payload.get("required_sustain_s"),
        }

        result = await collection.insert_one(doc)
        print(f"[DB] Alert saved → _id: {result.inserted_id}")
        return str(result.inserted_id)

    except Exception as e:
        print(f"[DB] Failed to save alert: {e}")
        return None

# Save detections
async def save_session(summary) -> str | None:
    """
    Save a SessionSummaryDocument to MongoDB.
    Accepts either a Pydantic model or a plain dict.
    """
    try:
        collection = get_detections_collection()
        doc = summary.model_dump() if hasattr(summary, "model_dump") else summary
        result = await collection.insert_one(doc)
        print(f"[DB] Session saved → _id: {result.inserted_id}")
        return str(result.inserted_id)
    except Exception as e:
        print(f"[DB] Failed to save session: {e}")
        return None




# Close the MongoDB connection
async def close_connection():
    global _client
    if _client:
        _client.close()
        _client = None