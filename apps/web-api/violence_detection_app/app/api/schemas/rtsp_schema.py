"""
camera_models.py
────────────────
Pydantic schemas for camera management.
Collection: cameras
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class CameraCreateRequest(BaseModel):
    """
    Input from the frontend form to create/register a camera.
    RTSP URL is built from these fields in the backend.
    """
    name:        str                          # e.g. "Front Gate Camera"
    ip:          str                          # e.g. "192.168.1.64"
    port:        int         = 554            # default RTSP port
    username:    Optional[str] = None         # None = no-auth URL format
    password:    Optional[str] = None
    stream_path: str         = "/stream1"     # e.g. "/Streaming/Channels/101"
    location:    Optional[str] = None         # e.g. "Zone A - Entrance"


class CameraUpdateRequest(BaseModel):
    """All fields optional — only provided fields are updated."""
    name:        Optional[str] = None
    ip:          Optional[str] = None
    port:        Optional[int] = None
    username:    Optional[str] = None
    password:    Optional[str] = None
    stream_path: Optional[str] = None
    location:    Optional[str] = None


class CameraDocument(BaseModel):
    """
    Full camera document as stored in MongoDB.
    """
    camera_id:   str
    name:        str
    ip:          str
    port:        int
    username:    Optional[str] = None
    password:    Optional[str] = None
    stream_path: str
    location:    Optional[str] = None
    rtsp_url:    str                          # built by backend
    status:      str         = "unknown"      # "online" | "offline" | "unknown"
    created_at:  str
    updated_at:  str


class CameraTestResult(BaseModel):
    """Response schema for the /cameras/test endpoint."""
    success:     bool
    rtsp_url:    str
    message:     str
    frame_width:  Optional[int]   = None
    frame_height: Optional[int]   = None
    fps:          Optional[float] = None