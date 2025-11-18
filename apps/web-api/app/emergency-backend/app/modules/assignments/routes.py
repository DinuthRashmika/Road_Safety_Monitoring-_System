from fastapi import APIRouter, HTTPException
from .service import record_status

router = APIRouter()

@router.post("/assignments/record")
async def record(body: dict):
    inc = body.get("incident_id")
    resp_id = body.get("responder_id") # Changed from unit_id
    status = body.get("status")
    
    if not all([inc, resp_id, status]):
        raise HTTPException(400, "incident_id, responder_id, and status are required")
        
    await record_status(inc, resp_id, status)
    return {"ok": True}