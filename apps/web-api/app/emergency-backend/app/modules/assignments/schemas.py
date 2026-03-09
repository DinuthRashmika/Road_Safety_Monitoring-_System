from pydantic import BaseModel

class Assignment(BaseModel):
    incident_id: str
    responder_id: str 
    status: str
    at: str