import asyncio
import cv2
import os
import numpy as np
import urllib.request
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, Any
import logging
from ultralytics import YOLO
from bson import ObjectId

from app.db.mongo import get_client
from app.modules.hub.ingest_routes import ingest as ingest_incident
from app.utils.time import utcnow_iso
from app.config import settings

logger = logging.getLogger(__name__)

# Global model instance
_accident_model = None

def get_accident_model():
    """Lazy load the accident detection model"""
    global _accident_model
    if _accident_model is None:
        model_path = getattr(settings, 'ACCIDENT_MODEL_PATH', "app/accident_model.pt")
        try:
            logger.info(f"Loading Accident Detection Model from: {model_path}")
            _accident_model = YOLO(model_path)
            logger.info("✅ Accident Detection Model loaded successfully")
        except Exception as e:
            logger.error(f"❌ Failed to load accident model: {e}")
            _accident_model = None
    return _accident_model

def map_severity(violation_data: Dict[str, Any]) -> str:
    """Map violation data to severity grade (low/medium/high)"""
    violation_type = violation_data.get("violationType", "").lower()
    confidence = violation_data.get("confidence", 0)
    violation_conf = violation_data.get("violationConfidence", 0)
    
    max_conf = max(confidence, violation_conf)
    
    if "accident" in violation_type or "crash" in violation_type:
        return "high"
    
    if "triple" in violation_type and max_conf > 0.7:
        return "high"
    
    if max_conf > 0.8:
        return "high"
    elif max_conf > 0.5:
        return "medium"
    else:
        return "low"

def map_camera_risk(camera_data: Optional[Dict]) -> str:
    """Map camera data to risk class"""
    if not camera_data:
        return "medium"
    
    risk = camera_data.get("camera_risk_class", "").lower()
    if risk in ["high", "medium", "low"]:
        return risk
    
    location = camera_data.get("location", "").lower()
    if "school" in location or "hospital" in location or "junction" in location:
        return "high"
    elif "highway" in location or "main" in location:
        return "medium"
    else:
        return "low"

def get_vehicles_involved(violation_data: Dict[str, Any]) -> int:
    """Estimate number of vehicles involved"""
    violation_type = violation_data.get("violationType", "").lower()
    
    if "triple" in violation_type:
        return 1
    elif "accident" in violation_type or "crash" in violation_type:
        return 2
    else:
        return 1

async def fetch_camera_data(cameras_collection, location: str, camera_id: str = None) -> Optional[Dict]:
    """Fetch camera details - FIRST by location name, THEN by ID"""
    try:
        if location and location != "Unknown":
            camera = await cameras_collection.find_one({
                "location": {"$regex": f"^{location}$", "$options": "i"}
            })
            if camera:
                return camera
            
            camera = await cameras_collection.find_one({
                "location": {"$regex": location, "$options": "i"}
            })
            if camera:
                return camera
        
        if camera_id:
            try:
                if isinstance(camera_id, str):
                    camera = await cameras_collection.find_one({"_id": ObjectId(camera_id)})
                else:
                    camera = await cameras_collection.find_one({"_id": camera_id})
                    
                if camera:
                    return camera
            except Exception as e:
                logger.warning(f"Error finding camera by ID: {e}")
        
        camera = await cameras_collection.find_one({})
        if camera:
            return camera
        
    except Exception as e:
        logger.error(f"Error fetching camera data: {e}")
    
    return None

async def is_actual_accident(image_path: str, max_retries: int = 2) -> Tuple[bool, float]:
    """Use YOLO to detect if image contains an accident with retry logic"""
    if not image_path:
        return False, 0.0

    model = get_accident_model()
    if not model:
        logger.warning("Accident model not available")
        return False, 0.0

    for attempt in range(max_retries + 1):
        try:
            img = None
            if image_path.startswith(('http://', 'https://')):
                logger.info(f"Downloading image (attempt {attempt + 1}/{max_retries + 1})...")
                
                req = urllib.request.Request(
                    image_path,
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    }
                )
                
                with urllib.request.urlopen(req, timeout=15) as response:
                    image_data = response.read()
                    
                    if len(image_data) < 100:
                        if attempt < max_retries:
                            await asyncio.sleep(1 * (attempt + 1))
                            continue
                    
                    arr = np.asarray(bytearray(image_data), dtype=np.uint8)
                    img = cv2.imdecode(arr, -1)
                    
            elif os.path.exists(image_path):
                img = cv2.imread(image_path)
            else:
                return False, 0.0

            if img is None:
                if attempt < max_retries:
                    await asyncio.sleep(1 * (attempt + 1))
                    continue
                return False, 0.0

            results = model(img, conf=0.1)

            if len(results) > 0 and len(results[0].boxes) > 0:
                confidences = results[0].boxes.conf.cpu().numpy()
                max_conf = float(max(confidences)) if len(confidences) > 0 else 0
                num_detections = len(results[0].boxes)
                
                if max_conf > 0.1 and num_detections > 0:
                    return True, max_conf
                else:
                    return False, max_conf
            else:
                return False, 0.0

        except Exception as e:
            if attempt < max_retries:
                await asyncio.sleep(1 * (attempt + 1))
                continue
            return False, 0.0

    return False, 0.0

async def check_duplicate_incident(db, location: str, time_window_minutes: int = 5) -> Optional[Dict]:
    """Check for duplicate incidents (spatiotemporal clustering)"""
    try:
        time_threshold = (datetime.now() - timedelta(minutes=time_window_minutes)).isoformat()
        
        cursor = db["incidents"].find({
            "location.address": {"$regex": location, "$options": "i"},
            "reported_at": {"$gte": time_threshold},
            "status": {"$in": ["unverified", "new", "accepted", "enroute", "arrived"]}
        }).sort("reported_at", -1).limit(1)
        
        incidents = await cursor.to_list(length=1)
        return incidents[0] if incidents else None
        
    except Exception as e:
        logger.error(f"Error checking duplicates: {e}")
        return None

async def process_violation(violation: Dict, cameras_collection, incidents_collection) -> bool:
    """Process a single violation record"""
    try:
        violation_id = violation.get("_id")
        logger.info(f"Processing violation: {violation_id}")
        
        location = violation.get("location", "Unknown")
        
        detection_time_raw = violation.get("detectionTime") or violation.get("createdAt") or utcnow_iso()
        
        if isinstance(detection_time_raw, datetime):
            detection_time = detection_time_raw.isoformat()
        else:
            detection_time = str(detection_time_raw)
        
        image_path = violation.get("imagePath") or ""
        violation_type = violation.get("violationType", "").lower()
        plate_number = violation.get("plateNumber", "")
        camera_id = violation.get("cameraId")
        
        confidence = violation.get("confidence", 0)
        violation_conf = violation.get("violationConfidence", 0)
        
        if not image_path:
            return False
        
        is_accident, accident_conf = await is_actual_accident(image_path)
        
        if not is_accident:
            return False
        
        existing = await check_duplicate_incident(
            incidents_collection.database, 
            location
        )
        
        if existing:
            explain = existing.get("explain", [])
            new_note = f"Duplicate confirmed by secondary source (violation: {violation_id})"
            
            if new_note not in explain:
                explain.append(new_note)
                
                await incidents_collection.update_one(
                    {"_id": existing["_id"]},
                    {
                        "$set": {"explain": explain},
                        "$inc": {"duplicate_count": 1}
                    }
                )
            
            return True
        
        camera_data = await fetch_camera_data(cameras_collection, location, camera_id)
        
        lat = 6.9271
        lng = 79.8612
        
        location_coords = {
            "ambalangoda": {"lat": 6.2275, "lng": 80.0564},
            "galle": {"lat": 6.0319, "lng": 80.2168},
            "kirama": {"lat": 6.2134, "lng": 80.6527},
            "walasmulla kirama": {"lat": 6.2134, "lng": 80.6527},
            "matara": {"lat": 5.9549, "lng": 80.5550},
            "colombo": {"lat": 6.9271, "lng": 79.8612},
        }
        
        if camera_data:
            if "coordinates" in camera_data:
                lat = float(camera_data["coordinates"].get("lat", lat))
                lng = float(camera_data["coordinates"].get("lng", lng))
            else:
                location_lower = location.lower()
                for key, coords in location_coords.items():
                    if key in location_lower:
                        lat, lng = coords["lat"], coords["lng"]
                        break
        else:
            location_lower = location.lower()
            for key, coords in location_coords.items():
                if key in location_lower:
                    lat, lng = coords["lat"], coords["lng"]
                    break
        
        payload = {
            "source": "traffic",
            "timestamp_utc": detection_time,
            "location": {
                "lat": lat,
                "lng": lng,
                "address": location
            },
            "severity_grade": map_severity(violation),
            "camera_risk_class": map_camera_risk(camera_data),
            "accident": {
                "vehicles_involved": get_vehicles_involved(violation),
                "fire_present": False
            },
            "media": {
                "image_url": image_path
            },
            "report_id": f"VIOLATION-{str(violation_id)}",
            "violation_metadata": {
                "violation_type": violation_type,
                "confidence": float(confidence),
                "accident_confidence": accident_conf,
                "plate_number": plate_number,
                "original_violation_id": str(violation_id)
            }
        }
        
        result = await ingest_incident(payload)
        logger.info(f"✅ Successfully ingested incident: {result.get('id')}")
        return True
        
    except Exception as e:
        logger.error(f"Error processing violation {violation.get('_id')}: {e}")
        return False

async def poll_shenal_database():
    """Main polling function"""
    logger.info("🚀 Starting database poller...")
    
    consecutive_errors = 0
    
    while True:
        try:
            client = get_client()
            
            shenal_db = client["road_safety"]
            violations_collection = shenal_db["violations"]
            cameras_collection = shenal_db["cameras"]
            
            emergency_db = client["emergency_db"]
            
            violations_count = await violations_collection.count_documents({})
            cameras_count = await cameras_collection.count_documents({})
            
            logger.info(f"📊 Violations: {violations_count}, Cameras: {cameras_count}")
            
            if violations_count == 0:
                await asyncio.sleep(30)
                continue
            
            cursor = violations_collection.find({
                "emergency_processed": {"$ne": True}
            }).sort("_id", -1).limit(5)
            
            violations = await cursor.to_list(length=5)
            
            if violations:
                logger.info(f"📦 Found {len(violations)} new violations")
                
                for violation in violations:
                    success = await process_violation(
                        violation, 
                        cameras_collection, 
                        emergency_db
                    )
                    
                    await violations_collection.update_one(
                        {"_id": violation["_id"]},
                        {
                            "$set": {
                                "emergency_processed": True,
                                "emergency_processed_at": utcnow_iso(),
                                "emergency_success": success
                            }
                        }
                    )
                    
                    await asyncio.sleep(2)
                
                consecutive_errors = 0
            else:
                total = await violations_collection.count_documents({})
                emergency_processed = await violations_collection.count_documents({"emergency_processed": True})
                logger.info(f"Processed: {emergency_processed}/{total}")
            
            await asyncio.sleep(10)
            
        except Exception as e:
            consecutive_errors += 1
            logger.error(f"Polling error: {e}")
            await asyncio.sleep(min(30 * (2 ** consecutive_errors), 300))

async def start_scheduler():
    """Start the background poller"""
    try:
        asyncio.create_task(poll_shenal_database())
        logger.info("✅ database poller scheduled")
    except Exception as e:
        logger.error(f"❌ Failed to start scheduler: {e}")