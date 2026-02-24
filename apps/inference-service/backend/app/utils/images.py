import os
import uuid
from pathlib import Path
from fastapi import UploadFile, HTTPException
from app.core.config import settings
import shutil
import cv2
import numpy as np
from datetime import datetime
import logging
import mimetypes # <--- Import this

logger = logging.getLogger(__name__)

def ensure_dir(directory: str):
    Path(directory).mkdir(parents=True, exist_ok=True)

async def save_image(file: UploadFile, subdir: str = "") -> str:
    """Save uploaded image and return relative path"""
    
    valid_types = [
        "image/jpeg", "image/png", "image/jpg", 
        "image/webp", "image/bmp", "image/gif", "image/tiff"
    ]
    
    # --- FIX: Robust Content-Type Check ---
    content_type = file.content_type
    
    # If content_type is None, try to guess from the filename
    if not content_type:
        content_type, _ = mimetypes.guess_type(file.filename)
        
    if content_type not in valid_types:
        # One last check: extension fallback
        ext = file.filename.split('.')[-1].lower() if '.' in file.filename else ''
        if ext in ['jpg', 'jpeg', 'png', 'webp']:
            pass # Accept it based on extension
        else:
            raise HTTPException(400, f"Invalid image type: {file.content_type}. Allowed: JPEG, PNG, WEBP, BMP")
    # --------------------------------------

    try:
        # Generate unique filename
        if '.' in file.filename:
            ext = file.filename.split('.')[-1].lower()
        else:
            # Fallback based on content type
            ext_map = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}
            ext = ext_map.get(content_type, "jpg")
            
        filename = f"{uuid.uuid4().hex}.{ext}"
        
        rel_dir = os.path.join(settings.UPLOAD_DIR, subdir)
        ensure_dir(rel_dir)
        
        file_path = os.path.join(rel_dir, filename)
        with open(file_path, 'wb') as buffer:
            while True:
                chunk = await file.read(8192)
                if not chunk:
                    break
                buffer.write(chunk)
        
        return os.path.join(subdir, filename)
        
    except Exception as e:
        logger.error(f"Error saving image: {str(e)}")
        raise HTTPException(500, f"Failed to save image: {str(e)}")

# ... (Keep make_public_url and save_detection_image exactly as before) ...
def make_public_url(request, image_path: str | None) -> str | None:
    if not image_path:
        return None
    normalized_path = image_path.replace("\\", "/")
    return f"{request.base_url}static/{normalized_path}"

def save_detection_image(image_data: bytes, plate_number: str) -> str:
    try:
        detection_dir = os.path.join(settings.UPLOAD_DIR, "detections")
        ensure_dir(detection_dir)
        
        today = datetime.now().strftime("%Y-%m-%d")
        date_dir = os.path.join(detection_dir, today)
        ensure_dir(date_dir)
        
        timestamp = datetime.now().strftime("%H%M%S")
        filename = f"{plate_number}_{timestamp}_{uuid.uuid4().hex[:8]}.jpg"
        filepath = os.path.join(date_dir, filename)
        
        if isinstance(image_data, bytes):
            with open(filepath, 'wb') as f:
                f.write(image_data)
        elif isinstance(image_data, np.ndarray):
            cv2.imwrite(filepath, image_data)
        else:
            try:
                import base64
                img_data = base64.b64decode(image_data)
                with open(filepath, 'wb') as f:
                    f.write(img_data)
            except:
                raise ValueError("Unsupported image data format")
        
        rel_path = os.path.join("detections", today, filename)
        return rel_path
        
    except Exception as e:
        logger.error(f"Failed to save detection image: {e}")
        return None