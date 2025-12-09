from pydantic import BaseModel, Field
from typing import Literal, Optional, Dict

from app.modules.responders.schemas import Location

Severity = Literal["low","medium","high"]
Risk = Literal["low","medium","high"]
Status = Literal["unverified", "new","accepted","enroute","arrived","resolved"]


class Accident(BaseModel):
    vehicles_involved: int = 1
    fire_present: bool = False

class Violence(BaseModel):
    participants_count: int = 1
    weapon_conf: float = 0.0

class Media(BaseModel):
    image_url: Optional[str] = None
    thumb_url: Optional[str] = None

class Incident(BaseModel):
    id: Optional[str] = None
    
    report_id: Optional[str] = None 
    
    source: Literal["traffic","violence"]
    
    reported_at: Optional[str] = Field(None, alias="timestamp_utc")
    
    location: Location
    severity_grade: Severity
    camera_risk_class: Risk
    accident: Optional[Accident] = None
    violence: Optional[Violence] = None
    media: Optional[Media] = None
    score: int = 0
    required_roles: list[str] = Field(default_factory=list) 
    
    # Global status (can be used for admin or summary)
    status: Status = "unverified"
    
    # Tracks status per responder ID: {"responder_id_123": "accepted"}
    responder_statuses: Dict[str, str] = Field(default_factory=dict)
    
    assignee_responder_id: Optional[str] = None 
    explain: list[str] = Field(default_factory=list)
    
    model_config = {
        "populate_by_name": True
    }