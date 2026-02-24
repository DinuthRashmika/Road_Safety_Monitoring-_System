from pydantic import BaseModel, Field
from typing import Optional, Dict

class SessionCreate(BaseModel):
    distanceKm:float = Field(..., gt=0)
class SessionOut(BaseModel):
    id: str
    name: str
    startedAt: str
    endedAt: Optional[str] = None
    metrics: Dict[str, int]
