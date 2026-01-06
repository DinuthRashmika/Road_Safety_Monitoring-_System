# from fastapi import APIRouter, Depends, HTTPException, Cookie, Response, BackgroundTasks, WebSocket, WebSocketDisconnect
# import uuid
# from typing import Optional
# from datetime import datetime
# from requests import Session

# from violence_detection_app.app.api.schemas.video_schema import (SourceRequest, SourcePropertiesResponse )
# from violence_detection_app.app.api.schemas.lrcn_schema import ( LrcnDetectionStartedResponse)
# from violence_detection_app.app.api.schemas.yolo_schema import (FrameDetectionResponse)
# from violence_detection_app.app.services.video_service import VideoService
# from violence_detection_app.src.data_processing.video_handler import VideoHandler
# from violence_detection_app.app.services.lrcn_service import DetectionService

# detection_service = DetectionService()

# # in-memory session registry (OK for now)
# ACTIVE_SESSIONS = {}

# ws_router = APIRouter(tags=["WebSocket"])
    
# @ws_router.websocket("/ws/detection/{session_id}")
# async def websocket_detection(websocket: WebSocket, session_id: str):
#     """
#     WebSocket endpoint for receiving real-time LRCN results
    
#     Client connects here after calling /start
#     """
#     await websocket.accept()
    
#     try:
#         # Check if session exists
#         session = detection_service.get_session(session_id)
        
#         if not session:
#             await websocket.send_json({
#                 "type": "error",
#                 "data": {"message": f"Session {session_id} not found"}
#             })
#             await websocket.close()
#             return
        
#         # Start processing video and streaming results
#         await detection_service.process_video_stream(session_id, websocket)
    
#     except WebSocketDisconnect:
#         print(f"Client disconnected from session {session_id}")
#         detection_service.stop_session(session_id)
    
#     except Exception as e:
#         print(f"WebSocket error: {e}")
#         await websocket.send_json({
#             "type": "error",
#             "data": {"message": str(e)}
#         })
    
#     finally:
#         await websocket.close()

