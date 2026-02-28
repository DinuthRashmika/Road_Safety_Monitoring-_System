# app/routes/protective_alerts.py

from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId
from typing import List, Any, Dict
import logging

import app.db.mongodb as mongodb

# ✅ IMPORTANT:
# Use the SAME dependency you already use in other routes to get logged-in owner/user.
# If your project has: from app.core.deps import get_current_user
# OR: get_current_owner
# Replace the import below to match your existing system.

from app.core.deps import get_current_user  # <-- change ONLY if your project uses different name

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/protective-alerts", tags=["Protective Alerts"])


def _oid(x) -> ObjectId:
    try:
        return ObjectId(str(x))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid id")


def _serialize_doc(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Convert Mongo ObjectIds + datetime to JSON friendly."""
    if not doc:
        return doc

    out = {}
    for k, v in doc.items():
        if isinstance(v, ObjectId):
            out[k] = str(v)
        else:
            out[k] = v
    return out


def _get_owner_id_from_user(current_user: dict) -> str:
    """
    Your system has Owners and/or Users.
    We need the logged in person's Mongo _id for filtering.
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # common patterns:
    # {"id": "..."} or {"_id": ObjectId(...)}
    if "id" in current_user and current_user["id"]:
        return str(current_user["id"])

    if "_id" in current_user and current_user["_id"]:
        return str(current_user["_id"])

    raise HTTPException(status_code=401, detail="Invalid user session")


@router.get("/", response_model=List[dict])
async def get_my_protective_alerts(current_user: dict = Depends(get_current_user)):
    """
    Returns protective alerts ONLY from collection: protective_alerts
    for the logged in owner/user.
    """
    if mongodb.db is None or mongodb.db.db is None:
        raise HTTPException(status_code=500, detail="Database not connected")

    owner_id = _get_owner_id_from_user(current_user)
    db = mongodb.db.db

    cursor = db.protective_alerts.find({"ownerId": _oid(owner_id)}).sort("createdAt", -1)
    docs = await cursor.to_list(length=200)

    return [_serialize_doc(d) for d in docs]


@router.put("/{alert_id}/read")
async def mark_protective_alert_as_read(
    alert_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Mark a protective alert as read (only if it belongs to logged user).
    """
    if mongodb.db is None or mongodb.db.db is None:
        raise HTTPException(status_code=500, detail="Database not connected")

    owner_id = _get_owner_id_from_user(current_user)
    db = mongodb.db.db

    res = await db.protective_alerts.update_one(
        {"_id": _oid(alert_id), "ownerId": _oid(owner_id)},
        {"$set": {"isRead": True}},
    )

    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Protective alert not found")

    return {"success": True, "id": alert_id}