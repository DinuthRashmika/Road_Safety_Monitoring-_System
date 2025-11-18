# app/modules/incidents/repo.py
from __future__ import annotations
from typing import Optional, List, Dict
from bson import ObjectId
from app.db.mongo import get_db
from app.modules.responders.repo import get_user_by_email, get_user


def _norm(doc: dict) -> dict:
    """Convert Mongo _id to 'id' and drop raw ObjectId."""
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
    
    active_statuses = ["new", "accepted", "enroute", "arrived"]
    
    # --- Admin View (Unchanged) ---
    if role == "admin":
        if status == "active":
            query: dict = {"status": {"$in": active_statuses}}
        else:
            query: dict = {"status": status} # e.g., "resolved"

        cursor = (
            db["incidents"]
            .find(query)
            .sort([("score", -1), ("reported_at", -1)])
            .limit(limit)
        )
        return [_norm(x) async for x in cursor]

    # --- Responder View (Logic is now changed) ---
    
    # 1. For "resolved" incidents (History Page - Unchanged)
    if status == "resolved":
        query = {
            "status": "resolved",
            "assignee_responder_id": user_id 
        }
        cursor = (
            db["incidents"]
            .find(query)
            .sort([("reported_at", -1)]) 
            .limit(limit)
        )
        return [_norm(x) async for x in cursor]

    # 2. For "active" incidents (Dashboard Queue - THIS IS THE FIX)
    if status == "active":
        
        # We removed the $geoNear pipeline.
        # This query is now simple and finds all relevant incidents.
        query = {
            "status": {"$in": active_statuses},
            # Find incidents that are either NEW and need this role
            # OR are already assigned to YOU.
            "$or": [
                {"status": "new", "required_roles": {"$in": [role]}},
                {"assignee_responder_id": user_id}
            ]
        }
        cursor = (
            db["incidents"]
            .find(query)
            .sort([("score", -1)]) # Sort by score
            .limit(limit)
        )
        return [_norm(x) async for x in cursor]
    
    # 3. Fallback for any other specific status
    query = {
        "status": status,
        "assignee_responder_id": user_id 
    }
    cursor = (
        db["incidents"]
        .find(query)
        .sort([("reported_at", -1)])
        .limit(limit)
    )
    return [_norm(x) async for x in cursor]