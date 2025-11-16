from datetime import datetime, timezone
from .repo import append_timeline

async def record_status(incident_id: str, responder_id: str, status: str): 
    await append_timeline(incident_id, responder_id, status, datetime.now(timezone.utc).isoformat())