from fastapi import APIRouter

router = APIRouter(
    prefix="/detect",
    tags=["Object Detection"]
)