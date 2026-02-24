from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class CameraCreateIn(BaseModel):
    name: str = Field(..., min_length=2)
    location: str = Field(..., min_length=2)

class CameraOut(BaseModel):
    id: str
    name: str
    location: str
    status: str
    secret_key: str  # Used by the camera to authenticate (optional)
    createdAt: datetime