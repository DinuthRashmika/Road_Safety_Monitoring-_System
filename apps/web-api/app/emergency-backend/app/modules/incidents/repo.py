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
    """Deletes a single incident by its ID."""
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
    
    # "Active" means the responder is working on it, OR it's new and waiting for them.
    
    if role == "admin":
        # Admin sees the raw global view
        if status == "active":
             # Show anything not resolved globally (simplified for admin)
            query: dict = {"status": {"$ne": "resolved"}}
        else:
            query: dict = {"status": status}

        cursor = (
            db["incidents"]
            .find(query)
            .sort([("score", -1), ("reported_at", -1)])
            .limit(limit)
        )
        return [_norm(x) async for x in cursor]
    
    # --- Responder Logic (Police, Fire, Ambulance) ---

    if status == "resolved":
        # Fetch incidents where THIS user specifically marked it as resolved
        query = {
            f"responder_statuses.{user_id}": "resolved"
        }
        cursor = (
            db["incidents"]
            .find(query)
            .sort([("reported_at", -1)])
            .limit(limit)
        )
        
        results = []
        async for x in cursor:
            d = _norm(x)
            d["status"] = "resolved" # Force status for frontend view
            results.append(d)
        return results

    if status == "active":
        # It is active for a user if:
        # 1. They have ALREADY accepted/enroute/arrived (it is in their status map)
        # 2. OR It is "New" (User not in map) AND their role is required.
        
        query = {
            "$or": [
                # Case A: User has interacted and it is NOT resolved
                {f"responder_statuses.{user_id}": {"$in": ["accepted", "enroute", "arrived"]}},
                
                # Case B: User has NOT interacted (field missing) AND role is required
                {
                    f"responder_statuses.{user_id}": {"$exists": False},
                    "required_roles": role,
                    "status": {"$ne": "resolved"} # Optional: Ensure global incident isn't dead
                }
            ]
        }
        
        cursor = (
            db["incidents"]
            .find(query)
            .sort([("score", -1)])
            .limit(limit)
        )
        
        # Post-process to inject the correct "status" for the frontend
        results = []
        async for doc in cursor:
            d = _norm(doc)
            
            # Check this specific user's status
            user_status = d.get("responder_statuses", {}).get(user_id)
            
            if user_status:
                d["status"] = user_status
            else:
                # If they haven't touched it, it appears as "new" to them
                d["status"] = "new"
                
            results.append(d)
            
        return results
    
    return []