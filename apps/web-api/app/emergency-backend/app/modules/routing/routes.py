from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends, Query
from app.modules.routing import eta as eta_adapter, route as route_adapter
from app.db.mongo import get_db
from app.deps import get_current_responder_doc
from bson import ObjectId

router = APIRouter()

@router.get("/routing/eta")
async def routing_eta(
    from_lat: float = Query(...),
    from_lng: float = Query(...),
    to_lat: float = Query(...),
    to_lng: float = Query(...),
):
    return await eta_adapter(from_lat, from_lng, to_lat, to_lng)

@router.get("/routing/route")
async def routing_route(
    from_lat: float = Query(...),
    from_lng: float = Query(...),
    to_lat: float = Query(...),
    to_lng: float = Query(...),
):
    return await route_adapter(from_lat, from_lng, to_lat, to_lng)

async def _get_locations(incident_id: str, current_responder: dict) -> tuple[dict, dict]:
    """
    Helper to get start (responder) and end (incident) locations.
    Uses the CURRENT user as the start point, allowing route preview before assignment.
    """
    db = get_db()
    inc = await db["incidents"].find_one({"_id": ObjectId(incident_id)})
    if not inc:
        raise HTTPException(404, "Incident not found")
    
    resp_loc = current_responder.get("location") or {}
    
    inc_loc = inc.get("location") or {}
    
    if not all([inc_loc.get("lat"), inc_loc.get("lng"), resp_loc.get("lat"), resp_loc.get("lng")]):
         raise HTTPException(400, "Your profile or the incident is missing GPS coordinates")
         
    return resp_loc, inc_loc


@router.get("/incidents/{incident_id}/eta")
async def incident_eta(
    incident_id: str, 
    responder: dict = Depends(get_current_responder_doc)
):
    resp_loc, inc_loc = await _get_locations(incident_id, responder)
    
    return await eta_adapter(
        float(resp_loc["lat"]), float(resp_loc["lng"]),
        float(inc_loc["lat"]), float(inc_loc["lng"])
    )

@router.get("/incidents/{incident_id}/route")
async def incident_route(
    incident_id: str,
    responder: dict = Depends(get_current_responder_doc)
):
    resp_loc, inc_loc = await _get_locations(incident_id, responder)
    
    return await route_adapter(
        float(resp_loc["lat"]), float(resp_loc["lng"]),
        float(inc_loc["lat"]), float(inc_loc["lng"])
    )