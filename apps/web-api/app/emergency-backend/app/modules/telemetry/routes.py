# app/modules/telemetry/routes.py
from fastapi import APIRouter, Depends
from .metrics import metrics_tiles
from app.deps import get_current_responder_doc # <-- 1. Import dependency

router = APIRouter()

@router.get("/metrics/tiles")
async def tiles(
    responder: dict = Depends(get_current_responder_doc) # <-- 2. Inject user
):
    # 3. Get user info
    role = responder.get("role")
    user_id = responder.get("id")
    
    # 4. Pass user info to the metrics function
    return await metrics_tiles(role=role, user_id=user_id)