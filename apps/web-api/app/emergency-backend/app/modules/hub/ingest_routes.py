from __future__ import annotations

import logging
import re
from fastapi import APIRouter, HTTPException, Body
from pydantic import ValidationError
from bson import ObjectId
from typing import Optional, Dict, Any

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
    
    # Handle Google Drive links
    drive_pattern = r"drive\.google\.com\/file\/d\/([^/]+)"
    match = re.search(drive_pattern, url)
    
    if match:
        file_id = match.group(1)
        new_url = f"https://drive.google.com/uc?export=view&id={file_id}"
        logger.info(f"Sanitized Google Drive URL: {new_url}")
        return new_url
    
    return url

async def store_violation_reference(incident_id: str, violation_metadata: Dict[str, Any]):
    try:
        db = get_db()
        await db["violation_references"].insert_one({
            "incident_id": incident_id,
            "violation_id": violation_metadata.get("original_violation_id"),
            "violation_type": violation_metadata.get("violation_type"),
            "plate_number": violation_metadata.get("plate_number"),
            "confidence": violation_metadata.get("confidence"),
            "accident_confidence": violation_metadata.get("accident_confidence"),
            "created_at": utcnow_iso()
        })
        logger.info(f"Stored violation reference for incident {incident_id}")
    except Exception as e:
        logger.error(f"Failed to store violation reference: {e}")

@router.post("/ingest")
async def ingest(payload: dict = Body(...)):
  
    try:
        if "media" in payload and isinstance(payload["media"], dict):
            raw_url = payload["media"].get("image_url")
            if raw_url:
                payload["media"]["image_url"] = clean_image_url(raw_url)

        provided_score = payload.pop("score", None)
        report_id = payload.get("report_id")
        violation_metadata = payload.pop("violation_metadata", None)

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

            return {"id": inc.id, "action": "updated"}

        if not existing_doc:
            lat = payload.get("location", {}).get("lat")
            lng = payload.get("location", {}).get("lng")
            src = payload.get("source")
            
            if lat and lng and src:
                nearby_parent = await find_nearby_active_incident(
                    lat, lng, src, max_distance_m=150
                )
                
                if nearby_parent:
                    logger.info(f"CLUSTERING: Merging report {report_id} into parent {nearby_parent['id']}")
                    
                    old_explain = nearby_parent.get("explain", [])
                    new_note = f"Duplicate confirmed by secondary source ({report_id or 'unknown'})"
                    
                    if new_note not in old_explain:
                        old_explain.append(new_note)
                        
                    patch = {
                        "explain": old_explain,
                        "duplicate_count": nearby_parent.get("duplicate_count", 0) + 1
                    }

                    await update_incident(nearby_parent["id"], patch)
                    
                    updated_parent = await get_incident(nearby_parent["id"])
                    await broadcast_incident_update(updated_parent)
                    
                    if violation_metadata:
                        await store_violation_reference(
                            nearby_parent["id"], 
                            violation_metadata
                        )
                    
                    return {
                        "id": nearby_parent["id"], 
                        "action": "merged",
                        "parent_id": nearby_parent["id"]
                    }

        if not payload.get("timestamp_utc") and not payload.get("reported_at"):
            payload["timestamp_utc"] = utcnow_iso()

        inc = Incident(**payload)

        if inc.media and inc.media.image_url:
            if await fire_present_from_image(inc.media.image_url):
                if inc.accident:
                    inc.accident = inc.accident.model_copy(update={"fire_present": True})
                else:
                    inc.accident = Accident(vehicles_involved=1, fire_present=True)
                logger.info(f"🔥 Fire detected in image for new incident")

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
        
        doc["duplicate_count"] = 0
        
        inserted_id = await insert_incident(doc)

        if violation_metadata:
            await store_violation_reference(str(inserted_id), violation_metadata)

        if inc.status == "new":
            out = _sanitize({**doc, "id": str(inserted_id)})
            await broadcast_incident_update(out)
            logger.info(f"📢 Broadcast new incident {inserted_id}")

        logger.info(f"✅ Created new incident {inserted_id} with status {inc.status}")
        return {"id": str(inserted_id), "action": "created", "status": inc.status}

    except ValidationError as ve:
        logger.error(f"Validation error: {ve.errors()}")
        raise HTTPException(status_code=422, detail=ve.errors())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ingest failed: {e}")
        raise HTTPException(status_code=500, detail=f"Ingest failed: {e}")