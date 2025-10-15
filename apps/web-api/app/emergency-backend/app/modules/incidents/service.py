from .schemas import Incident
from .priority import score_incident
from .repo import update_incident

async def accept_incident(incident_id: str, unit_id: str):
    await update_incident(incident_id, {"status":"accepted", "assignee_unit_id": unit_id})

def compute_scores(inc: Incident) -> Incident:
    return score_incident(inc)
