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


class SourceProperties(BaseModel):
    # Incoming Video Properties
    source_id: str = Field(..., description="Incoming video ID")
    source_type: SourceType
    source_path: str = Field(..., description="File path, RTSP URL, or camera index")
    source_name: Optional[str] = Field(None, description="Human-readable name")
    source_location: Optional[str] = Field(None, description="Physical location")

    fps: Optional[float] = Field(..., description="Original FPS")
    height: int = Field(..., gt=0, description="Height of original frame in pixels")
    width: int = Field(..., gt=0, description="Width of original frame in pixels")
    total_frames: Optional[int] = Field(..., gt=0, description="Total frames of the video")
    bitrate: Optional[float] = Field(..., ge=0.0, description="Video bitrate in seconds")
    duration: Optional[float] = Field(..., ge=0.0, description="Video duration in seconds")

    @validator('duration_seconds', always=True)
    def calculate_duration(cls, v, values):
        """Auto-calculate duration from fps and total_frames"""
        if 'fps' in values and 'total_frames' in values:
            fps = values['fps']
            total_frames = values['total_frames']
            if fps > 0:
                return total_frames / fps
        return v

class VideoProcessing(BaseModel):
    # While Video Processing if wanna save and display
    video_path: str = Field(..., description="Path to input video")
    output_path: Optional[str] = Field(None, description="Path to save output video")
    display: bool = Field(True, description="Whether to display video while processing") 


