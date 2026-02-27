"""
YOLO Detection Microservice
Run this in YOLO venv on port 8001

Usage:
  source yolo_venv/bin/activate
  python yolo_service.py
"""

from fastapi import FastAPI
from pydantic import BaseModel
import cv2
import numpy as np
import base64
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from violence_detection_app.src.model_inference.object_detection import ObjectDetection
from violence_detection_app.src.config import config

app = FastAPI(title="YOLO Detection Service", version="1.0")

# Initialize YOLO detector once when service starts
print("🔧 Initializing YOLO detector...")
detector = ObjectDetection(
    model_path=config.YOLO_MODEL_PATH,
    confidence_threshold=0.25,
    verbose=False
)
print(" YOLO detector ready!\n")


class FrameRequest(BaseModel):
    """Request model for frame detection"""
    frame_base64: str


class DetectionResponse(BaseModel):
    """Response model for detection results"""
    success: bool
    detections: list
    total_objects: int
    error: str = None


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "YOLO Detection",
        "status": "running",
        "model": config.YOLO_MODEL_PATH,
        "confidence_threshold": 0.25
    }


@app.post("/detect", response_model=DetectionResponse)
async def detect_objects(request: FrameRequest):
    """
    Detect objects in a base64-encoded frame
    
    Args:
        request: FrameRequest with base64-encoded image
        
    Returns:
        DetectionResponse with detected objects
    """
    try:
        # Decode base64 frame
        img_data = base64.b64decode(request.frame_base64)
        nparr = np.frombuffer(img_data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            return DetectionResponse(
                success=False,
                detections=[],
                total_objects=0,
                error="Failed to decode frame"
            )
        
        # Detect objects using YOLO real model
        detections = detector.detect_in_frame(frame)
        
        return DetectionResponse(
            success=True,
            detections=detections,
            total_objects=len(detections)
        )
        
    except Exception as e:
        print(f"Detection error: {e}")
        return DetectionResponse(
            success=False,
            detections=[],
            total_objects=0,
            error=str(e)
        )


if __name__ == "__main__":
    import uvicorn
    
    print("="*70)
    print("----Starting YOLO Detection Service----")
    print("="*70)
    print(f"URL: http://localhost:8001")
    print(f"Docs: http://localhost:8001/docs")
    print(f"Model: {config.YOLO_MODEL_PATH}")
    print("="*70 + "\n")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        log_level="info"
    )

    # uvicorn main:app --port 8001 --reload