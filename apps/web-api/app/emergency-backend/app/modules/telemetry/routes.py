from fastapi import APIRouter
from .repo import metrics_tiles

router = APIRouter()

@router.get("/metrics/tiles")
async def tiles():
    return await metrics_tiles()
