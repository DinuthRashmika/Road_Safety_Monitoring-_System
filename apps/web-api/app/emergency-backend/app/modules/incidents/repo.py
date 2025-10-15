# app/modules/incidents/repo.py

from bson import ObjectId
from app.db.mongo import get_db

def _id(o): 
    return str(o["_id"])

def _norm(doc: dict) -> dict:
    """Convert Mongo _id to 'id' and drop raw ObjectId."""
    if not doc:
        return doc
    doc = dict(doc)  # shallow copy
    doc["id"] = str(doc["_id"])
    doc.pop("_id", None)
    return doc

# app/modules/incidents/repo.py (continued)

async def insert_incident(doc: dict) -> str:
    db = get_db()
    res = await db["incidents"].insert_one(doc)
    return str(res.inserted_id)

async def get_incident(incident_id: str) -> dict | None:
    db = get_db()
    doc = await db["incidents"].find_one({"_id": ObjectId(incident_id)})
    return _norm(doc) if doc else None

async def update_incident(incident_id: str, patch: dict):
    db = get_db()
    await db["incidents"].update_one({"_id": ObjectId(incident_id)}, {"$set": patch})

async def list_queue(limit=50):
    db = get_db()
    cur = db["incidents"].find({"status": "new"}).sort([("score",-1), ("reported_at",-1)]).limit(limit)
    return [ _norm(x) async for x in cur ]
