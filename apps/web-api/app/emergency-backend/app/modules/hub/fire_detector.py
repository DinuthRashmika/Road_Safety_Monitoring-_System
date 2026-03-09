import logging
import re
import httpx
import cv2
import numpy as np
import os
from typing import Optional
from ultralytics import YOLO
from app.config import settings

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
    drive_pattern = r"drive\.google\.com\/file\/d\/([^/]+)"
    match = re.search(drive_pattern, url)
    if match:
        file_id = match.group(1)
        return f"https://drive.google.com/uc?export=download&id={file_id}"
    
    return url

async def fire_present_from_image(image_path: Optional[str]) -> bool:
    """
    Check for fire in image - handles both URLs and Shenal's local paths
    """
    if not image_path:
        return False

    try:
        frame = None
        
        if image_path.startswith(('http://', 'https://')):
          
            target_url = _get_direct_url(image_path)
            logger.info(f"Downloading image from URL for fire detection: {target_url[:50]}...")
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            
            async with httpx.AsyncClient(follow_redirects=True) as client:
                resp = await client.get(target_url, headers=headers, timeout=15.0)
                resp.raise_for_status()
                image_bytes = resp.content
                
            np_arr = np.frombuffer(image_bytes, np.uint8)
            frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        
        else:
            clean_path = image_path.replace('\\', '/').lstrip('/')
            
            full_path = os.path.join("shenal_uploads", clean_path)
            
            logger.info(f"Looking for local image for fire detection at: {full_path}")
            
            if os.path.exists(full_path):
                frame = cv2.imread(full_path)
                if frame is not None:
                    logger.info(f"✅ Successfully loaded local image for fire detection")
                else:
                    logger.warning(f"OpenCV failed to read image: {full_path}")
            else:
                alt_path = os.path.join("shenal_uploads", "detections", os.path.basename(image_path))
                if os.path.exists(alt_path):
                    logger.info(f"Found image at alternative path: {alt_path}")
                    frame = cv2.imread(alt_path)
                else:
                    logger.warning(f"Local image not found for fire detection: {image_path}")
                    return False
        
        if frame is None:
            logger.warning(f"Could not load image: {image_path}")
            return False
            
    except Exception as e:
        logger.error(f"Image processing error for {image_path}: {e}")
        return False

    model = get_model()
    if not model:
        logger.warning("Model not available. Skipping check.")
        return False

    results = model.predict(frame, conf=settings.FIRE_CONF_THRESHOLD, verbose=False)

    if len(results) > 0 and len(results[0].boxes) > 0:
        logger.info(f"🔥 POSITIVE fire detection for {image_path}")
        return True

    logger.info(f"✅ No fire detected in {image_path}")
    return False