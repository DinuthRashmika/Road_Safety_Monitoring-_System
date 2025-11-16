from .schemas import Incident
from .priority import score_incident
from .repo import update_incident

async def accept_incident(incident_id: str, responder_id: str):
    await update_incident(incident_id, {"status":"accepted", "assignee_responder_id": responder_id})

def compute_scores(inc: Incident) -> Incident:
    return score_incident(inc)