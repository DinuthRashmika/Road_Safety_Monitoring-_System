from __future__ import annotations

from typing import Any, Dict, List, Optional
from bson import ObjectId
from pymongo.errors import DuplicateKeyError

from app.db.mongo import get_db

def _id(doc: Dict[str, Any]) -> str:
    return str(doc["_id"])

def _norm_user(doc: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": _id(doc),
        "name": doc.get("name"),
        "email": doc.get("email"),
        "role": doc.get("role"),
        "location": doc.get("location"), 
    }

async def create_user(name: str, email: str, role: str, password_hash: str, location: dict) -> str:
    db = get_db()
    email_norm = email.strip().lower()
    try:
        res = await db["users"].insert_one(
            {"name": name, "email": email_norm, "role": role, "password_hash": password_hash, "location": location}
        )
        return str(res.inserted_id)
    except DuplicateKeyError:
        raise ValueError("email_exists")

async def list_users() -> List[Dict[str, Any]]:
    db = get_db()
    cur = db["users"].find({}, {"password_hash": 0})
    return [_norm_user(x) async for x in cur]

async def get_user(user_id: str) -> Optional[Dict[str, Any]]:
    db = get_db()
    doc = await db["users"].find_one({"_id": ObjectId(user_id)}, {"password_hash": 0})
    return _norm_user(doc) if doc else None
    
async def get_user_by_email(email: str) -> Optional[dict]:
    db = get_db()
    return await db["users"].find_one({"email": email.strip().lower()})


async def update_user(user_id: str, patch: Dict[str, Any]) -> None:
    db = get_db()
    if "email" in patch and isinstance(patch["email"], str):
        patch["email"] = patch["email"].strip().lower()
    try:
        await db["users"].update_one({"_id": ObjectId(user_id)}, {"$set": patch})
    except DuplicateKeyError:
        raise ValueError("email_exists")

async def delete_user(user_id: str) -> None:
    db = get_db()
    await db["users"].delete_one({"_id": ObjectId(user_id)})
