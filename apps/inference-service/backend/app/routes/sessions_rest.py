from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId
import app.db.mongodb as mongodb
from app.core.deps import get_current_owner
from app.schemas.session import SessionCreate, SessionOut
from app.models.session_model import session_doc
from datetime import datetime

router = APIRouter(prefix="/api/sessions", tags=["DMS Sessions"])

@router.post("", response_model=SessionOut)
async def start_session(payload: SessionCreate, current=Depends(get_current_owner)):
    """
    Start a new DMS session. Returns the session id for WS.
    """
    doc = session_doc(current["_id"], payload.name)
    res = await mongodb.db.sessions.insert_one(doc)
    return {
        "id": str(res.inserted_id),
        "name": doc["name"],
        "startedAt": doc["startedAt"].isoformat(),
        "endedAt": None,
        "metrics": doc["metrics"],
    }

@router.post("/{sid}/end", response_model=SessionOut)
async def end_session(sid: str, current=Depends(get_current_owner)):
    """
    Mark session as ended (no effect on stored events).
    """
    q = {"_id": ObjectId(sid), "ownerId": current["_id"]}
    s = await mongodb.db.sessions.find_one(q)
    if not s:
        raise HTTPException(404, "Session not found")
    await mongodb.db.sessions.update_one(q, {"$set": {"endedAt": datetime.utcnow()}})
    s = await mongodb.db.sessions.find_one(q)
    return {
        "id": str(s["_id"]),
        "name": s["name"],
        "startedAt": s["startedAt"].isoformat(),
        "endedAt": s["endedAt"].isoformat() if s.get("endedAt") else None,
        "metrics": s["metrics"],
    }

@router.get("", response_model=list[SessionOut])
async def list_sessions(current=Depends(get_current_owner)):
    """
    List sessions for the logged-in owner.
    """
    cur = mongodb.db.sessions.find({"ownerId": current["_id"]}).sort("startedAt", -1)
    out = []
    async for s in cur:
        out.append({
            "id": str(s["_id"]),
            "name": s["name"],
            "startedAt": s["startedAt"].isoformat(),
            "endedAt": s["endedAt"].isoformat() if s.get("endedAt") else None,
            "metrics": s["metrics"],
        })
    return out

@router.get("/{sid}", response_model=SessionOut)
async def get_session(sid: str, current=Depends(get_current_owner)):
    """
    Get a single session summary.
    """
    s = await mongodb.db.sessions.find_one({"_id": ObjectId(sid), "ownerId": current["_id"]})
    if not s:
        raise HTTPException(404, "Session not found")
    return {
        "id": str(s["_id"]),
        "name": s["name"],
        "startedAt": s["startedAt"].isoformat(),
        "endedAt": s["endedAt"].isoformat() if s.get("endedAt") else None,
        "metrics": s["metrics"],
    }
