from pydantic import BaseModel, Field
from typing import Literal, Optional, Dict, List

from app.modules.responders.schemas import Location

Severity = Literal["low","medium","high"]
Risk = Literal["low","medium","high"]
Status = Literal["unverified", "new","accepted","enroute","arrived","resolved"]

class DetectedObject(BaseModel):
    """Individual object detected in human behavior alert"""
    object: str
    confidence: float

class ViolenceDetails(BaseModel):
    """Enhanced violence details for human behavior alerts"""
    participants_count: int = 1
    weapon_conf: float = 0.0
    
    threat_score: Optional[float] = None
    has_weapon: Optional[bool] = None
    action_confidence: Optional[float] = None
    sustained_seconds: Optional[float] = None
    action: Optional[str] = None
    objects_detected: Optional[List[DetectedObject]] = None
    threat_level: Optional[str] = None
    action_contribution: Optional[float] = None
    object_contribution: Optional[float] = None
    synergy_bonus: Optional[float] = None
    reasoning: Optional[str] = None
    human_summary: Optional[str] = None

class Accident(BaseModel):
    vehicles_involved: int = 1
    fire_present: bool = False

class Violence(BaseModel):
    """Original violence class - kept for backward compatibility"""
    participants_count: int = 1
    weapon_conf: float = 0.0

class Media(BaseModel):
    image_url: Optional[str] = None
    thumb_url: Optional[str] = None

class Incident(BaseModel):
    id: Optional[str] = None
    
    report_id: Optional[str] = None 
    
    source: Literal["traffic","violence", "human_behavior"] 
    
    reported_at: Optional[str] = Field(None, alias="timestamp_utc")
    
    location: Location
    severity_grade: Severity
    camera_risk_class: Risk
    accident: Optional[Accident] = None
    violence: Optional[ViolenceDetails] = None  
    media: Optional[Media] = None
    score: int = 0
    required_roles: list[str] = Field(default_factory=list) 
    
    status: Status = "unverified"
    
    responder_statuses: Dict[str, str] = Field(default_factory=dict)
    
    assigned_responders: List[Dict] = Field(default_factory=list)

    role_statuses: Dict[str, str] = Field(default_factory=dict)
    
    assignee_responder_id: Optional[str] = None 
    explain: list[str] = Field(default_factory=list)
    
    pending_responder_roles: Optional[list[str]] = None
    
    model_config = {
        "populate_by_name": True
    }