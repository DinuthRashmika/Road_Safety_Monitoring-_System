"""
camera_service.py
─────────────────
Business logic for camera management:
  - Build RTSP URL from form fields
  - Test RTSP connection via OpenCV
  - CRUD operations against MongoDB
"""

import cv2
import uuid
from datetime import datetime
from typing import List, Optional

from violence_detection_app.app.api.schemas.rtsp_schema import (
    CameraCreateRequest,
    CameraUpdateRequest,
    CameraDocument,
    CameraTestResult,
)
from violence_detection_app.app.database.database import get_client
import os


# ── Collection helper ──────────────────────────────────────────────────────

def get_cameras_collection():
    from violence_detection_app.app.database.database import MONGODB_DB
    return get_client()[MONGODB_DB]["cameras"]


# ═══════════════════════════════════════════════
#  RTSP URL BUILDER
# ═══════════════════════════════════════════════

def build_rtsp_url(
    ip: str,
    port: int,
    stream_path: str,
    username: Optional[str] = None,
    password: Optional[str] = None,
) -> str:
    """
    Builds RTSP URL from components.

    With auth:    rtsp://username:password@ip:port/stream_path
    Without auth: rtsp://ip:port/stream_path
    """
    # Normalise stream_path — ensure it starts with /
    if not stream_path.startswith("/"):
        stream_path = f"/{stream_path}"

    if username and password:
        return f"rtsp://{username}:{password}@{ip}:{port}{stream_path}"
    else:
        return f"rtsp://{ip}:{port}{stream_path}"


def build_safe_rtsp_url(rtsp_url: str) -> str:
    """
    Returns a display-safe version of the RTSP URL
    with the password masked: rtsp://admin:***@ip:port/path
    """
    try:
        if "@" in rtsp_url:
            prefix, rest    = rtsp_url.split("@", 1)
            # prefix = rtsp://user:pass
            proto_creds     = prefix.split("://", 1)
            if ":" in proto_creds[1]:
                user, _     = proto_creds[1].split(":", 1)
                return f"{proto_creds[0]}://{user}:***@{rest}"
        return rtsp_url
    except Exception:
        return rtsp_url


# ═══════════════════════════════════════════════
#  RTSP CONNECTION TESTER
# ═══════════════════════════════════════════════

def test_rtsp_connection(rtsp_url: str) -> CameraTestResult:
    """MOCK — always returns success for testing DB save flow."""
    return CameraTestResult(
        success      = True,
        rtsp_url     = build_safe_rtsp_url(rtsp_url),
        message      = "Connection successful — stream is live",
        frame_width  = 1280,
        frame_height = 720,
        fps          = 25.0,
    )

# # TRUE TESTER
# def test_rtsp_connection(rtsp_url: str) -> CameraTestResult:
#     """
#     Attempts to open the RTSP stream with OpenCV and read one frame.
#     Returns CameraTestResult with success status and stream details.

#     Note: This is a synchronous blocking call — run it in a thread
#     when calling from async FastAPI routes (see camera_routes.py).
#     """
#     cap = None
#     try:
#         # CAP_FFMPEG backend is more reliable for RTSP
#         cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)

#         # Give it a moment to connect
#         cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 8000)   # 8s open timeout
#         cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 8000)   # 8s read timeout

#         if not cap.isOpened():
#             return CameraTestResult(
#                 success  = False,
#                 rtsp_url = build_safe_rtsp_url(rtsp_url),
#                 message  = "Could not open stream — check IP, port, credentials, and stream path",
#             )

#         ret, _ = cap.read()
#         if not ret:
#             return CameraTestResult(
#                 success  = False,
#                 rtsp_url = build_safe_rtsp_url(rtsp_url),
#                 message  = "Stream opened but could not read a frame — camera may be offline",
#             )

#         # Read stream properties
#         width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
#         height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
#         fps    = round(cap.get(cv2.CAP_PROP_FPS), 2)

#         return CameraTestResult(
#             success      = True,
#             rtsp_url     = build_safe_rtsp_url(rtsp_url),
#             message      = "Connection successful — stream is live",
#             frame_width  = width,
#             frame_height = height,
#             fps          = fps,
#         )

#     except Exception as e:
#         return CameraTestResult(
#             success  = False,
#             rtsp_url = build_safe_rtsp_url(rtsp_url),
#             message  = f"Connection error: {str(e)}",
#         )
#     finally:
#         if cap is not None:
#             cap.release()


# ═══════════════════════════════════════════════
#  CAMERA CRUD — MongoDB
# ═══════════════════════════════════════════════

async def create_camera(data: CameraCreateRequest) -> CameraDocument:
    """
    Builds RTSP URL, tests connection, saves camera to MongoDB.
    Raises ValueError if camera with same IP+port+stream already exists.
    """
    collection = get_cameras_collection()

    # Check for duplicate
    existing = await collection.find_one({
        "ip":          data.ip,
        "port":        data.port,
        "stream_path": data.stream_path,
    })
    if existing:
        raise ValueError(
            f"Camera already exists with IP {data.ip}:{data.port}{data.stream_path} "
            f"(name: {existing.get('name')})"
        )

    rtsp_url = build_rtsp_url(
        ip          = data.ip,
        port        = data.port,
        stream_path = data.stream_path,
        username    = data.username,
        password    = data.password,
    )

    now       = datetime.now().isoformat()
    camera_id = f"cam_{uuid.uuid4().hex[:10]}"

    doc = {
        "camera_id":   camera_id,
        "name":        data.name,
        "ip":          data.ip,
        "port":        data.port,
        "username":    data.username,
        "password":    data.password,
        "stream_path": data.stream_path,
        "location":    data.location,
        "rtsp_url":    rtsp_url,
        "status":      "unknown",         # will be set after test
        "created_at":  now,
        "updated_at":  now,
    }

    await collection.insert_one(doc)
    doc.pop("_id", None)
    return CameraDocument(**doc)


async def get_all_cameras() -> List[dict]:
    """Returns all cameras, passwords masked for safety."""
    collection = get_cameras_collection()
    cameras    = []
    async for doc in collection.find({}, {"_id": 0}):
        # Mask password in response
        if doc.get("password"):
            doc["password"] = "***"
        if doc.get("rtsp_url"):
            doc["rtsp_url"] = build_safe_rtsp_url(doc["rtsp_url"])
        cameras.append(doc)
    return cameras


async def get_camera_by_id(camera_id: str) -> Optional[dict]:
    """Returns a single camera by camera_id, password masked."""
    collection = get_cameras_collection()
    doc        = await collection.find_one({"camera_id": camera_id}, {"_id": 0})
    if not doc:
        return None
    if doc.get("password"):
        doc["password"] = "***"
    if doc.get("rtsp_url"):
        doc["rtsp_url"] = build_safe_rtsp_url(doc["rtsp_url"])
    return doc


async def update_camera(camera_id: str, data: CameraUpdateRequest) -> Optional[dict]:
    """
    Updates only the provided fields.
    Rebuilds RTSP URL if any URL-affecting fields changed.
    """
    collection = get_cameras_collection()

    # Get current doc (with real password) for URL rebuild
    current = await collection.find_one({"camera_id": camera_id})
    if not current:
        return None

    # Build update dict — only non-None fields
    update_fields = {k: v for k, v in data.model_dump().items() if v is not None}
    update_fields["updated_at"] = datetime.now().isoformat()

    # Rebuild RTSP URL if any relevant field changed
    url_fields = {"ip", "port", "stream_path", "username", "password"}
    if url_fields & set(update_fields.keys()):
        merged = {**current, **update_fields}
        update_fields["rtsp_url"] = build_rtsp_url(
            ip          = merged["ip"],
            port        = merged["port"],
            stream_path = merged["stream_path"],
            username    = merged.get("username"),
            password    = merged.get("password"),
        )

    await collection.update_one(
        {"camera_id": camera_id},
        {"$set": update_fields}
    )

    return await get_camera_by_id(camera_id)


async def delete_camera(camera_id: str) -> bool:
    """Deletes camera by camera_id. Returns True if deleted, False if not found."""
    collection = get_cameras_collection()
    result     = await collection.delete_one({"camera_id": camera_id})
    return result.deleted_count > 0


async def update_camera_status(camera_id: str, status: str):
    """Updates just the status field. Called after a connection test."""
    collection = get_cameras_collection()
    await collection.update_one(
        {"camera_id": camera_id},
        {"$set": {"status": status, "updated_at": datetime.now().isoformat()}}
    )


async def get_rtsp_url_raw(camera_id: str) -> Optional[str]:
    """
    Returns the real (unmasked) RTSP URL for internal use
    e.g. when starting detection on this camera.
    """
    collection = get_cameras_collection()
    doc        = await collection.find_one({"camera_id": camera_id}, {"_id": 0})
    return doc.get("rtsp_url") if doc else None