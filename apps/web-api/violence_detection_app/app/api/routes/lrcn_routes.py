from fastapi import APIRouter, Depends, HTTPException, Cookie, Response, BackgroundTasks, WebSocket, WebSocketDisconnect
import uuid
from typing import Optional
from datetime import datetime
from requests import Session

from violence_detection_app.app.api.schemas.video_schema import (SourceRequest, SourcePropertiesResponse )
from violence_detection_app.app.api.schemas.lrcn_schema import ( LrcnDetectionStartedResponse)
from violence_detection_app.app.api.schemas.yolo_schema import (FrameDetectionResponse)
from violence_detection_app.app.services.video_service import VideoService
from violence_detection_app.src.data_processing.video_handler import VideoHandler
from violence_detection_app.app.services.session_service import SessionService


router = APIRouter(
    prefix="/detection",
    tags=["Detection"]
)

detection_service = SessionService()

# in-memory session registry (OK for now)
ACTIVE_SESSIONS = {}

# 01. start detection
@router.post("/lrcn_start", response_model= LrcnDetectionStartedResponse)
def start_lrcn_detection(
    request: SourceRequest, 
    response: Response
):
    try:
        # 02. Create new session
        session_id = detection_service.create_session(request.source_path)
        
        # Build WebSocket URL (model is in memory.Video is open)
        websocket_url = f"ws://localhost:8000/ws/detection/{session_id}"
        
        return LrcnDetectionStartedResponse(
            session_id=session_id,
            websocket_url=websocket_url,
            success=True,
            message="LRCN Detection session created"
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start detection: {str(e)}"
        )
    
ws_router = APIRouter(tags=["WebSocket"])

@router.post("/detection/lrcn_stop")
async def stop_detection(request: StopRequest):
    detection_service.stop_session(request.session_id)
    return {"success": True, "message": "Stopped"}
    
# Client connects via WebSocket
@ws_router.websocket("/ws/detection/{session_id}")
async def websocket_detection(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for receiving real-time LRCN results
    
    Client connects here after calling /start
    """
    # 04. WebSocket handshake
    await websocket.accept()
    
    try:
        # 05. Check if session exists (Session lookup )
        # close it if a session is not found 
        session = detection_service.get_session(session_id)
        
        if not session:
            await websocket.send_json({
                "type": "error",
                "data": {"message": f"Session {session_id} not found"}
            })
            await websocket.close()
            return
        
        # 06. Start streaming if a session is found PAMALAIII
        await detection_service.process_video_stream(session_id, websocket)
        print(f"----Pamali we found a session streaming starting")
    
    except WebSocketDisconnect:
        print(f"Client disconnected from session {session_id}")
        detection_service.stop_session(session_id)
    
    except Exception as e:
        print(f"WebSocket error: {e}")
        await websocket.send_json({
            "type": "error",
            "data": {"message": str(e)}
        })
    
    finally:
        await websocket.close()


# @router.post("/stop/{session_id}")
# async def stop_detection(session_id: str):
#     """
#     Manually stop a detection session
#     """
#     try:
#         detection_service.stop_session(session_id)
#         return {
#             "success": True,
#             "message": f"Session {session_id} stopped"
#         }
#     except Exception as e:
#         raise HTTPException(
#             status_code=404,
#             detail=f"Session not found: {str(e)}"
#         )
