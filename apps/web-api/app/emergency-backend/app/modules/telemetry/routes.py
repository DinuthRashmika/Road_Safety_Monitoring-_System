from fastapi import APIRouter, Depends
from .metrics import metrics_tiles
from app.deps import get_current_responder_doc

router = APIRouter()

@router.get("/metrics/tiles")
async def tiles(
    responder: dict = Depends(get_current_responder_doc) 
):
    role = responder.get("role")
    user_id = responder.get("id")
    location = responder.get("location") # Pass location for distance calculations
    
    return await metrics_tiles(role=role, user_id=user_id, location=location)