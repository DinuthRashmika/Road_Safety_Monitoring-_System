from __future__ import annotations
from typing import Optional

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
async def get_incident_route(
    incident_id: str,
    responder: dict = Depends(get_current_responder_doc)
):
    inc = await get_incident(incident_id)
    if not inc:
        raise HTTPException(404, "Not found")
    
    user_id = responder.get("id")
    role = responder.get("role")

    if role == "admin":
        required = inc.get("required_roles", [])
        role_stats = inc.get("role_statuses", {})
        
        pending = [r for r in required if role_stats.get(r) != "resolved"]
        inc["pending_responder_roles"] = pending
        
        if len(pending) == 0 and len(required) > 0:
            inc["status"] = "resolved"
        elif inc.get("status") != "unverified":
            inc["status"] = "active"

    else:
        user_status = inc.get("responder_statuses", {}).get(user_id)
        
        if user_status:
            inc["status"] = user_status
        elif role in inc.get("required_roles", []) and not user_status:
            inc["status"] = "new"
            
    return inc

@router.post(
    "/incidents/{incident_id}/accept"
)
async def accept_route(incident_id: str, responder: dict = Depends(get_current_responder_doc)):
    responder_id = responder.get("id")
    responder_role = responder.get("role")
    
    await accept_incident(incident_id, responder_id)

    await update_incident(incident_id, {
        f"role_statuses.{responder_role}": "accepted"
    })
    
    updated_doc = await get_incident(incident_id)
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
    responder_role = responder.get("role")

    cur = await get_incident(incident_id)
    if not cur:
        raise HTTPException(404, "Not found")
    
    current_user_status = cur.get("responder_statuses", {}).get(responder_id, "new")

    if not can_transition(current_user_status, new_status):
        raise HTTPException(400, f"Invalid transition {current_user_status} -> {new_status}")
    
    updates = {
        f"responder_statuses.{responder_id}": new_status,
        f"role_statuses.{responder_role}": new_status
    }
    
    await update_incident(incident_id, updates)
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