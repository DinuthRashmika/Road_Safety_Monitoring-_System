from __future__ import annotations

from fastapi import APIRouter, HTTPException, Body
from pydantic import ValidationError
from bson import ObjectId

from app.modules.incidents.schemas import Incident
from app.modules.incidents.service import compute_scores
from app.modules.incidents.repo import insert_incident
from app.modules.incidents.broadcast import broadcast_incident_update

router = APIRouter()


def _coerce_score(value) -> int:
    """Accept int/float/str; round to nearest int and clamp 0..100."""
    try:
        s = int(round(float(value)))
    except Exception:
        raise HTTPException(status_code=422, detail="`score` must be numeric (0..100).")
    return max(0, min(100, s))


def _sanitize(o):
    """Recursively convert ObjectId -> str so json.dumps will work."""
    if isinstance(o, ObjectId):
        return str(o)
    if isinstance(o, dict):
        return {k: _sanitize(v) for k, v in o.items()}
    if isinstance(o, list):
        return [_sanitize(v) for v in o]
    return o


@router.post("/ingest")
async def ingest(payload: dict = Body(...)):
    """
    Accept Incident payload. If 'score' is present, use it (rounded int).
    required_units are computed server-side from the incident details.
    """
    try:
        provided_score = payload.pop("score", None)

        inc = Incident(**payload)

        inc = compute_scores(inc)

        if provided_score is not None:
            inc.score = _coerce_score(provided_score)

        doc = inc.model_dump()
        inserted_id = await insert_incident(doc)

        out = _sanitize({**doc, "mongo_id": inserted_id})
        await broadcast_incident_update(out)

        return {"id": str(inserted_id)}

    except ValidationError as ve:
        raise HTTPException(status_code=422, detail=ve.errors())
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingest failed: {e}")
