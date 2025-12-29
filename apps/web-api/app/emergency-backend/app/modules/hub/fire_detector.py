import logging
import re
import httpx
import cv2
import numpy as np
from typing import Optional
from ultralytics import YOLO
from app.config import settings

# Initialize logger
logger = logging.getLogger(__name__)

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

def _get_direct_url(url: str) -> str:
    """
    Converts viewer links (like Google Drive) into direct download links.
    """
    # Detect Google Drive 'View' links
    # Pattern: drive.google.com/file/d/FILE_ID/view
    drive_pattern = r"drive\.google\.com\/file\/d\/([^/]+)"
    match = re.search(drive_pattern, url)
    if match:
        file_id = match.group(1)
        # Convert to direct download format
        return f"https://drive.google.com/uc?export=download&id={file_id}"
    
    return url

async def fire_present_from_image(image_url: Optional[str]) -> bool:
    """
    Downloads an image (handling Drive links) and runs YOLO to check for fire.
    """
    if not image_url:
        return False

    # 1. Convert URL if it's a Google Drive link
    target_url = _get_direct_url(image_url)

    # 2. Download the image bytes
    try:
        # Use a real browser User-Agent to prevent blocking by Flickr/etc
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        # 'follow_redirects=True' is crucial for shorteners or download keys
        async with httpx.AsyncClient(follow_redirects=True) as client:
            resp = await client.get(target_url, headers=headers, timeout=15.0)
            resp.raise_for_status()
            image_bytes = resp.content
            
    except Exception as e:
        logger.error(f"Failed to download image from {target_url}. Error: {e}")
        return False

    # 3. Convert bytes to OpenCV Image
    try:
        np_arr = np.frombuffer(image_bytes, np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        
        if frame is None:
            # This happens if the link was HTML (not an image) or corrupt
            logger.warning(f"Could not decode image. Content-Type was: {resp.headers.get('content-type')}")
            return False
            
    except Exception as e:
        logger.error(f"Image processing error: {e}")
        return False

    # 4. Load Model and Run Inference
    model = get_model()
    if not model:
        logger.warning("Model not available. Skipping check.")
        return False

    results = model.predict(frame, conf=settings.FIRE_CONF_THRESHOLD, verbose=False)

    # 5. Check results
    if len(results) > 0 and len(results[0].boxes) > 0:
        logger.info(f"POSITIVE detection for {image_url} - Hazard Detected")
        return True

    logger.info(f"Negative (Clear) for {image_url}")
    return False