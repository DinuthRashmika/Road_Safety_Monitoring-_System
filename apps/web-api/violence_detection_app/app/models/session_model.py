from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime


class DetectedAction(BaseModel):
    """One unique action detected during the session."""
    action: str                        # e.g. "fighting"
    first_seen_at: str                 # ISO timestamp
    last_seen_at: str                  # ISO timestamp
    duration_seconds: float            # how long it was detected
    frame_count: int                   # how many frames it appeared in
    avg_confidence: float              # average confidence across frames
    max_confidence: float              # peak confidence
    is_violent: bool


class DetectedObject(BaseModel):
    """One unique object type detected during the session."""
    object_name: str                   # e.g. "knife"
    first_seen_at: str
    last_seen_at: str
    duration_seconds: float
    frame_count: int
    avg_confidence: float
    max_confidence: float


class ConfidenceDistribution(BaseModel):
    """Bucketed confidence distribution for analysis."""
    low: int      = 0   # 0–40%
    medium: int   = 0   # 40–70%
    high: int     = 0   # 70–90%
    critical: int = 0   # 90–100%


class CameraInfo(BaseModel):
    camera_label: str
    source_path: str
    resolution_width: Optional[int]  = None
    resolution_height: Optional[int] = None
    fps: Optional[float]             = None
    total_frames_processed: int      = 0


class SessionSummaryDocument(BaseModel):
    """
    One document saved per detection session.
    Stored in MongoDB collection: detection_sessions
    """
    # Identity
    session_id: str
    started_at: str                    # ISO timestamp
    ended_at: str                      # ISO timestamp
    duration_seconds: float
    end_reason: str                    # "user_stopped" | "video_ended"

    # Camera
    camera: CameraInfo

    # What was detected
    detected_actions: List[DetectedAction] = []
    detected_objects: List[DetectedObject] = []

    # Threat summary
    highest_threat_level: str          # CRITICAL / HIGH / MEDIUM / NONE
    total_alerts_fired: int
    alert_ids: List[str] = []          # references to alerts collection

    # Confidence distributions
    action_confidence_distribution: ConfidenceDistribution = Field(
        default_factory=ConfidenceDistribution
    )
    object_confidence_distribution: ConfidenceDistribution = Field(
        default_factory=ConfidenceDistribution
    )

    # Per-action confidence breakdown
    action_confidence_breakdown: Dict[str, float] = {}  # {"fighting": 0.84, ...}
    object_confidence_breakdown: Dict[str, float] = {}  # {"knife": 0.71, ...}