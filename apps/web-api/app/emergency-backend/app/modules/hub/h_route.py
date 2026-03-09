"""
Human Behavior (Pamalis) routes for ingesting alerts into the emergency system.
"""

from fastapi import APIRouter, HTTPException, Body
from datetime import datetime
import logging
from app.db.mongo import get_db
from app.modules.incidents.schemas import Incident, ViolenceDetails, DetectedObject
from app.modules.incidents.service import compute_scores
from app.modules.incidents.repo import insert_incident
from app.utils.time import utcnow_iso

logger = logging.getLogger(__name__)
router = APIRouter()

# Camera location mapping based on your data
CAMERA_LOCATIONS = {
    "Main Camera": {"lat": 6.9271, "lng": 79.8612, "address": "Colombo"},
    "Zone A": {"lat": 6.9271, "lng": 79.8612, "address": "Colombo"},
    "Zone B": {"lat": 6.0319, "lng": 80.2168, "address": "Galle"},
    "Zone C": {"lat": 5.9549, "lng": 80.5550, "address": "Matara"},
    "Zone D": {"lat": 6.2275, "lng": 80.0564, "address": "Ambalangoda"},
    "Zone E": {"lat": 6.2134, "lng": 80.6527, "address": "Kirama"},
}

@router.post("/human/ingest")
async def ingest_human_alert(payload: dict = Body(...)):
    """
    Ingest human behavior alerts from Pamalis system.
    No detection models run - just processes raw alert data.
    Responders: Police and Ambulance only (no fire)
    """
    try:
        objects_detected = []
        if payload.get("objects_detected"):
            for obj in payload["objects_detected"]:
                objects_detected.append(DetectedObject(
                    object=obj.get("object", "unknown"),
                    confidence=obj.get("confidence", 0)
                ))
        
        camera_risk = "medium"
        
        # Get location from payload or use camera mapping
        location_name = payload.get("location", "Unknown")
        camera_name = payload.get("camera", "Main Camera")
        
        # Try to get coordinates from camera mapping
        location_coords = CAMERA_LOCATIONS.get(camera_name, CAMERA_LOCATIONS.get("Main Camera"))
        
        violence_details = ViolenceDetails(
            participants_count=1,  
            weapon_conf=payload.get("threat_score", 0),
            threat_score=payload.get("threat_score"),
            has_weapon=payload.get("has_weapon", False),
            action_confidence=payload.get("action_confidence"),
            sustained_seconds=payload.get("sustained_seconds"),
            action=payload.get("action"),
            objects_detected=objects_detected,
            threat_level=payload.get("threat_level"),
            action_contribution=payload.get("action_contribution"),
            object_contribution=payload.get("object_contribution"),
            synergy_bonus=payload.get("synergy_bonus"),
            reasoning=payload.get("reasoning"),
            human_summary=payload.get("human_summary")
        )
        
        severity_map = {
            "HIGH": "high",
            "MEDIUM": "medium", 
            "LOW": "low"
        }
        severity = severity_map.get(payload.get("threat_level", "MEDIUM"), "medium")
        
        incident = Incident(
            source="human_behavior",
            reported_at=payload.get("timestamp", utcnow_iso()),
            location={
                "lat": location_coords["lat"], 
                "lng": location_coords["lng"],
                "address": location_name
            },
            severity_grade=severity,
            camera_risk_class=camera_risk,
            violence=violence_details,
            media=None
        )
        
        # Compute priority scores
        incident = compute_scores(incident)
        
        doc = incident.model_dump(exclude_none=True)
        inserted_id = await insert_incident(doc)
        
        logger.info(f"✅ Human behavior alert ingested: {inserted_id} with score {incident.score}")
        logger.info(f"   Location: {location_name} ({location_coords['lat']}, {location_coords['lng']})")
        logger.info(f"   Required responders: {incident.required_roles}")
        
        return {
            "id": str(inserted_id), 
            "score": incident.score,
            "required_roles": incident.required_roles,
            "location": location_coords
        }
        
    except Exception as e:
        logger.error(f"Failed to ingest human behavior alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/human/health")
async def human_health():
    """Health check for human behavior endpoint"""
    return {
        "status": "healthy",
        "source": "human_behavior",
        "timestamp": utcnow_iso()
    }