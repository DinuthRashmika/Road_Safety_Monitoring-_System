import os
import uuid
from pathlib import Path
from fastapi import UploadFile, HTTPException
from app.core.config import settings
import shutil
import cv2
import numpy as np
from datetime import datetime

def ensure_dir(directory: str):
    """Ensure directory exists"""
    Path(directory).mkdir(parents=True, exist_ok=True)

async def save_image(file: UploadFile, subdir: str = "") -> str:
    """Save uploaded image and return relative path"""
    try:
        # Validate file type
        if file.content_type not in ["image/jpeg", "image/png", "image/jpg"]:
            raise HTTPException(400, "Invalid image type. Only JPEG and PNG allowed.")
        
        # Generate unique filename
        ext = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
        filename = f"{uuid.uuid4().hex}.{ext}"
        
        # Create directory structure
        rel_dir = os.path.join(settings.UPLOAD_DIR, subdir)
        ensure_dir(rel_dir)
        
        # Save file
        file_path = os.path.join(rel_dir, filename)
        with open(file_path, 'wb') as buffer:
            # Read file in chunks to handle large files
            while True:
                chunk = await file.read(8192)
                if not chunk:
                    break
                buffer.write(chunk)
        
        # Return relative path
        return os.path.join(subdir, filename)
        
    except Exception as e:
        raise HTTPException(500, f"Failed to save image: {str(e)}")

def make_public_url(request, image_path: str | None) -> str | None:
    """Convert relative image path to public URL"""
    if not image_path:
        return None
    return f"{request.base_url}static/{image_path}"

def save_detection_image(image_data: bytes, plate_number: str) -> str:
    """Save detection image to disk"""
    try:
        # Create detection directory
        detection_dir = os.path.join(settings.UPLOAD_DIR, "detections")
        ensure_dir(detection_dir)
        
        # Create subdirectory by date
        today = datetime.now().strftime("%Y-%m-%d")
        date_dir = os.path.join(detection_dir, today)
        ensure_dir(date_dir)
        
        # Generate filename
        timestamp = datetime.now().strftime("%H%M%S")
        filename = f"{plate_number}_{timestamp}_{uuid.uuid4().hex[:8]}.jpg"
        filepath = os.path.join(date_dir, filename)
        
        # Decode image data if needed
        if isinstance(image_data, bytes):
            # Save raw bytes
            with open(filepath, 'wb') as f:
                f.write(image_data)
        elif isinstance(image_data, np.ndarray):
            # Save numpy array as image
            cv2.imwrite(filepath, image_data)
        else:
            # Try to decode as base64
            try:
                import base64
                img_data = base64.b64decode(image_data)
                with open(filepath, 'wb') as f:
                    f.write(img_data)
            except:
                raise ValueError("Unsupported image data format")
        
        # Return relative path
        rel_path = os.path.join("detections", today, filename)
        return rel_path
        
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to save detection image: {e}")
        return None