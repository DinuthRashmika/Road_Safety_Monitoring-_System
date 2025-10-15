from app.db.mongo import get_db

async def append_timeline(incident_id: str, unit_id: str, status: str, at: str):
    db = get_db()
    await db["assignments"].insert_one({"incident_id": incident_id, "unit_id": unit_id, "status": status, "at": at})
