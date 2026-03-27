from typing import List, Dict, Optional
from enum import Enum
from pydantic import BaseModel, Field, validator
import time
from violence_detection_app.app.api.schemas.video_schema import SourcePropertiesResponse


class DetectionBase(BaseModel):
    """Base schema for detection"""
    object: str
    class_id: int
    confidence: float
    bbox: List[float]

    @validator("bbox")
    def validate_bbox(cls, v):
        if len(v) != 4:
            raise ValueError("bbox must be [x1, y1, x2, y2]")
        x1, y1, x2, y2 = v
        if x2 <= x1 or y2 <= y1:
            raise ValueError("Invalid bbox coordinates")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "object": "knife",
                "class_id": 43,
                "confidence": 0.87,
                "bbox": [100.5, 200.3, 350.8, 450.2]
            }
        }

class FrameDetectionResponse(BaseModel):
    """
    Detection results for a single frame
    One frame can have multiple detections (multiple objects)
    """
    frame_index: int = Field(..., ge=0, description="Frame number in video/stream")
    # timestamp: time = Field(default_factory=time.time, description="timestamp")
    object_detections: List[DetectionBase] = Field(default_factory=list, description="All object detections details in this frame") 
    # action_detections: List[FrameDetections] = Field(default_factory=list, description="All action detections details in this frame") 
    # object_detection_count: int = Field(0, ge=0, description="Number of objects detected in the frame")
    has_violence: bool = Field(False, description="Any violent objects detected in that frame")
    
    @validator('has_violence', always=True)
    def set_has_violence(cls, v, values):
        """Auto-determine if violence detected"""
        if 'detections' in values:
            return len(values['detections']) > 0
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "frame_index": 125,
                "timestamp": 1640000000.0,
                "detections": [
                    {
                        "object": "knife",
                        "class_id": 43,
                        "confidence": 0.87,
                        "bbox": [100.5, 200.3, 350.8, 450.2]
                    }
                ],
                "detection_count": 1,
                "has_violence": True
            }
        }

    
class VideoStatsSchema(BaseModel):
    video_id: str

    frames_processed: int
    frames_with_detections: int
    total_detections: int

    # detections_by_object: Dict[str, int]        # { 'knife': 10, 'gun': 3 }
    total_objects_detected: List[str]          # ['knife', 'gun']
    # avg_confidences: Dict[str, float]  # { 'knife': 0.85, 'gun': 0.92 }
    
# class ObjectDetectionCountSchema(BaseModel):
#     object: str = Field(..., description="Object name")
#     count: int = Field(..., ge=0, description="Total detections of this object")

# class ObjectAvgConfidence(BaseModel):
#     object: str = Field(..., description="Object name")
#     avg_confidence: float = Field(..., ge=0.0, le=1.0, description="Average confidence")

class PerObjectStatisticsSchema(BaseModel):
    """
    Statistics for a specific object type across all frames
    E.g., knife statistics, gun statistics
    """
    object_name: str = Field(..., description="Object type (e.g., 'knife')")
    total_detections: int = Field(..., ge=0, description="Total times this object was detected")
    # frames_with_object: int = Field(..., ge=0, description="Number of frames containing this object")
    avg_confidence: float = Field(..., ge=0.0, le=1.0, description="Average confidence across all detections")
    min_confidence: float = Field(..., ge=0.0, le=1.0, description="Minimum confidence")
    max_confidence: float = Field(..., ge=0.0, le=1.0, description="Maximum confidence")
    presence_percentage: Optional[float] = Field(None, ge=0.0, le=100.0, description="% of frames with this object")


class CompleteVideoStatsFromYoloResponse(BaseModel):
    """
    Final analysis results after user stops detection (presses 'q')
    Complete summary of entire video/stream session
    """
    video_id: str
    source_properties: Optional[SourcePropertiesResponse]
    video_stats: VideoStatsSchema
    per_object_stats: Dict[str, PerObjectStatisticsSchema]
    detected_frames: List[FrameDetectionResponse]

    class Config:
        schema_extra = {
            "example": {
                "source_id": "source_12345",
                "session_start": "2025-01-01T10:00:00",
                "session_end": "2025-01-01T10:05:00",
                "total_frames_processed": 300,
                "frames_with_violence": 45,
                "violence_percentage": 15.0,
                "total_detections": 67,
                "unique_objects_detected": ["knife", "gun"],
                "object_statistics": {
                    "knife": {
                        "object_name": "knife",
                        "total_detections": 45,
                        "frames_with_object": 38,
                        "avg_confidence": 0.85,
                        "min_confidence": 0.67,
                        "max_confidence": 0.95,
                        "presence_percentage": 12.5
                    }
                },
                "threat_level": "HIGH"
            }
        }
