from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Response
from violence_detection_app.app.api.schemas.video_schema import SourceRequest
from violence_detection_app.app.api.schemas.lrcn_schema import LrcnDetectionStartedResponse
from violence_detection_app.app.services.session_service import SessionService
from violence_detection_app.src.config.config import DATA_DIR
import os
import shutil
from fastapi import UploadFile, File
from fastapi.responses import JSONResponse


router = APIRouter(
    prefix="/detection",
    tags=["Detection"]
)

ws_router = APIRouter(tags=["WebSocket"])

detection_service = SessionService()

# UPLOAD_DIR = "uploaded_videos"
# os.makedirs(UPLOAD_DIR, exist_ok=True)

UPLOAD_DIR = os.path.join(DATA_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Upload videos
@router.post("/upload_video")
async def upload_video(file: UploadFile = File(...)):
    allowed = {".mp4", ".avi", ".mov", ".mkv", ".webm"}
    ext     = os.path.splitext(file.filename)[1].lower()

    if ext not in allowed:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": f"File type {ext} not allowed"}
        )

    save_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(save_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    abs_path = os.path.abspath(save_path)
    return {
        "success":   True,
        "filename":  file.filename,
        "path":      abs_path,
        "size_mb":   round(os.path.getsize(abs_path) / (1024 * 1024), 2),
    }


# Start detection
@router.post("/lrcn_start", response_model=LrcnDetectionStartedResponse)
def start_lrcn_detection(request: SourceRequest, response: Response):
    """
    Start a new detection session
    
    Creates a session with LRCN model and returns WebSocket URL
    """
    try:
        # Create new session
        session_id = detection_service.create_session(request.source_path)
        
        # Build WebSocket URL
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


# Stop detection
@router.post("/lrcn_stop")
async def stop_detection(request: SourceRequest):
    """
    Stop a running detection session
    
    Request body should contain session_id in source_path field
    """
    try:
        # Extract session_id from source_path
        session_id = request.source_path
        
        # Get session
        session = detection_service.get_session(session_id)
        
        if not session:
            raise HTTPException(
                status_code=404,
                detail=f"Session {session_id} not found or already stopped"
            )
        
        # Set stop flag
        session.stop()
        
        # Stop and cleanup
        detection_service.stop_session(session_id)
        
        return {
            "success": True,
            "message": "Detection stopped successfully",
            "session_id": session_id
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Error stopping detection: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to stop detection: {str(e)}"
        )


# WebSocket endpoint
@ws_router.websocket("/ws/detection/{session_id}")
async def websocket_detection(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for receiving real-time detection results
    
    Client connects here after calling /lrcn_start
    """
    # Accept WebSocket connection
    await websocket.accept()
    
    try:
        # Check if session exists
        session = detection_service.get_session(session_id)
        
        if not session:
            await websocket.send_json({
                "type": "error",
                "data": {"message": f"Session {session_id} not found"}
            })
            await websocket.close()
            return
        
        # Start streaming detection results
        print(f"WebSocket connected for session {session_id}")
        await detection_service.process_video_stream(session_id, websocket)
    
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
        

@router.get("/alerts")
async def get_alerts():
    try:
        from violence_detection_app.app.database.database import get_alerts_collection
        collection = get_alerts_collection()
        alerts = await collection.find().sort("timestamp", -1).to_list(length=200)
        for a in alerts:
            a["_id"] = str(a["_id"])
        return {"success": True, "alerts": alerts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/detections")
async def get_sessions():
    from violence_detection_app.app.database.database import get_detections_collection
    collection = get_detections_collection()
    sessions = await collection.find().sort("started_at", -1).to_list(length=200)
    for s in sessions:
        s["_id"] = str(s["_id"])
    return {"success": True, "sessions": sessions}