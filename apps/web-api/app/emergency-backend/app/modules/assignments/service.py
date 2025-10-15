from datetime import datetime, timezone
from .repo import append_timeline

async def record_status(incident_id: str, unit_id: str, status: str):
    await append_timeline(incident_id, unit_id, status, datetime.now(timezone.utc).isoformat())
