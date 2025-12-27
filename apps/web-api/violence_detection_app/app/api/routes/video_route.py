from fastapi import APIRouter
from violence_detection_app.app.services. video_service import get_video_properties_service

router = APIRouter(
    prefix="/video_input",
    tags=["Video Inputting"]
)

# @router.post("/properties", response_model=SourceProperties)
# def get_video_properties(request: )