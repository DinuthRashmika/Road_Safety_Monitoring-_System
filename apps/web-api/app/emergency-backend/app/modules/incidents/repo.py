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


async def list_queue(limit: int = 50, role: Optional[str] = None, user_location: Optional[dict] = None) -> List[Dict]:
    """
    Return 'new' incidents, sorted by score OR distance.
    Role filtering:
      - admin: see all 'new' incidents, sorted by score
      - police/ambulance/fire: see 'new' incidents that are GEOGRAPHICALLY NEARBY
        and require their role.
    """
    db = get_db()
    
    if role == "admin":
        query: dict = {"status": "new"}
        cursor = (
            db["incidents"]
            .find(query)
            .sort([("score", -1), ("reported_at", -1)])
            .limit(limit)
        )
        return [_norm(x) async for x in cursor]

    if not user_location:
        return [] 

    pipeline = [
        {
            "$geoNear": {
                "near": {
                    "type": "Point",
                    "coordinates": [user_location["lng"], user_location["lat"]]
                },
                "distanceField": "distance_m", 
                "query": {
                    "status": "new",
                    "required_roles": {"$in": [role]}
                },
                "spherical": True
            }
        },
        { "$sort": {"distance_m": 1} }, 
        { "$limit": limit }
    ]
    
    cursor = db["incidents"].aggregate(pipeline)
    return [_norm(x) async for x in cursor]