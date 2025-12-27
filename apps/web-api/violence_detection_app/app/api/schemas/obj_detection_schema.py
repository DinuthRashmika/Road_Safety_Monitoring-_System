import time
from typing import Dict, List
from pydantic import BaseModel, Field, validator


class FrameDetections(BaseModel):
    #Per detection
    object: str = Field(..., description="detected object name")
    clas_id: int = Field(..., description="detected class id")
    confidence = float = Field(..., description="detected confidence")
    bbox: List[float] = Field(..., description="bounding box of the detected object")

    @validator('bbox')
    def validate_bbox(cls, v):
        x1, y1, x2, y2 = v
        if x2 <= x1 or y2 <= y1:
            raise ValueError(f"Invalid bounding box {v}")
        

class FrameAnalysis(BaseModel):
    # Per frame analysis (frame can have multiple detections)
    frame_index: int = Field(None, ge=0, description="Frame index in video/stream")
    timestamp: time = Field(default_factory=time.time, description="timestamp")
    object_detections: List[FrameDetections] = Field(default_factory=list, description="All object detections details in this frame") 
    # action_detections: List[FrameDetections] = Field(default_factory=list, description="All action detections details in this frame") 
    object_detection_count: int = Field(0, ge=0, description="Number of objects detected in the frame")
    has_violence: bool = Field(False, description="Any violent objects detected in that frame")

    @validator('detection_count', always=True)
    def set_detection_count(cls, v, values):
        """Auto-calculate detection count from detections list"""
        if 'detections' in values:
            return len(values['detections'])
        return v
    
    @validator('has_violence', always=True)
    def set_has_violence(cls, v, values):
        """Auto-determine if violence detected"""
        if 'detections' in values:
            return len(values['detections']) > 0
        return v
    
class VideoAnalysis(BaseModel):
    # Complete stream/video analysis by YOLO
    video_id: str
    frames_processed: int
    frames_with_detections: int
    total_detections: int
    detections_by_object: Dict[str, int] = Field(default_factory=dict)

