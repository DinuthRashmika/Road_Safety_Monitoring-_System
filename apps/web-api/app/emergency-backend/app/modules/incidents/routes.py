from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from app.security.roles import require_roles
from app.utils.sse import event_stream
from .repo import list_queue, get_incident, update_incident
from .service import accept_incident
from .status import can_transition
from .broadcast import get_queue

router = APIRouter()

@router.get("/incidents/queue")
async def get_queue_route(limit: int = 50):
    return await list_queue(limit=limit)

@router.get("/incidents/{incident_id}")
async def get_incident_route(incident_id: str):
    inc = await get_incident(incident_id)
    if not inc:
        raise HTTPException(404, "Not found")
    inc["id"] = str(inc["_id"])
    del inc["_id"]
    return inc

@router.post("/incidents/{incident_id}/accept", dependencies=[Depends(require_roles("police","ambulance","fire","admin"))])
async def accept_route(incident_id: str, body: dict):
    unit_id = body.get("unit_id")
    if not unit_id:
        raise HTTPException(400, "unit_id required")
    await accept_incident(incident_id, unit_id)
    return {"ok": True}

@router.post("/incidents/{incident_id}/status", dependencies=[Depends(require_roles("police","ambulance","fire","admin"))])
async def status_route(incident_id: str, body: dict):
    new_status = body.get("status")
    from .repo import get_incident
    cur = await get_incident(incident_id)
    if not cur:
        raise HTTPException(404, "Not found")
    if not can_transition(cur["status"], new_status):
        raise HTTPException(400, f"Invalid transition {cur['status']} -> {new_status}")
    await update_incident(incident_id, {"status": new_status})
    return {"ok": True}

@router.get("/stream/incidents")
async def stream_incidents():
    q = get_queue()
    return StreamingResponse(event_stream(q), media_type="text/event-stream")
