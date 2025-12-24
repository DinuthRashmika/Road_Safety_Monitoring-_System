import logging
import httpx
import cv2
import numpy as np
from typing import Optional
from ultralytics import YOLO
from app.config import settings

# Initialize logger for this module
logger = logging.getLogger(__name__)

# Global variable to hold the model so we don't reload it for every single request
_model_instance = None

def get_model():
    """
    Lazy loads the YOLO model only when needed.
    """
    global _model_instance
    if _model_instance is None:
        logger.info(f"Loading Fire Detection Model from: {settings.FIRE_MODEL_PATH}")
        try:
            _model_instance = YOLO(settings.FIRE_MODEL_PATH)
        except Exception as e:
            logger.error(f"Could not load YOLO model: {e}")
            return None
    return _model_instance

async def fire_present_from_image(image_url: Optional[str]) -> bool:
    """
    Downloads an image from a URL and runs the YOLO model to check for fire.
    """
    if not image_url:
        return False

    # 1. Download the image bytes
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(image_url, timeout=10.0)
            resp.raise_for_status()
            image_bytes = resp.content
    except Exception as e:
        logger.error(f"Failed to download image from {image_url}. Error: {e}")
        return False

    # 2. Convert bytes to OpenCV Image
    try:
        # Convert string data to numpy array
        np_arr = np.frombuffer(image_bytes, np.uint8)
        # Decode image
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        
        if frame is None:
            logger.warning("Could not decode image bytes.")
            return False
            
    except Exception as e:
        logger.error(f"Image processing error: {e}")
        return False

    # 3. Load Model and Run Inference
    model = get_model()
    if not model:
        logger.warning("Model not available. Skipping check.")
        return False

    # Run inference (verbose=False keeps standard output clean, lets us handle logging)
    results = model.predict(frame, conf=settings.FIRE_CONF_THRESHOLD, verbose=False)

    # 4. Check results
    # results[0].boxes contains the detections
    if len(results) > 0 and len(results[0].boxes) > 0:
        # If we have ANY boxes with confidence > threshold, we assume fire/accident is present.
        logger.info(f"POSITIVE detection for {image_url} - Hazard Detected")
        return True

    logger.info(f"Negative (Clear) for {image_url}")
    return False