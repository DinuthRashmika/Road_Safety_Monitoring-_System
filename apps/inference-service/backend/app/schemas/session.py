from pydantic import BaseModel, Field
from typing import Optional, Dict

class SessionCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)

class SessionOut(BaseModel):
    id: str
    name: str
    startedAt: str
    endedAt: Optional[str] = None
    metrics: Dict[str, int]
