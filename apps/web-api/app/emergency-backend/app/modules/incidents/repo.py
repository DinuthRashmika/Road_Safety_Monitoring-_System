from __future__ import annotations
from typing import Optional, List, Dict, Any
from bson import ObjectId
from math import radians, cos, sin, asin, sqrt

from app.db.mongo import get_db
# Import the new function we just added
from app.modules.responders.repo import get_user_by_email, get_user, get_responders_by_role


def calculate_distance(lat1, lon1, lat2, lon2):
    """Returns distance in km between two points using Haversine formula"""
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
        return 999999 # Treat as infinite if location missing
        
    try:
        lon1, lat1, lon2, lat2 = map(radians, [float(lon1), float(lat1), float(lon2), float(lat2)])
        dlon = lon2 - lon1 
        dlat = lat2 - lat1 
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a)) 
        r = 6371 # Radius of earth in kilometers
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
    doc = await db["incidents"].find_one({"_id": ObjectId(incident_id)})
    return _norm(doc) if doc else None


async def update_incident(incident_id: str, patch: dict) -> None:
    db = get_db()
    await db["incidents"].update_one({"_id": ObjectId(incident_id)}, {"$set": patch})


async def delete_incident(incident_id: str) -> None:
    db = get_db()
    await db["incidents"].delete_one({"_id": ObjectId(incident_id)})


async def list_queue(
    limit: int = 50,
    role: Optional[str] = None,
    user_location: Optional[dict] = None,
    status: str = "active",
    user_id: Optional[str] = None
) -> List[Dict]:
    
    db = get_db()
    
    # --- ADMIN LOGIC ---
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
            
            # Calculate Pending Roles
            required = d.get("required_roles", [])
            role_stats = d.get("role_statuses", {})
            
            pending = [r for r in required if role_stats.get(r) != "resolved"]
            d["pending_responder_roles"] = pending
            
            # Determine Global Admin Status
            if len(pending) == 0 and len(required) > 0:
                admin_view_status = "resolved"
            else:
                admin_view_status = "active"

            # Filter based on requested status
            if status == "resolved":
                if admin_view_status == "resolved":
                    d["status"] = "resolved"
                    results.append(d)
            else: 
                # status == "active"
                if admin_view_status != "resolved":
                    d["status"] = "active"
                    results.append(d)

        return results[:limit]
    
    # --- RESPONDER LOGIC ---
    
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
        # 1. Fetch relevant incidents:
        #    A. Already accepted/enroute/arrived by THIS user (Always show these)
        #    B. "New" incidents requiring this user's role (Subject to distance check)
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
        
        # 2. Pre-fetch peers to avoid DB calls inside the loop
        peers = []
        if role:
            peers = await get_responders_by_role(role)
        
        results = []
        async for doc in cursor:
            d = _norm(doc)
            user_status = d.get("responder_statuses", {}).get(user_id)
            
            # Case A: User has already acted on it. Always show it so they can finish the job.
            if user_status:
                d["status"] = user_status
                results.append(d)
                continue
            
            # Case B: It is "New" (no status for this user). 
            # Check if I am the NEAREST unit of my type.
            
            inc_loc = d.get("location", {})
            
            # Calculate my distance
            my_lat = user_location.get("lat") if user_location else None
            my_lng = user_location.get("lng") if user_location else None
            
            my_dist = calculate_distance(
                my_lat, my_lng, 
                inc_loc.get("lat"), inc_loc.get("lng")
            )
            
            is_nearest = True
            
            # Compare against all other peers of the same role
            for peer in peers:
                if peer["id"] == user_id: 
                    continue # Skip myself
                
                peer_loc = peer.get("location", {})
                peer_dist = calculate_distance(
                    peer_loc.get("lat"), peer_loc.get("lng"),
                    inc_loc.get("lat"), inc_loc.get("lng")
                )
                
                # If another peer is strictly closer, I am not the nearest.
                # (If distances are equal, we keep is_nearest=True so at least one person sees it)
                if peer_dist < my_dist:
                    is_nearest = False
                    break
            
            # Only add to results if I am the nearest unit
            if is_nearest:
                d["status"] = "new"
                results.append(d)
            
        return results
    
    return []