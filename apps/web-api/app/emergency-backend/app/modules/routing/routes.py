from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends, Query
from app.modules.routing import eta as eta_adapter, route as route_adapter
from app.db.mongo import get_db
from app.security.roles import require_roles
from bson import ObjectId
from app.modules.responders.repo import get_user

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

async def _get_responder_and_incident_locations(incident_id: str) -> tuple[dict, dict]:
    """Helper to get incident location and assigned responder's location."""
    db = get_db()
    inc = await db["incidents"].find_one({"_id": ObjectId(incident_id)})
    if not inc:
        raise HTTPException(404, "Incident not found")
    
    responder_id = inc.get("assignee_responder_id")
    if not responder_id:
        raise HTTPException(400, "Incident has not been assigned to a responder")
        
    responder = await get_user(responder_id)
    if not responder:
        raise HTTPException(404, "Assigned responder not found")

    inc_loc = inc.get("location") or {}
    resp_loc = responder.get("location") or {}
    
    if not all([inc_loc.get("lat"), inc_loc.get("lng"), resp_loc.get("lat"), resp_loc.get("lng")]):
         raise HTTPException(400, "Incident or responder is missing location data")
         
    return resp_loc, inc_loc


@router.get("/incidents/{incident_id}/eta", dependencies=[Depends(require_roles("police","ambulance","fire","admin"))])
async def incident_eta(incident_id: str):
    resp_loc, inc_loc = await _get_responder_and_incident_locations(incident_id)
    return await eta_adapter(
        float(resp_loc["lat"]), float(resp_loc["lng"]),
        float(inc_loc["lat"]), float(inc_loc["lng"])
    )

@router.get("/incidents/{incident_id}/route", dependencies=[Depends(require_roles("police","ambulance","fire","admin"))])
async def incident_route(incident_id: str):
    resp_loc, inc_loc = await _get_responder_and_incident_locations(incident_id)
    return await route_adapter(
        float(resp_loc["lat"]), float(resp_loc["lng"]),
        float(inc_loc["lat"]), float(inc_loc["lng"])
    )