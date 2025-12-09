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
    
    active_statuses = ["new", "accepted", "enroute", "arrived"]
    
    if role == "admin":
        if status == "active":
            query: dict = {"status": {"$in": active_statuses}}
        else:
            query: dict = {"status": status}

        cursor = (
            db["incidents"]
            .find(query)
            .sort([("score", -1), ("reported_at", -1)])
            .limit(limit)
        )
        return [_norm(x) async for x in cursor]
    
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

    if status == "active":
        query = {
            "status": {"$in": active_statuses},
            "$or": [
                {"status": "new", "required_roles": {"$in": [role]}},
                {"assignee_responder_id": user_id}
            ]
        }
        cursor = (
            db["incidents"]
            .find(query)
            .sort([("score", -1)])
            .limit(limit)
        )
        return [_norm(x) async for x in cursor]
    
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