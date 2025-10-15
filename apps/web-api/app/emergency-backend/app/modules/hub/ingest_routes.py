from fastapi import APIRouter
from app.modules.incidents.schemas import Incident
from app.modules.incidents.service import compute_scores
from app.modules.incidents.repo import insert_incident
from app.modules.incidents.broadcast import broadcast_incident_update

router = APIRouter()

@router.post("/ingest")
async def ingest(incident: Incident):
    computed = compute_scores(incident)
    doc = computed.model_dump()
    _id = await insert_incident({**doc})
    doc["mongo_id"] = _id
    await broadcast_incident_update(doc)
    return {"id": _id}
