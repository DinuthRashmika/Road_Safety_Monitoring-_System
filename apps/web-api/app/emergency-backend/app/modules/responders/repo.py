from __future__ import annotations

from typing import Any, Dict, List
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
    }


def _norm_unit(doc: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": _id(doc),
        "code": doc.get("code"),
        "type": doc.get("type"),
        "home_lat": doc.get("home_lat"),
        "home_lng": doc.get("home_lng"),
        "status": doc.get("status"),
    }


# ---------- Users ----------
async def create_user(name: str, email: str, role: str, password_hash: str) -> str:
    db = get_db()
    email_norm = email.strip().lower()
    try:
        res = await db["users"].insert_one(
            {"name": name, "email": email_norm, "role": role, "password_hash": password_hash}
        )
        return str(res.inserted_id)
    except DuplicateKeyError:
        raise ValueError("email_exists")


async def list_users() -> List[Dict[str, Any]]:
    db = get_db()
    cur = db["users"].find({}, {"password_hash": 0})
    return [_norm_user(x) async for x in cur]


async def delete_user(user_id: str) -> None:
    db = get_db()
    await db["users"].delete_one({"_id": ObjectId(user_id)})


# ---------- Units ----------
async def create_unit(doc: Dict[str, Any]) -> str:
    db = get_db()
    try:
        res = await db["units"].insert_one(doc)
        return str(res.inserted_id)
    except DuplicateKeyError:
        raise ValueError("unit_code_exists")


async def list_units() -> List[Dict[str, Any]]:
    db = get_db()
    cur = db["units"].find({})
    return [_norm_unit(x) async for x in cur]


async def update_unit(unit_id: str, patch: Dict[str, Any]) -> None:
    db = get_db()
    await db["units"].update_one({"_id": ObjectId(unit_id)}, {"$set": patch})


async def delete_unit(unit_id: str) -> None:
    db = get_db()
    await db["units"].delete_one({"_id": ObjectId(unit_id)})
