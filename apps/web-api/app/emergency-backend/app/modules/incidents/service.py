from .schemas import Incident
from .priority import score_incident
from .repo import update_incident

async def accept_incident(incident_id: str, responder_id: str):
    
    await update_incident(incident_id, {
        f"responder_statuses.{responder_id}": "accepted"
    })

def compute_scores(inc: Incident) -> Incident:
    return score_incident(inc)