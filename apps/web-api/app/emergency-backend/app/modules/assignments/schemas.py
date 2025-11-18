from pydantic import BaseModel

class Assignment(BaseModel):
    incident_id: str
    responder_id: str # Changed from unit_id
    status: str
    at: str