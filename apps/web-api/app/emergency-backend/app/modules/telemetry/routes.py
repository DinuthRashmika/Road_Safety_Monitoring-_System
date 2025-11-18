# app/modules/telemetry/routes.py
from fastapi import APIRouter
from .metrics import metrics_tiles # <-- THIS IS THE FIX (was 'from .repo ...')

router = APIRouter()

@router.get("/metrics/tiles")
async def tiles():
    return await metrics_tiles()