from __future__ import annotations

from fastapi import APIRouter, HTTPException, Body
from pydantic import ValidationError
from bson import ObjectId
from app.db.mongo import get_db 
from app.modules.incidents.schemas import Incident, Accident 
from app.modules.incidents.service import compute_scores
from app.modules.incidents.repo import insert_incident, update_incident, get_incident
from app.modules.incidents.broadcast import broadcast_incident_update
from app.modules.hub.fire_detector import fire_present_from_image 
from app.utils.time import utcnow_iso 

router = APIRouter()

MIN_SCORE_FOR_PROMOTION = 50 

def _coerce_score(value) -> int:
    """Accept int/float/str; round to nearest int and clamp 0..100."""
    try:
        s = int(round(float(value)))
    except Exception:
        raise HTTPException(status_code=422, detail="`score` must be numeric (0..100).")
    return max(0, min(100, s))


def _sanitize(o):
    """Recursively convert ObjectId -> str so json.dumps will work."""
    if isinstance(o, ObjectId):
        return str(o)
    if isinstance(o, dict):
        return {k: _sanitize(v) for k, v in o.items()}
    if isinstance(o, list):
        return [_sanitize(v) for v in o]
    return o


@router.post("/ingest")
async def ingest(payload: dict = Body(...)):
    """
    Accept Incident payload. 
    MODIFIED LOGIC: Forces 'unverified' on initial ingest. Only allows promotion 
    to 'new' upon update that explicitly sets the fire status (true/false) AND meets 
    the priority score threshold (50) or is a fire incident.
    """
    try:
        provided_score = payload.pop("score", None)
        report_id = payload.get("report_id")

        db = get_db()
        existing_doc = None
        
        if report_id:
            existing_doc = await db["incidents"].find_one({"report_id": report_id})
        
        fire_status_provided = 'accident' in payload and 'fire_present' in payload['accident']
        
        if existing_doc:
            was_unverified = existing_doc.get("status") == "unverified"
            
            inc_data = {
                **_sanitize(existing_doc), 
                **payload, 
                "id": str(existing_doc["_id"])
            }
            inc = Incident(**inc_data)
            
            inc = compute_scores(inc)

            if provided_score is not None:
                inc.score = _coerce_score(provided_score)

            current_fire = (inc.accident and inc.accident.fire_present) or False
            
            if was_unverified and fire_status_provided:
                if current_fire or inc.score >= MIN_SCORE_FOR_PROMOTION:
                    inc.status = "new"
                    inc.reported_at = utcnow_iso()
            
            doc_to_update = inc.model_dump(exclude={"id"})
            
            if was_unverified and inc.status == "new" and hasattr(inc, 'reported_at'):
                 doc_to_update["reported_at"] = inc.reported_at
                 
            await update_incident(inc.id, doc_to_update)
            updated_doc = await get_incident(inc.id)
            
            if updated_doc and updated_doc["status"] != "unverified":
                await broadcast_incident_update(updated_doc)
            
            return {"id": inc.id}

        if not payload.get("timestamp_utc") and not payload.get("reported_at"):
             payload["timestamp_utc"] = utcnow_iso()

        inc = Incident(**payload)
        
        if inc.media and inc.media.image_url:
            if await fire_present_from_image(inc.media.image_url):
                if inc.accident:
                    inc.accident = inc.accident.model_copy(update={"fire_present": True})
                else:
                    inc.accident = Accident(vehicles_involved=1, fire_present=True)

        inc = compute_scores(inc)

        if provided_score is not None:
            inc.score = _coerce_score(provided_score)
        
        inc.status = "unverified" 
        
        doc = inc.model_dump(exclude_none=True)
        inserted_id = await insert_incident(doc)

        out = _sanitize({**doc, "id": str(inserted_id)}) 
        
        return {"id": str(inserted_id)}

    except ValidationError as ve:
        raise HTTPException(status_code=422, detail=ve.errors())
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingest failed: {e}")