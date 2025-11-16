from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.deps import get_current_responder_doc, require_roles
from app.utils.sse import event_stream
from .repo import list_queue, get_incident, update_incident
from .service import accept_incident
from .status import can_transition
from .broadcast import get_queue

router = APIRouter()


@router.get("/incidents/queue")
async def get_queue_route(
    limit: int = 50,
    responder: dict = Depends(get_current_responder_doc), 
):
    """
    Role-aware, location-aware queue:
      - admin: all 'new' incidents sorted by score
      - police/ambulance/fire: only incidents near them that require their role
    """
    role = responder.get("role")
    location = responder.get("location")
    
    return await list_queue(limit=limit, role=role, user_location=location)


@router.get("/incidents/{incident_id}")
async def get_incident_route(incident_id: str):
    inc = await get_incident(incident_id)
    if not inc:
        raise HTTPException(404, "Not found")
    return inc


@router.post(
    "/incidents/{incident_id}/accept",
    dependencies=[Depends(require_roles("police", "ambulance", "fire", "admin"))],
)
async def accept_route(incident_id: str, responder: dict = Depends(get_current_responder_doc)):
    """
    Accept an incident. The system knows who the responder is from their token.
    """
    responder_id = responder.get("id")
    await accept_incident(incident_id, responder_id)
    return {"ok": True}


@router.post(
    "/incidents/{incident_id}/status",
    dependencies=[Depends(require_roles("police", "ambulance", "fire", "admin"))],
)
async def status_route(incident_id: str, body: dict):
    new_status = body.get("status")
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