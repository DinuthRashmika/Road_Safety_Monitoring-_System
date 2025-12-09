from __future__ import annotations
from typing import Optional, List, Dict, Any
from bson import ObjectId
from app.db.mongo import get_db
from app.modules.responders.repo import get_user_by_email, get_user


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
        # Admin needs to see items based on Multi-Responder Resolution
        
        # 1. Fetch EVERYTHING (filtered by limit) to process in Python 
        #    (Optimization: In production, use Aggregation Pipeline, but this is safer for logic)
        cursor = (
            db["incidents"]
            .find({})
            .sort([("score", -1), ("reported_at", -1)])
            .limit(limit * 2) # Fetch extra to filter
        )
        
        results = []
        async for doc in cursor:
            d = _norm(doc)
            
            # Calculate Pending Roles
            required = d.get("required_roles", [])
            role_stats = d.get("role_statuses", {})
            
            # A role is pending if it is NOT "resolved" in the role_statuses map
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
                    # It's active if even one person is pending
                    d["status"] = "active"
                    results.append(d)

        return results[:limit]
    
    # --- RESPONDER LOGIC (Unchanged) ---
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
        
        results = []
        async for doc in cursor:
            d = _norm(doc)
            user_status = d.get("responder_statuses", {}).get(user_id)
            d["status"] = user_status if user_status else "new"
            results.append(d)
            
        return results
    
    return []