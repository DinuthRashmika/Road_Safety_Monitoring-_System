"""We can use these objects rather than dictionaries or JSON string or things that arent types correctly
"""
from pydantic import BaseModel, Field, validator
from typing import List, Literal, Optional, Dict
from enum import Enum
import time

class SourceType(str, Enum):
    """Type of video source"""
    VIDEO_FILE = "video_file"
    RTSP_STREAM = "rtsp_stream"
    WEBCAM = "webcam"
    USB_CAMERA = "usb_camera"

class SourceBase(BaseModel):
    """Base schema for video source"""
    source_id: str

class SourceRequest(BaseModel):
    """
    Request to get video source properties
    User sends: video path/URL → Backend returns properties
    """
    # source_type: SourceType = Field(..., description="Source path type")
    source_path: str = Field(..., description="File path, RTSP URL, or camera index")
    # source_name: Optional[str] = Field(None, description="Human-readable name")
    # source_location: Optional[str] = Field(None, description="Physical location")

    class Config:
        schema_extra = {
            "example": {
                "source_type": "video_file",
                "source_path": "/videos/cctv_recording.mp4",
                "source_name": "Main Gate Camera",
                "source_location": "Building A - Entrance"
            }
        }


class SourcePropertiesResponse(BaseModel):
    """
    Response containing video source properties
    Sent to UI after analyzing video metadata
    """
    # session_id: Optional[str] = None
    # source_id: str = Field(..., description="Video ID given by backend")
    fps: Optional[float] = Field(..., description="Original FPS")
    height: int = Field(..., gt=0, description="Height of original frame in pixels")
    width: int = Field(..., gt=0, description="Width of original frame in pixels")
    total_frames: Optional[int] = Field(..., gt=0, description="Total frames of the video")
    bitrate: Optional[float] = Field(..., ge=0.0, description="Video bitrate in seconds")
    duration: Optional[float] = Field(..., ge=0.0, description="Video duration in seconds")

    # @validator('duration_seconds', always=True)
    # def calculate_duration(cls, v, values):
    #     """Auto-calculate duration from fps and total_frames"""
    #     if 'fps' in values and 'total_frames' in values:
    #         fps = values['fps']
    #         total_frames = values['total_frames']
    #         if fps > 0:
    #             return total_frames / fps
    #     return v
    
    class Config:
        schema_extra = {
            "example": {
                "source_id": "source_12345",
                "source_name": "Main Gate Camera",
                "source_location": "Building A - Entrance",
                "fps": 30.0,
                "width": 1920,
                "height": 1080,
                "total_frames": 900,
                "duration": 30.0,
                "bitrate": 5000000
            }
        }



# -------------------------------------------------------------------------------------------------------------------------------

class VideoSavingRequest(BaseModel):
    # If wanna save video
    output_path: Optional[str] = Field(None, description="Path to save output video")
    


