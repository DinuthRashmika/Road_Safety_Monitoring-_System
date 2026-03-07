from pydantic import BaseModel, Field
from datetime import datetime

class CameraCreateIn(BaseModel):
    name: str = Field(..., min_length=2)
    location: str = Field(..., min_length=2)

    # ✅ NEW: allow low/medium/high (default low)
    camera_risk_class: str = Field(
        default="low",
        pattern="^(low|medium|high)$"
    )

class CameraOut(BaseModel):
    id: str
    name: str
    location: str
    status: str
    secret_key: str

    # ✅ NEW: default prevents crash for old docs
    camera_risk_class: str = Field(
        default="low",
        pattern="^(low|medium|high)$"
    )

    createdAt: datetime