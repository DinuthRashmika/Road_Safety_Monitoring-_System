"""
camera_routes.py
────────────────
FastAPI router for camera management.

Endpoints:
  POST   /cameras/test          — test RTSP without saving
  POST   /cameras               — create + save camera
  GET    /cameras               — list all cameras
  GET    /cameras/{camera_id}   — get single camera
  PUT    /cameras/{camera_id}   — update camera
  DELETE /cameras/{camera_id}   — delete camera
  POST   /cameras/{camera_id}/test — test an existing saved camera
"""

import asyncio
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from typing import List

from violence_detection_app.app.api.schemas.rtsp_schema import (
    CameraCreateRequest,
    CameraUpdateRequest,
    CameraTestResult,
)
from violence_detection_app.app.services.rtsp_service import (
    build_rtsp_url,
    test_rtsp_connection,
    create_camera,
    get_all_cameras,
    get_camera_by_id,
    update_camera,
    delete_camera,
    update_camera_status,
    get_rtsp_url_raw,
)

router = APIRouter(
    prefix="/cameras", 
    tags=["Cameras"]
)


# ═══════════════════════════════════════════════
#  TEST RTSP WITHOUT SAVING
#  Frontend calls this first before registering
# ═══════════════════════════════════════════════

@router.post("/test", response_model=CameraTestResult)
async def test_rtsp(data: CameraCreateRequest):
    """
    Builds RTSP URL from form fields and tests the connection.
    Does NOT save anything to the database.

    Use this so the user can verify connection before registering the camera.
    """
    rtsp_url = build_rtsp_url(
        ip          = data.ip,
        port        = data.port,
        stream_path = data.stream_path,
        username    = data.username,
        password    = data.password,
    )

    # Run blocking OpenCV call in a thread so we don't block the event loop
    result = await asyncio.get_event_loop().run_in_executor(
        None, test_rtsp_connection, rtsp_url
    )
    return result


# ═══════════════════════════════════════════════
#  CREATE CAMERA
# ═══════════════════════════════════════════════

@router.post("", status_code=201)
async def add_camera(data: CameraCreateRequest):
    """
    Creates, tests, and saves a camera to MongoDB.

    Flow:
      1. Check for duplicates
      2. Build RTSP URL
      3. Save to DB with status = "unknown"
      4. Test connection in background — updates status to online/offline

    Returns the saved camera document immediately (don't wait for test result).
    """
    try:
        camera = await create_camera(data)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save camera: {str(e)}")

    # Test connection in background — updates status field asynchronously
    async def background_test():
        rtsp_url = build_rtsp_url(
            ip          = data.ip,
            port        = data.port,
            stream_path = data.stream_path,
            username    = data.username,
            password    = data.password,
        )
        loop   = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, test_rtsp_connection, rtsp_url)
        status = "online" if result.success else "offline"
        await update_camera_status(camera.camera_id, status)
        print(f"[CAM] {camera.name} connection test → {status}")

    asyncio.ensure_future(background_test())

    return {
        "success":   True,
        "message":   "Camera registered successfully. Testing connection in background...",
        "camera":    camera.model_dump(),
    }


# ═══════════════════════════════════════════════
#  LIST ALL CAMERAS
# ═══════════════════════════════════════════════

@router.get("")
async def list_cameras():
    """Returns all registered cameras. Passwords are masked."""
    cameras = await get_all_cameras()
    return {
        "success": True,
        "count":   len(cameras),
        "cameras": cameras,
    }


# ═══════════════════════════════════════════════
#  GET SINGLE CAMERA
# ═══════════════════════════════════════════════

@router.get("/{camera_id}")
async def get_camera(camera_id: str):
    """Returns a single camera by ID."""
    camera = await get_camera_by_id(camera_id)
    if not camera:
        raise HTTPException(status_code=404, detail=f"Camera {camera_id} not found")
    return {"success": True, "camera": camera}


# ═══════════════════════════════════════════════
#  UPDATE CAMERA
# ═══════════════════════════════════════════════

@router.put("/{camera_id}")
async def edit_camera(camera_id: str, data: CameraUpdateRequest):
    """
    Updates only the provided fields.
    RTSP URL is automatically rebuilt if IP, port, path, or credentials change.
    """
    updated = await update_camera(camera_id, data)
    if not updated:
        raise HTTPException(status_code=404, detail=f"Camera {camera_id} not found")
    return {
        "success": True,
        "message": "Camera updated successfully",
        "camera":  updated,
    }


# ═══════════════════════════════════════════════
#  DELETE CAMERA
# ═══════════════════════════════════════════════

@router.delete("/{camera_id}")
async def remove_camera(camera_id: str):
    """Permanently deletes a camera from the database."""
    deleted = await delete_camera(camera_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Camera {camera_id} not found")
    return {
        "success":   True,
        "message":   f"Camera {camera_id} deleted successfully",
        "camera_id": camera_id,
    }


# ═══════════════════════════════════════════════
#  TEST EXISTING SAVED CAMERA
# ═══════════════════════════════════════════════

@router.post("/{camera_id}/test", response_model=CameraTestResult)
async def test_existing_camera(camera_id: str):
    """
    Tests the connection of an already-saved camera.
    Updates its status in the database after the test.
    """
    rtsp_url = await get_rtsp_url_raw(camera_id)
    if not rtsp_url:
        raise HTTPException(status_code=404, detail=f"Camera {camera_id} not found")

    result = await asyncio.get_event_loop().run_in_executor(
        None, test_rtsp_connection, rtsp_url
    )

    # Update status in DB
    status = "online" if result.success else "offline"
    await update_camera_status(camera_id, status)

    return result