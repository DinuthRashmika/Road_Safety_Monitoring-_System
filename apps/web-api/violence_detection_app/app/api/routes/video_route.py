"""Endpoints gonna hit by our user"""
from fastapi import APIRouter, Depends, HTTPException, Cookie, Response, BackgroundTasks
import uuid
from typing import Optional
from datetime import datetime

from requests import Session
# # db file
# from violence_detection_app.app.database.database import get_db, SessionLocal
# # database models
# from violence_detection_app.app.models.video_model import Video
# backend schemas
from violence_detection_app.app.api.schemas.video_schema import ( SourceRequest, SourcePropertiesResponse )
from violence_detection_app.app.api.schemas.yolo_schema import (FrameDetectionResponse)
# from violence_detection_app.app.services.video_service import get_video_source
# from violence_detection_app.app.services import video_service
from violence_detection_app.app.services.video_service import VideoService
from violence_detection_app.src.data_processing.video_handler import VideoHandler


"""Different endpoints in different files, and different API prefixes for them"""

router = APIRouter(
    prefix="/source",
    tags=["Video Sources"]
)

video_service = VideoService()

# Create session id
def create_session_id(session_id: Optional[str] = Cookie(None)):
    if not session_id:
        session_id = str(uuid.uuid4())
    return session_id

# Get Source URL
@router.post("/properties", response_model=SourcePropertiesResponse)
def get_source_properties(
    request: SourceRequest,
    # background_tasks: BackgroundTasks, # background tasks independaltly from main thread
    response: Response,
    # session_id: str = Depends(create_session_id), #session_id is a str, depends on get_session_id
    # db: Session = Depends(get_db)
):
    # response.set_cookie(key="session_id", value=session_id, httponly=True) #store session_id so can use it later
    
    # if saving in a db according to a db schema
    # source_id = str(uuid.uuid4())

    try:
        return video_service.get_source_properties(request)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))















# @router.post("/properties", response_model=SourceProperties)
# def get_video_properties(request: )