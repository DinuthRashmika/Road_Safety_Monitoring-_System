from app.db.mongo import get_db
from datetime import datetime, timedelta, timezone

async def metrics_tiles():
    db = get_db()
    active = await db["incidents"].count_documents({"status":{"$in":["new","accepted","enroute","arrived"]}})
    resolved_today = await db["incidents"].count_documents({
        "status":"resolved",
        "reported_at":{"$gte": (datetime.now(timezone.utc)-timedelta(days=1)).isoformat()}
    })
    units_available = await db["units"].count_documents({"status":"available"})
    return {"active": active, "resolved_today": resolved_today, "units_available": units_available, "avg_response_min": 0}
