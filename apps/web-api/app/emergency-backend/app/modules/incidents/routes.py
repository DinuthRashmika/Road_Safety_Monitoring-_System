from __future__ import annotations
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

# Removed 'get_current_user_token' which caused the error
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
async def get_incident_route(
    incident_id: str,
    # This dependency will ensure the user is logged in
    responder: dict = Depends(get_current_responder_doc)
):
    inc = await get_incident(incident_id)
    if not inc:
        raise HTTPException(404, "Not found")
    
    # If a responder is requesting this, show THEIR status
    if responder:
        user_id = responder.get("id")
        user_status = inc.get("responder_statuses", {}).get(user_id)
        
        # If they have a specific status, show it (e.g., 'accepted')
        if user_status:
            inc["status"] = user_status
        # If they are required but haven't accepted, show 'new' instead of global status
        elif responder.get("role") in inc.get("required_roles", []) and not user_status:
            inc["status"] = "new"
            
    return inc

@router.post(
    "/incidents/{incident_id}/accept"
)
async def accept_route(incident_id: str, responder: dict = Depends(get_current_responder_doc)):
    responder_id = responder.get("id")
    
    # This now updates the user-specific status map
    await accept_incident(incident_id, responder_id)
    
    # Fetch updated and project status
    updated_doc = await get_incident(incident_id)
    if not updated_doc:
        raise HTTPException(404, "Incident not found after accept")
    
    # Return the doc with the status explicitly set to accepted for the UI
    updated_doc["status"] = "accepted"
        
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
    responder_id = responder.get("id")

    cur = await get_incident(incident_id)
    if not cur:
        raise HTTPException(404, "Not found")
    
    # Get current status specifically for this responder
    current_user_status = cur.get("responder_statuses", {}).get(responder_id, "new")

    if not can_transition(current_user_status, new_status):
        raise HTTPException(400, f"Invalid transition {current_user_status} -> {new_status}")
    
    # Update ONLY this responder's status
    await update_incident(incident_id, {f"responder_statuses.{responder_id}": new_status})
    
    await record_status(incident_id, responder_id, new_status)
    
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