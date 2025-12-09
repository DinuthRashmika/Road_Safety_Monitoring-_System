from .schemas import Incident
from .priority import score_incident
from .repo import update_incident

async def accept_incident(incident_id: str, responder_id: str):
    # We update the responder_statuses map key for this specific responder
    # We leave the global status alone (or set it to 'active' if needed, but not 'accepted')
    
    await update_incident(incident_id, {
        f"responder_statuses.{responder_id}": "accepted"
        # We can also set global status to 'active' if it was 'new', 
        # but managing global status state is less important than user state.
    })

def compute_scores(inc: Incident) -> Incident:
    return score_incident(inc)