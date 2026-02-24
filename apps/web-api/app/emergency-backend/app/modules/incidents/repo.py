from __future__ import annotations
from typing import Optional, List, Dict, Any
from bson import ObjectId
from math import radians, cos, sin, asin, sqrt

from app.db.mongo import get_db
from app.modules.responders.repo import get_user_by_email, get_user, get_responders_by_role


def calculate_distance(lat1, lon1, lat2, lon2):
    """Returns distance in km between two points using Haversine formula"""
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
        return 999999 
        
    try:
        lon1, lat1, lon2, lat2 = map(radians, [float(lon1), float(lat1), float(lon2), float(lat2)])
        dlon = lon2 - lon1 
        dlat = lat2 - lat1 
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a)) 
        r = 6371 
        return c * r
    except (ValueError, TypeError):
        return 999999


def _norm(doc: dict) -> dict:
    if not doc:
        return doc
    out = dict(doc)
    out["id"] = str(out["_id"])
    out.pop("_id", None)
    return out


async def insert_incident(doc: dict) -> str:
    db = get_db()
    res = await db["incidents"].insert_one(doc)
    return str(res.inserted_id)


async def get_incident(incident_id: str) -> Optional[dict]:
    db = get_db()
    try:
        doc = await db["incidents"].find_one({"_id": ObjectId(incident_id)})
        return _norm(doc) if doc else None
    except:
        return None


async def find_nearby_active_incident(
    lat: float, 
    lng: float, 
    source: str, 
    max_distance_m: int = 150 
) -> Optional[dict]:
    """
    NOVELTY FEATURE: Spatiotemporal Clustering.
    Finds an existing active OR unverified incident to merge duplicate reports.
    INCLUDES FALLBACK if MongoDB Index is missing.
    """
    db = get_db()
    
    active_statuses = ["unverified", "new", "accepted", "enroute", "arrived"]
    
    try:
        query = {
            "status": {"$in": active_statuses}, 
            "source": source, 
            "location": {
                "$near": {
                    "$geometry": {
                        "type": "Point",
                        "coordinates": [lng, lat]
                    },
                    "$maxDistance": max_distance_m
                }
            }
        }
        doc = await db["incidents"].find_one(query)
        if doc:
            return _norm(doc)
            
    except Exception as e:
        pass
    try:
        fallback_query = {
            "status": {"$in": active_statuses},
            "source": source
        }
        
        cursor = db["incidents"].find(fallback_query).sort("timestamp_utc", -1).limit(50)
        
        async for doc in cursor:
            doc_lat = doc.get("location", {}).get("lat")
            doc_lng = doc.get("location", {}).get("lng")
            
            dist_km = calculate_distance(lat, lng, doc_lat, doc_lng)
            dist_m = dist_km * 1000.0
            
            if dist_m <= max_distance_m:
                return _norm(doc)
                
    except Exception:
        pass
        
    return None


async def update_incident(incident_id: str, patch: dict) -> None:
    db = get_db()
    await db["incidents"].update_one({"_id": ObjectId(incident_id)}, {"$set": patch})


async def delete_incident(incident_id: str) -> None:
    db = get_db()
    await db["incidents"].delete_one({"_id": ObjectId(incident_id)})


async def enrich_incident_with_responders(doc: dict) -> dict:
    statuses = doc.get("responder_statuses", {})
    if not statuses:
        doc["assigned_responders"] = []
        return doc
    
    enriched = []
    for uid, status in statuses.items():
        u = await get_user(uid)
        if u:
            enriched.append({
                "id": u["id"],
                "name": u.get("name", "Unknown"),
                "email": u.get("email"),
                "role": u.get("role"),
                "status": status,
                "location": u.get("location") 
            })
    
    doc["assigned_responders"] = enriched
    return doc


async def list_queue(
    limit: int = 50,
    role: Optional[str] = None,
    user_location: Optional[dict] = None,
    status: str = "active",
    user_id: Optional[str] = None
) -> List[Dict]:
    
    db = get_db()
    
    if role == "admin":
        cursor = (
            db["incidents"]
            .find({})
            .sort([("score", -1), ("reported_at", -1)])
            .limit(limit * 2) 
        )
        
        results = []
        async for doc in cursor:
            d = _norm(doc)
            await enrich_incident_with_responders(d)
            
            required = d.get("required_roles", [])
            role_stats = d.get("role_statuses", {})
            
            pending = [r for r in required if role_stats.get(r) != "resolved"]
            d["pending_responder_roles"] = pending
            
            if len(pending) == 0 and len(required) > 0:
                admin_view_status = "resolved"
            else:
                admin_view_status = "active"

            if status == "resolved":
                if admin_view_status == "resolved":
                    d["status"] = "resolved"
                    results.append(d)
            else: 
                if admin_view_status != "resolved":
                    d["status"] = "active"
                    results.append(d)

        return results[:limit]
    
    if status == "resolved":
        query = {f"responder_statuses.{user_id}": "resolved"}
        cursor = db["incidents"].find(query).sort([("reported_at", -1)]).limit(limit)
        results = []
        async for x in cursor:
            d = _norm(x)
            d["status"] = "resolved"
            results.append(d)
        return results

    if status == "active":
        query = {
            "$or": [
                {f"responder_statuses.{user_id}": {"$in": ["accepted", "enroute", "arrived"]}},
                {
                    f"responder_statuses.{user_id}": {"$exists": False},
                    "required_roles": role,
                    "status": {"$ne": "resolved"}
                }
            ]
        }
        
        cursor = db["incidents"].find(query).sort([("score", -1)]).limit(limit)
        peers = []
        if role:
            peers = await get_responders_by_role(role)
        
        results = []
        async for doc in cursor:
            d = _norm(doc)
            user_status = d.get("responder_statuses", {}).get(user_id)
            
            if user_status:
                d["status"] = user_status
                results.append(d)
                continue
            
            inc_loc = d.get("location", {})
            my_lat = user_location.get("lat") if user_location else None
            my_lng = user_location.get("lng") if user_location else None
            my_dist = calculate_distance(my_lat, my_lng, inc_loc.get("lat"), inc_loc.get("lng"))
            
            is_nearest = True
            for peer in peers:
                if peer["id"] == user_id: continue 
                peer_loc = peer.get("location", {})
                peer_dist = calculate_distance(
                    peer_loc.get("lat"), peer_loc.get("lng"),
                    inc_loc.get("lat"), inc_loc.get("lng")
                )
                if peer_dist < my_dist:
                    is_nearest = False
                    break
            
            if is_nearest:
                d["status"] = "new"
                results.append(d)
            
        return results
    
    return []