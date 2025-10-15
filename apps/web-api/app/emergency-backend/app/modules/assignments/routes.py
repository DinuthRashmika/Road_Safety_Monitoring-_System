from fastapi import APIRouter, HTTPException
from .service import record_status

router = APIRouter()

@router.post("/assignments/record")
async def record(body: dict):
    inc = body.get("incident_id"); unit = body.get("unit_id"); status = body.get("status")
    if not all([inc, unit, status]):
        raise HTTPException(400, "incident_id, unit_id, status required")
    await record_status(inc, unit, status)
    return {"ok": True}
