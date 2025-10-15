from pydantic import BaseModel, Field
from typing import Literal, Optional

Severity = Literal["low","medium","high"]
Risk = Literal["low","medium","high"]
Status = Literal["new","accepted","enroute","arrived","resolved"]

class Location(BaseModel):
    lat: float
    lng: float
    address: Optional[str] = None

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
    id: str
    source: Literal["traffic","violence"]
    reported_at: str
    location: Location
    severity_grade: Severity
    camera_risk_class: Risk
    accident: Optional[Accident] = None
    violence: Optional[Violence] = None
    media: Optional[Media] = None
    score: int = 0
    required_units: list[str] = Field(default_factory=list)
    status: Status = "new"
    assignee_unit_id: Optional[str] = None
    explain: list[str] = Field(default_factory=list)
