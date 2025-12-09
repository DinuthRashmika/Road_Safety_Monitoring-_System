from __future__ import annotations
from datetime import datetime, timedelta, timezone
from typing import Dict, Tuple

from app.db.mongo import get_db

ACTIVE_STATUSES = {"new", "accepted", "enroute", "arrived"}
RESPONSE_PAIR = ("accepted", "arrived")


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat()


async def _count_active_incidents(role: str, user_id: str) -> int:
    db = get_db()

    if role == "admin":
        query = {"status": {"$in": list(ACTIVE_STATUSES)}}
    else:
        query = {
            "status": {"$in": list(ACTIVE_STATUSES)},
            "$or": [
                {"status": "new", "required_roles": {"$in": [role]}},
                {"assignee_responder_id": user_id, "status": {"$in": ["accepted", "enroute", "arrived"]}}
            ]
        }
    
    return await db["incidents"].count_documents(query)


async def _count_resolved_in_window(window_hours: int, role: str, user_id: str) -> int:
   
    db = get_db()
    since = _iso(_now_utc() - timedelta(hours=window_hours))

    assignment_match_query = {"status": "resolved", "resolved_at": {"$gte": since}}
    
    if role != "admin":
         assignment_match_query["responder_id"] = user_id
         
    pipeline = [
        {"$match": assignment_match_query},
        {"$group": {"_id": "$incident_id"}}, 
        {"$count": "count"},
    ]
    
    agg = db["assignments"].aggregate(pipeline)
    doc = await agg.to_list(length=1)
    return int(doc[0]["count"]) if doc else 0


async def _avg_response_minutes(window_hours: int, role: str, user_id: str) -> float:
    db = get_db()
    since_dt = _now_utc() - timedelta(hours=window_hours)
    since_iso = _iso(since_dt)

    query = {
        "status": {"$in": list(RESPONSE_PAIR)},
        "at": {"$gte": since_iso},
    }

    if role != "admin":
        query["responder_id"] = user_id

    cursor = db["assignments"].find(query, {"incident_id": 1, "status": 1, "at": 1, "_id": 0})

    pairs: Dict[str, Dict[str, datetime]] = {}
    async for doc in cursor:
        inc_id = doc["incident_id"]
        status = doc["status"]
        at = datetime.fromisoformat(doc["at"].replace("Z", "+00:00")).astimezone(timezone.utc)
        if inc_id not in pairs:
            pairs[inc_id] = {}
        if status not in pairs[inc_id] or at < pairs[inc_id][status]:
            pairs[inc_id][status] = at

    total = 0.0
    n = 0
    for inc_id, times in pairs.items():
        if RESPONSE_PAIR[0] in times and RESPONSE_PAIR[1] in times:
            delta = (times[RESPONSE_PAIR[1]] - times[RESPONSE_PAIR[0]]).total_seconds() / 60.0
            if delta >= 0:
                total += delta
                n += 1

    return round(total / n, 1) if n else 0.0


async def metrics_tiles(role: str, user_id: str, window_hours: int = 24) -> dict:
    active = await _count_active_incidents(role, user_id)
    resolved = await _count_resolved_in_window(window_hours, role, user_id)
    avg_resp = await _avg_response_minutes(window_hours, role, user_id)

    return {
        "active": int(active),
        "resolved_window": int(resolved),
        "avg_response_min": float(avg_resp),
        "window_hours": int(window_hours),
    }