from typing import Dict, Optional
from pydantic import BaseModel, Field


class LrcnDetectionStartedResponse(BaseModel):

    session_id: str = Field(..., description="session id of the current detection session")
    websocket_url: str = Field(..., description="websocket url backend sends for the relevent connection")
    success: bool = Field(False, description="False until detection starts")
    message: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "session_id": "session_abc123",
                "websocket_url": "ws://localhost:8000/ws/detection/session_abc123",
                "message": "Detection started successfully"
            }
        }

class LRCNFrameResult(BaseModel):
    frame_number: int
    action: str
    confidence: float
    ready: bool
    is_violent: bool
    all_probabilities: Dict[str, float]
    buffer_progress: Optional[int] = None
    buffer_size: Optional[int] = None
    timestamp: str

class WebSocketMessage(BaseModel):
    type: str
    data: Dict