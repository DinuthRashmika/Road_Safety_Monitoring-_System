from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends, Query
from app.modules.routing import eta as eta_adapter, route as route_adapter
from app.db.mongo import get_db
from app.security.roles import require_roles
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

@router.get("/incidents/{incident_id}/eta", dependencies=[Depends(require_roles("police","ambulance","fire","admin"))])
async def incident_eta(incident_id: str, unit_id: str = Query(...)):
    db = get_db()
    inc = await db["incidents"].find_one({"_id": ObjectId(incident_id)})
    if not inc: raise HTTPException(404, "Incident not found")
    loc = inc.get("location") or {}
    unit = await db["units"].find_one({"_id": ObjectId(unit_id)})
    if not unit: raise HTTPException(404, "Unit not found")
    return await eta_adapter(float(unit["home_lat"]), float(unit["home_lng"]), float(loc["lat"]), float(loc["lng"]))

@router.get("/incidents/{incident_id}/route", dependencies=[Depends(require_roles("police","ambulance","fire","admin"))])
async def incident_route(incident_id: str, unit_id: str = Query(...)):
    db = get_db()
    inc = await db["incidents"].find_one({"_id": ObjectId(incident_id)})
    if not inc: raise HTTPException(404, "Incident not found")
    loc = inc.get("location") or {}
    unit = await db["units"].find_one({"_id": ObjectId(unit_id)})
    if not unit: raise HTTPException(404, "Unit not found")
    return await route_adapter(float(unit["home_lat"]), float(unit["home_lng"]), float(loc["lat"]), float(loc["lng"]))
