# app/modules/telemetry/metrics.py
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from typing import Dict, Tuple
from app.db.mongo import get_db

# ... (other code is the same) ...

async def _count_active_incidents() -> int:
    db = get_db()
    return await db["incidents"].count_documents({"status": {"$in": list(ACTIVE_STATUSES)}})

# async def _count_units_available() -> int:  <-- REMOVED
#     db = get_db()
#     return await db["units"].count_documents({"status": "available"})

# ... (other code is the same) ...

async def metrics_tiles(window_hours: int = 24) -> dict:
    """
    Returns telemetry tiles for the dashboard.
      - active: incidents in NEW/ACCEPTED/ENROUTE/ARRIVED
      - resolved_window: incidents resolved within the last `window_hours`
      - avg_response_min: average minutes from ACCEPTED to ARRIVED
    """
    active = await _count_active_incidents()
    resolved = await _count_resolved_in_window(window_hours)
    avg_resp = await _avg_response_minutes(window_hours)

    return {
        "active": int(active),
        "resolved_window": int(resolved),
        # "units_available": int(units_avail), <-- REMOVED
        "avg_response_min": float(avg_resp),
        "window_hours": int(window_hours),
    }