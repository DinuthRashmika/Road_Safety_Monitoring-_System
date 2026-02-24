import cv2
import asyncio
import requests
import time
import numpy as np
from datetime import datetime
import base64
import json
import logging
from app.core.config import settings
from app.services.plate_detector import PlateDetector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CCTVPlateDetector:
    def __init__(self):
        self.detector = PlateDetector()
        self.api_url = f"http://{settings.API_HOST}:{settings.API_PORT}/api/violations/detect"
        self.running = False
        
    def start(self, source=0, location="Main Gate", camera_id="CAM001"):
        """Start plate detection from CCTV/webcam"""
        logger.info(f"Starting plate detector from source: {source}")
        
        # Load model
        if not self.detector.load_model():
            logger.error("Failed to load model. Exiting.")
            return
        
        # Open video source
        cap = cv2.VideoCapture(source)
        if not cap.isOpened():
            logger.error(f"Failed to open video source: {source}")
            return
        
        self.running = True
        frame_count = 0
        
        logger.info("Plate detection started. Press 'q' to quit.")
        
        try:
            while self.running:
                ret, frame = cap.read()
                if not ret:
                    logger.warning("Failed to grab frame")
                    break
                
                frame_count += 1
                
                # Process every N frames (for performance)
                if frame_count % settings.FRAME_SKIP != 0:
                    continue
                
                # Detect plate
                result = self.detector.detect_plate(frame)
                
                if result:
                    plate_number, confidence, bbox = result
                    
                    logger.info(f"Detected: {plate_number} (confidence: {confidence:.2f})")
                    
                    # Convert frame to base64 for API
                    _, buffer = cv2.imencode('.jpg', frame)
                    image_base64 = base64.b64encode(buffer).decode('utf-8')
                    
                    # Send to API
                    asyncio.run(self.send_detection_to_api(
                        plate_number=plate_number,
                        confidence=float(confidence),
                        image_base64=image_base64,
                        location=location,
                        camera_id=camera_id
                    ))
                
                # Display frame (optional)
                cv2.imshow('Plate Detector', frame)
                
                # Check for quit command
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                
                # Small delay
                time.sleep(0.01)
                
        except KeyboardInterrupt:
            logger.info("Detection stopped by user")
        except Exception as e:
            logger.error(f"Error in detection loop: {e}")
        finally:
            cap.release()
            cv2.destroyAllWindows()
            self.running = False
            logger.info("Plate detector stopped")
    
    async def send_detection_to_api(self, plate_number: str, confidence: float, 
                                   image_base64: str, location: str, camera_id: str):
        """Send detection to backend API"""
        try:
            payload = {
                "plate_number": plate_number,
                "confidence": confidence,
                "image_base64": image_base64,
                "location": location,
                "camera_id": camera_id
            }
            
            response = requests.post(self.api_url, json=payload, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    if data.get("vehicle_owner"):
                        logger.info(f"Owner found: {data['vehicle_owner']['name']}")
                    else:
                        logger.info("No registered owner found for this plate")
                else:
                    logger.warning(f"API error: {data.get('message')}")
            else:
                logger.error(f"API request failed: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send detection to API: {e}")
        except Exception as e:
            logger.error(f"Error in send_detection_to_api: {e}")
    
    def stop(self):
        """Stop detection"""
        self.running = False
        logger.info("Stopping plate detector...")

def main():
    """Main function to run plate detector"""
    detector = CCTVPlateDetector()
    
    try:
        # Start detection from webcam (change source as needed)
        # source = 0  # Default webcam
        # source = "rtsp://username:password@camera_ip:port/stream"  # RTSP stream
        # source = "http://camera_ip:port/video"  # HTTP stream
        
        source = settings.WEBCAM_SOURCE
        detector.start(source=source)
        
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
    finally:
        detector.stop()

if __name__ == "__main__":
    main()