"""
Image serving routes for local images from Shenal's uploads.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import os
from pathlib import Path
import logging
import urllib.parse

logger = logging.getLogger(__name__)
router = APIRouter()

# Base directory for Shenal's images
SHENAL_UPLOADS_DIR = Path("shenal_uploads")

@router.get("/images/{filename:path}")
async def get_image(filename: str):
    """
    Serve images from shenal_uploads folder.
    Example: /api/images/CBH%206301_151010_96a5d19f.jpg
    """
    logger.info(f"📸 Image request: {filename}")
    
    if not SHENAL_UPLOADS_DIR.exists():
        logger.error(f"Directory not found: {SHENAL_UPLOADS_DIR.absolute()}")
        raise HTTPException(status_code=404, detail="Image directory not found")
    
    # URL decode the filename
    decoded_filename = urllib.parse.unquote(filename)
    logger.info(f"Decoded filename: {decoded_filename}")
    
    # Extract just the base filename (ignore any paths)
    base_filename = os.path.basename(decoded_filename)
    logger.info(f"Searching for: {base_filename}")
    
    # Search recursively in shenal_uploads
    found_files = []
    for file_path in SHENAL_UPLOADS_DIR.rglob("*"):
        if file_path.is_file() and file_path.name.lower() == base_filename.lower():
            logger.info(f"✅ Found exact match: {file_path}")
            return FileResponse(file_path)
    
    # If exact match not found, try partial match
    for file_path in SHENAL_UPLOADS_DIR.rglob("*"):
        if file_path.is_file() and base_filename.lower() in file_path.name.lower():
            logger.info(f"✅ Found partial match: {file_path}")
            return FileResponse(file_path)
    
    # If still not found, list available files
    available = []
    for i, f in enumerate(list(SHENAL_UPLOADS_DIR.rglob("*.jpg"))[:10]):
        available.append(str(f.relative_to(SHENAL_UPLOADS_DIR)))
    
    logger.error(f"❌ Image not found: {base_filename}")
    raise HTTPException(
        status_code=404,
        detail=f"Image '{base_filename}' not found. Available images: {available}"
    )

@router.get("/images/test/{filename}")
async def test_image(filename: str):
    """Test endpoint to directly access an image by filename"""
    return await get_image(filename)

@router.get("/images/debug/list")
async def list_images():
    """List all available images"""
    if not SHENAL_UPLOADS_DIR.exists():
        return {"error": "Directory not found"}
    
    images = []
    for file_path in SHENAL_UPLOADS_DIR.rglob("*.jpg"):
        images.append(str(file_path.relative_to(SHENAL_UPLOADS_DIR)))
    
    return {
        "count": len(images),
        "images": images
    }