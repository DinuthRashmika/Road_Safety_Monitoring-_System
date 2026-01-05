from __future__ import annotations

import logging
import re
from fastapi import APIRouter, HTTPException, Body
from pydantic import ValidationError
from bson import ObjectId
from app.db.mongo import get_db
from app.modules.incidents.schemas import Incident, Accident
from app.modules.incidents.service import compute_scores
from app.modules.incidents.repo import (
    insert_incident, 
    update_incident, 
    get_incident, 
    find_nearby_active_incident 
)
from app.modules.incidents.broadcast import broadcast_incident_update
from app.modules.hub.fire_detector import fire_present_from_image
from app.utils.time import utcnow_iso

logger = logging.getLogger(__name__)

router = APIRouter()

MIN_SCORE_FOR_PROMOTION = 50

def _coerce_score(value) -> int:
    try:
        s = int(round(float(value)))
    except Exception:
        raise HTTPException(status_code=422, detail="`score` must be numeric (0..100).")
    return max(0, min(100, s))


def _sanitize(o):
    if isinstance(o, ObjectId):
        return str(o)
    if isinstance(o, dict):
        return {k: _sanitize(v) for k, v in o.items()}
    if isinstance(o, list):
        return [_sanitize(v) for v in o]
    return o

def clean_image_url(url: str) -> str:
    if not url:
        return url
    
    drive_pattern = r"drive\.google\.com\/file\/d\/([^/]+)"
    match = re.search(drive_pattern, url)
    
    if match:
        file_id = match.group(1)
        new_url = f"https://drive.google.com/uc?export=view&id={file_id}"
        logger.info(f"Sanitized Google Drive URL: {new_url}")
        return new_url
        
    return url

@router.post("/ingest")
async def ingest(payload: dict = Body(...)):
    try:
        if "media" in payload and isinstance(payload["media"], dict):
            raw_url = payload["media"].get("image_url")
            if raw_url:
                payload["media"]["image_url"] = clean_image_url(raw_url)

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

            if was_unverified and (fire_status_provided or inc.score >= MIN_SCORE_FOR_PROMOTION):
                if current_fire or inc.score >= MIN_SCORE_FOR_PROMOTION:
                    inc.status = "new"
                    inc.reported_at = utcnow_iso() 

            doc_to_update = inc.model_dump(exclude={"id"})

            if was_unverified and inc.status == "new":
                 doc_to_update["reported_at"] = inc.reported_at

            await update_incident(inc.id, doc_to_update)
            updated_doc = await get_incident(inc.id)

            if updated_doc and updated_doc["status"] != "unverified":
                await broadcast_incident_update(updated_doc)

            return {"id": inc.id}
        
        if not existing_doc:
            lat = payload.get("location", {}).get("lat")
            lng = payload.get("location", {}).get("lng")
            src = payload.get("source")
            
            if lat and lng and src:
                nearby_parent = await find_nearby_active_incident(lat, lng, src, max_distance_m=150)
                
                if nearby_parent:
                    logger.info(f"CLUSTERING: Merging report {report_id} into parent {nearby_parent['id']}")
                    
                    current_score = nearby_parent.get("score", 0)
                    new_score = min(100, current_score + 3) # +3 Bonus
                    
                    old_explain = nearby_parent.get("explain", [])
                    new_note = f"CONFIRMED: +3 score boost from secondary camera ({report_id})"
                    if new_note not in old_explain:
                        old_explain.append(new_note)
                        
                    patch = {
                        "score": new_score,
                        "explain": old_explain
                    }

                    if nearby_parent["status"] == "unverified" and new_score >= MIN_SCORE_FOR_PROMOTION:
                        patch["status"] = "new"
                        patch["reported_at"] = utcnow_iso() 
                        logger.info(f"CLUSTERING: Incident {nearby_parent['id']} promoted to NEW due to multi-source verification.")

                    await update_incident(nearby_parent["id"], patch)
                    
                    updated_parent = await get_incident(nearby_parent["id"])
                    await broadcast_incident_update(updated_parent)
                    
                    return {"id": nearby_parent["id"], "cluster_action": "merged"}

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

        current_fire = (inc.accident and inc.accident.fire_present) or False
        
        if current_fire or inc.score >= MIN_SCORE_FOR_PROMOTION:
             inc.status = "new"
             inc.reported_at = payload.get("timestamp_utc", utcnow_iso()) 
        else:
             inc.status = "unverified"
             inc.reported_at = payload.get("timestamp_utc", utcnow_iso())

        doc = inc.model_dump(exclude_none=True)
        inserted_id = await insert_incident(doc)

        if inc.status == "new":
            out = _sanitize({**doc, "id": str(inserted_id)})
            await broadcast_incident_update(out)

        return {"id": str(inserted_id)}

    except ValidationError as ve:
        raise HTTPException(status_code=422, detail=ve.errors())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ingest failed: {e}")
        raise HTTPException(status_code=500, detail=f"Ingest failed: {e}")