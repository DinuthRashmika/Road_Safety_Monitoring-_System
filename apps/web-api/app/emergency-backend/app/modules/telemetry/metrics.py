# app/modules/telemetry/metrics.py
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Dict, Tuple

from app.db.mongo import get_db


ACTIVE_STATUSES = {"new", "accepted", "enroute", "arrived"}
RESPONSE_PAIR = ("accepted", "arrived")


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    # Store/compare ISO strings consistently
    return dt.astimezone(timezone.utc).isoformat()


async def _count_active_incidents() -> int:
    db = get_db()
    return await db["incidents"].count_documents({"status": {"$in": list(ACTIVE_STATUSES)}})


async def _count_units_available() -> int:
    db = get_db()
    return await db["units"].count_documents({"status": "available"})


async def _count_resolved_in_window(window_hours: int) -> int:
    """
    Counts distinct incidents that reached 'resolved' within the time window,
    using the assignments timeline (more accurate than reported_at).
    """
    db = get_db()
    since = _iso(_now_utc() - timedelta(hours=window_hours))
    pipeline = [
        {"$match": {"status": "resolved", "at": {"$gte": since}}},
        {"$group": {"_id": "$incident_id"}},
        {"$count": "count"},
    ]
    agg = db["assignments"].aggregate(pipeline)
    doc = await agg.to_list(length=1)
    return int(doc[0]["count"]) if doc else 0


async def _avg_response_minutes(window_hours: int) -> float:
    """
    Average time from first 'accepted' → first 'arrived' per incident,
    considering only events whose timeline updates fall inside the window.
    If no paired timelines exist, returns 0.0.
    """
    db = get_db()
    since_dt = _now_utc() - timedelta(hours=window_hours)
    since_iso = _iso(since_dt)

    # Fetch relevant timeline updates in the window
    cursor = db["assignments"].find(
        {
            "status": {"$in": list(RESPONSE_PAIR)},
            "at": {"$gte": since_iso},
        },
        {"incident_id": 1, "status": 1, "at": 1, "_id": 0},
    )

    # Build first-accepted and first-arrived per incident
    pairs: Dict[str, Dict[str, datetime]] = {}
    async for doc in cursor:
        inc_id = doc["incident_id"]
        status = doc["status"]
        at = datetime.fromisoformat(doc["at"].replace("Z", "+00:00")).astimezone(timezone.utc)
        if inc_id not in pairs:
            pairs[inc_id] = {}
        # keep earliest timestamp for each status
        if status not in pairs[inc_id] or at < pairs[inc_id][status]:
            pairs[inc_id][status] = at

    # Compute diffs (accepted -> arrived) in minutes
    total = 0.0
    n = 0
    for inc_id, times in pairs.items():
        if RESPONSE_PAIR[0] in times and RESPONSE_PAIR[1] in times:
            delta = (times[RESPONSE_PAIR[1]] - times[RESPONSE_PAIR[0]]).total_seconds() / 60.0
            if delta >= 0:
                total += delta
                n += 1

    return round(total / n, 1) if n else 0.0


async def metrics_tiles(window_hours: int = 24) -> dict:
    """
    Returns telemetry tiles for the dashboard.
      - active: incidents in NEW/ACCEPTED/ENROUTE/ARRIVED
      - resolved_window: incidents resolved within the last `window_hours`
      - units_available: units with status=available
      - avg_response_min: average minutes from ACCEPTED to ARRIVED
    """
    active, units_avail = await _count_active_incidents(), await _count_units_available()
    resolved = await _count_resolved_in_window(window_hours)
    avg_resp = await _avg_response_minutes(window_hours)

    return {
        "active": int(active),
        "resolved_window": int(resolved),
        "units_available": int(units_avail),
        "avg_response_min": float(avg_resp),
        "window_hours": int(window_hours),
    }
