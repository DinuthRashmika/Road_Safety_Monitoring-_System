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
    doc = session_doc(current["_id"], current["fullName"],payload)
    res = await mongodb.db.sessions.insert_one(doc)
    return {
        "id": str(res.inserted_id),
        "name": doc["name"],
        "distanceKm": doc["distanceKm"],
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
from bson import ObjectId
from fastapi import HTTPException, Depends
@router.get("/{sid}", response_model=SessionOut)
async def get_session(sid: str, current=Depends(get_current_owner)):
    """
    Get a single session with related events.
    """

    session_id = ObjectId(sid)

    # 1. Get session
    s = await mongodb.db.sessions.find_one({
        "_id": session_id,
        "ownerId": current["_id"]
    })

    if not s:
        raise HTTPException(status_code=404, detail="Session not found")

    # 2. Get related events
    cursor = mongodb.db.events.find({"sessionId": session_id})
    events = []

    async for e in cursor:
        events.append({
            "id": str(e["_id"]),
            "type": e["type"],
            "confidence": e["confidence"],
            "createdAt": e["createdAt"].isoformat() if e.get("createdAt") else None
        })

    # 3. Assign response to variable
    session_response = {
        "id": str(s["_id"]),
        "name": s["name"],
        "startedAt": s["startedAt"].isoformat(),
        "endedAt": s["endedAt"].isoformat() if s.get("endedAt") else None,
        "metrics": s["metrics"],
        "events": events
    }

    # 4. Return variable
    return session_response
@router.delete("/{sid}")
async def delete_session(sid: str, current=Depends(get_current_owner)):
    """
    Delete a session and all related events.
    """

    # 1. Validate ObjectId
    try:
        session_id = ObjectId(sid)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid session ID")

    # 2. Check if session exists & belongs to owner
    session = await mongodb.db.sessions.find_one({
        "_id": session_id,
        "ownerId": current["_id"]
    })

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # 3. Delete related events
    events_result = await mongodb.db.events.delete_many({
        "sessionId": session_id
    })

    # 4. Delete session
    session_result = await mongodb.db.sessions.delete_one({
        "_id": session_id
    })

    # 5. Response
    return {
        "message": "Session and related events deleted successfully",
        "deletedSessionId": sid,
        "deletedEventsCount": events_result.deleted_count
    }