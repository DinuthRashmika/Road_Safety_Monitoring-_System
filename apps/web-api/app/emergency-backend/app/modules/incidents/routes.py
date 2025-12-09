from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

from app.deps import get_current_responder_doc, require_roles
from app.utils.sse import event_stream
from .repo import list_queue, get_incident, update_incident, delete_incident
from .service import accept_incident
from .status import can_transition
from .broadcast import get_queue
from app.modules.assignments.service import record_status 

router = APIRouter()

@router.get("/incidents/queue")
async def get_queue_route(
    limit: int = 50,
    status: str = Query("active"), 
    responder: dict = Depends(get_current_responder_doc),
):
    role = responder.get("role")
    location = responder.get("location")
    user_id = responder.get("id") 
    
    return await list_queue(
        limit=limit, 
        role=role, 
        user_location=location, 
        status=status,
        user_id=user_id 
    )


@router.get("/incidents/{incident_id}")
async def get_incident_route(incident_id: str):
    inc = await get_incident(incident_id)
    if not inc:
        raise HTTPException(404, "Not found")
    return inc

@router.post(
    "/incidents/{incident_id}/accept"
)
async def accept_route(incident_id: str, responder: dict = Depends(get_current_responder_doc)):
    responder_id = responder.get("id")
    await accept_incident(incident_id, responder_id)
    
    updated_doc = await get_incident(incident_id)
    if not updated_doc:
        raise HTTPException(404, "Incident not found after accept")
        
    return updated_doc


@router.post(
    "/incidents/{incident_id}/status"
)
async def status_route(
    incident_id: str, 
    body: dict, 
    responder: dict = Depends(get_current_responder_doc) 
):
    new_status = body.get("status")
    cur = await get_incident(incident_id)
    if not cur:
        raise HTTPException(404, "Not found")
    if not can_transition(cur["status"], new_status):
        raise HTTPException(400, f"Invalid transition {cur['status']} -> {new_status}")
    
    await update_incident(incident_id, {"status": new_status})
    
    action_by_responder_id = responder.get("id")
    
    await record_status(incident_id, action_by_responder_id, new_status)
    
    return {"ok": True}


@router.delete(
    "/incidents/{incident_id}",
    dependencies=[Depends(require_roles("admin"))], 
)
async def delete_incident_route(incident_id: str):
    await delete_incident(incident_id)
    return {"ok": True}


@router.get("/stream/incidents")
async def stream_incidents():
    q = get_queue()
    return StreamingResponse(event_stream(q), media_type="text/event-stream")