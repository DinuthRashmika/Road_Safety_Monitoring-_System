from __future__ import annotations

import logging
import re
import os
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
    get_incident
    # Removed: find_nearby_active_incident
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

def get_local_image_path(image_path: str) -> str:
    """Convert local file path to API endpoint, preserving folder structure"""
    if not image_path:
        return image_path
    
    if image_path.startswith(('http://', 'https://')):
        return image_path
    
    clean_path = image_path.replace('\\', '/')
    
    clean_path = clean_path.lstrip('/')
    
    import urllib.parse
    encoded_path = urllib.parse.quote(clean_path)
    
    return f"/api/images/{encoded_path}"

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
        # Handle image URL - convert local paths to API endpoints
        if "media" in payload and isinstance(payload["media"], dict):
            raw_url = payload["media"].get("image_url")
            if raw_url:
                cleaned_url = clean_image_url(raw_url)
                payload["media"]["image_url"] = get_local_image_path(cleaned_url)

        provided_score = payload.pop("score", None)
        report_id = payload.get("report_id")
        violation_metadata = payload.pop("violation_metadata", None)

        db = get_db()
        existing_doc = None

        # Check for existing incident by report_id
        if report_id:
            existing_doc = await db["incidents"].find_one({"report_id": report_id})

        fire_status_provided = 'accident' in payload and 'fire_present' in payload['accident']

        # CASE 1: Update existing incident
        if existing_doc:
            was_unverified = existing_doc.get("status") == "unverified"

            # Merge existing data with new payload
            inc_data = {
                **_sanitize(existing_doc),
                **payload,
                "id": str(existing_doc["_id"])
            }
            inc = Incident(**inc_data)

            # Recompute scores
            inc = compute_scores(inc)

            # Override score if provided
            if provided_score is not None:
                inc.score = _coerce_score(provided_score)

            current_fire = (inc.accident and inc.accident.fire_present) or False

            # Promote from unverified if conditions met
            if was_unverified and (fire_status_provided or inc.score >= MIN_SCORE_FOR_PROMOTION):
                if current_fire or inc.score >= MIN_SCORE_FOR_PROMOTION:
                    inc.status = "new"
                    inc.reported_at = utcnow_iso()

            # Prepare update
            doc_to_update = inc.model_dump(exclude={"id"})

            if was_unverified and inc.status == "new":
                doc_to_update["reported_at"] = inc.reported_at

            # Apply update
            await update_incident(inc.id, doc_to_update)
            updated_doc = await get_incident(inc.id)

            # Broadcast if promoted
            if updated_doc and updated_doc["status"] != "unverified":
                await broadcast_incident_update(updated_doc)

            return {"id": inc.id, "action": "updated"}

        # CASE 2: Create new incident (NO CLUSTERING/DUPLICATE CHECK)
        # Ensure timestamp exists
        if not payload.get("timestamp_utc") and not payload.get("reported_at"):
            payload["timestamp_utc"] = utcnow_iso()

        # Create incident object
        inc = Incident(**payload)

        # Check for fire in image
        if inc.media and inc.media.image_url:
            if await fire_present_from_image(inc.media.image_url):
                if inc.accident:
                    inc.accident = inc.accident.model_copy(update={"fire_present": True})
                else:
                    inc.accident = Accident(vehicles_involved=1, fire_present=True)
                logger.info(f"🔥 Fire detected in image for new incident")

        # Compute priority score
        inc = compute_scores(inc)

        # Override score if provided
        if provided_score is not None:
            inc.score = _coerce_score(provided_score)

        # Determine initial status based on score/fire
        current_fire = (inc.accident and inc.accident.fire_present) or False
        
        if current_fire or inc.score >= MIN_SCORE_FOR_PROMOTION:
            inc.status = "new"
            inc.reported_at = payload.get("timestamp_utc", utcnow_iso())
        else:
            inc.status = "unverified"
            inc.reported_at = payload.get("timestamp_utc", utcnow_iso())

        # Prepare document for insertion
        doc = inc.model_dump(exclude_none=True)
        
        # Add duplicate tracking (though clustering is disabled)
        doc["duplicate_count"] = 0
        
        # Insert into database
        inserted_id = await insert_incident(doc)

        # Store violation reference if provided
        if violation_metadata:
            await store_violation_reference(str(inserted_id), violation_metadata)

        # Broadcast if it's a new (verified) incident
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