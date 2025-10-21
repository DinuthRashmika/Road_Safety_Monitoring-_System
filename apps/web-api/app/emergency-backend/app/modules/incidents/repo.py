# app/modules/incidents/repo.py
from __future__ import annotations

from typing import Optional, List, Dict
from bson import ObjectId
from app.db.mongo import get_db


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


async def list_queue(limit: int = 50, role: Optional[str] = None) -> List[Dict]:
    """
    Return 'new' incidents sorted by score desc, reported_at desc.

    Role filtering:
      - admin: see all 'new' incidents
      - police/ambulance/fire: only see incidents where that role is in required_units
        (e.g., fire sees only incidents with fire_required = true in required_units)
    """
    db = get_db()
    query: dict = {"status": "new"}

    if role and role != "admin":
        query["required_units"] = {"$in": [role]}

    cursor = (
        db["incidents"]
        .find(query)
        .sort([("score", -1), ("reported_at", -1)])
        .limit(limit)
    )
    return [_norm(x) async for x in cursor]
