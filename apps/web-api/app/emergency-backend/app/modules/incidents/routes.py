from __future__ import annotations
from asyncio.log import logger
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

from app.deps import get_current_responder_doc, require_roles
from app.utils.sse import event_stream
from .repo import list_queue, get_incident, update_incident, delete_incident, enrich_incident_with_responders
from .service import accept_incident
from .status import can_transition
from .broadcast import get_queue
from app.modules.assignments.service import record_status 
from app.modules.routing import route as route_adapter
from app.db.mongo import get_db
from bson import ObjectId

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

        await enrich_incident_with_responders(inc)

    else:
        user_status = inc.get("responder_statuses", {}).get(user_id)
        
        if user_status:
            inc["status"] = user_status
        elif role in inc.get("required_roles", []) and not user_status:
            inc["status"] = "new"
            
    return inc

@router.post("/incidents/{incident_id}/accept")
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

@router.get("/incidents/{incident_id}/route")
async def get_incident_route_calculated(
    incident_id: str,
    responder: dict = Depends(get_current_responder_doc)
):
    """Get route from responder to incident - works for all incident types including violence"""
    db = get_db()
    
    # Get incident
    try:
        incident = await db["incidents"].find_one({"_id": ObjectId(incident_id)})
    except:
        incident = await db["incidents"].find_one({"id": incident_id})
    
    if not incident:
        raise HTTPException(404, "Incident not found")
    
    # Get responder location
    resp_loc = responder.get("location")
    if not resp_loc or not resp_loc.get("lat") or not resp_loc.get("lng"):
        # Use default responder location if not set
        resp_loc = {"lat": 6.9271, "lng": 79.8612, "address": "Default Location"}
        logger.warning(f"Responder has no location, using default")
    
    # Get incident location
    inc_loc = incident.get("location", {})
    if not inc_loc or not inc_loc.get("lat") or not inc_loc.get("lng"):
        # For incidents without coordinates, use default based on address
        logger.warning(f"Incident {incident_id} has no coordinates, using address-based default")
        address = inc_loc.get("address", "Unknown").lower()
        
        # Default coordinates based on common locations
        if "matara" in address:
            inc_loc = {"lat": 5.9549, "lng": 80.5550, "address": address}
        elif "galle" in address:
            inc_loc = {"lat": 6.0319, "lng": 80.2168, "address": address}
        elif "colombo" in address:
            inc_loc = {"lat": 6.9271, "lng": 79.8612, "address": address}
        else:
            inc_loc = {"lat": 6.9271, "lng": 79.8612, "address": address}
    
    logger.info(f"Calculating route from {resp_loc} to {inc_loc}")
    
    # Calculate route
    try:
        route_data = await route_adapter(
            float(resp_loc["lat"]), float(resp_loc["lng"]),
            float(inc_loc["lat"]), float(inc_loc["lng"])
        )
        
        # Add incident info to route data
        route_data["incident_id"] = incident_id
        route_data["incident_address"] = inc_loc.get("address", "Unknown")
        route_data["responder_address"] = resp_loc.get("address", "Unknown")
        route_data["start"] = resp_loc
        route_data["end"] = inc_loc
        
        return route_data
        
    except Exception as e:
        logger.error(f"Route calculation failed: {e}")
        raise HTTPException(500, f"Route calculation failed: {str(e)}")

@router.post("/incidents/{incident_id}/status")
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