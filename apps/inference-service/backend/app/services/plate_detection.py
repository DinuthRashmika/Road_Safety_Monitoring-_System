import asyncio
import cv2
import torch
import numpy as np
from datetime import datetime
import os
from pathlib import Path
from app.core.config import settings
import app.db.mongodb as mongodb
from app.models.violation_model import violation_doc
from app.utils.images import save_detection_image
import logging

logger = logging.getLogger(__name__)

class PlateDetector:
    def __init__(self):
        self.model = None
        self.confidence_threshold = settings.DETECTION_CONFIDENCE
        self.frame_count = 0
        
    def load_model(self):
        """Load YOLO model"""
        try:
            if not os.path.exists(settings.YOLO_MODEL):
                raise FileNotFoundError(f"Model file not found: {settings.YOLO_MODEL}")
            
            # Load YOLOv5 model
            self.model = torch.hub.load('ultralytics/yolov5', 'custom', 
                                       path=settings.YOLO_MODEL, force_reload=True)
            self.model.conf = self.confidence_threshold
            logger.info(f"Model loaded from {settings.YOLO_MODEL}")
            return True
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False
    
    def detect_plate(self, frame):
        """Detect license plate in frame"""
        if self.model is None:
            return None
        
        # Run inference
        results = self.model(frame)
        
        # Process results
        detections = results.pandas().xyxy[0]
        
        if len(detections) > 0:
            # Get the detection with highest confidence
            best_detection = detections.iloc[0]
            plate_number = best_detection.get('name', '').upper()
            confidence = best_detection.get('confidence', 0)
            
            if plate_number and confidence >= self.confidence_threshold:
                # Extract plate region
                x1, y1, x2, y2 = int(best_detection['xmin']), int(best_detection['ymin']), \
                                int(best_detection['xmax']), int(best_detection['ymax'])
                
                # Draw bounding box
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, f"{plate_number} ({confidence:.2f})", 
                           (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                
                return plate_number, confidence, (x1, y1, x2, y2), frame
        
        return None
    
    async def process_detection(self, plate_number: str, confidence: float, 
                               image_data: bytes = None, location: str = None, 
                               camera_id: str = None):
        """Process detected plate and create violation record"""
        try:
            if mongodb.db is None:
                logger.error("Database not initialized")
                return None
            
            # Clean plate number (remove spaces, special chars)
            clean_plate = ''.join(c for c in plate_number if c.isalnum()).upper()
            
            # Find vehicle in database
            vehicle = await mongodb.db.vehicles.find_one({
                "plateNo": clean_plate,
                "status": "active"
            })
            
            # Save detection image if enabled
            image_path = None
            if image_data and settings.SAVE_DETECTED_IMAGES:
                image_path = save_detection_image(image_data, clean_plate)
            
            # Create violation record
            violation = violation_doc(
                vehicleId=vehicle["_id"] if vehicle else None,
                plateNumber=clean_plate,
                detectionTime=datetime.now(),
                location=location,
                cameraId=camera_id,
                confidence=confidence,
                imagePath=image_path,
                notified=False,
                ownerId=str(vehicle["ownerId"]) if vehicle else None
            )
            
            # Insert violation
            await mongodb.db.violations.insert_one(violation)
            
            if vehicle:
                logger.info(f"Registered vehicle found for plate: {clean_plate}")
                # Get owner details
                owner = await mongodb.db.users.find_one({"_id": vehicle["ownerId"]})
                if owner:
                    return {
                        "violation_id": str(violation["_id"]),
                        "plate_number": clean_plate,
                        "owner": {
                            "id": str(owner["_id"]),
                            "name": owner["fullName"],
                            "phone": owner["phone"],
                            "email": owner["email"]
                        },
                        "vehicle": {
                            "type": vehicle["vehicleType"],
                            "model": vehicle["vehicleModel"]
                        }
                    }
            else:
                logger.info(f"No registered vehicle found for plate: {clean_plate}")
            
            return {
                "violation_id": str(violation["_id"]),
                "plate_number": clean_plate,
                "owner": None,
                "vehicle": None
            }
            
        except Exception as e:
            logger.error(f"Error processing detection: {e}")
            return None

# Global detector instance
detector = PlateDetector()