from pydantic import BaseModel

class Assignment(BaseModel):
    incident_id: str
    unit_id: str
    status: str
    at: str
