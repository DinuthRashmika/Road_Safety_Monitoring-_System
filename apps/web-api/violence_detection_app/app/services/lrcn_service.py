import asyncio
import cv2
import uuid
from typing import Dict, Optional
from datetime import datetime
import numpy as np

from violence_detection_app.src.model_inference.action_recognition import ActionRecognition
from violence_detection_app.src.config import config


class DetectionSession:
    """Manages a single detection session. Opens video, loads model, cleam everything up"""
    
    def __init__(self, session_id: str, source_path: str):
        self.session_id = session_id
        self.source_path = source_path
        self.is_active = False
        self.action_detector = None
        self.video_cap = None
        
    def initialize(self):
        """Initialize LRCN detector and video capture"""
        try:
            # Initialize LRCN
            self.action_detector = ActionRecognition(
                model_path=config.LRCN_MODEL_PATH,
                confidence_threshold=config.LRCN_CONFIDENCE_THRESHOLD,
                sequence_length=config.SEQUENCE_LENGTH,
                verbose=False
            )
            
            # Open video
            self.video_cap = cv2.VideoCapture(self.source_path)
            
            if not self.video_cap.isOpened():
                raise Exception(f"Cannot open video source: {self.source_path}")
            
            self.is_active = True
            return True
            
        except Exception as e:
            print(f"Error initializing session {self.session_id}: {e}")
            return False
    
    def cleanup(self):
        """Cleanup resources"""
        self.is_active = False
        if self.video_cap:
            self.video_cap.release()
        if self.action_detector:
            self.action_detector.reset_buffer()


class DetectionService:
    """Service to manage detection sessions"""
    
    def __init__(self):
        # Keeps all active sessions in memory.
        self.active_sessions: Dict[str, DetectionSession] = {}
    
    def create_session(self, source_path: str) -> str:
        """Create a new detection session"""
        session_id = f"session_{uuid.uuid4().hex[:12]}"
        session = DetectionSession(session_id, source_path)
        
        if session.initialize(): # Stores the session in active_sessions
            self.active_sessions[session_id] = session
            return session_id
        else:
            raise Exception("Failed to initialize detection session")
    
    def get_session(self, session_id: str) -> Optional[DetectionSession]:
        """give a session ID, get the/an active session object."""
        return self.active_sessions.get(session_id)
    
    def stop_session(self, session_id: str):
        """Stop and cleanup a session"""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            session.cleanup()
            del self.active_sessions[session_id]
    
    async def process_video_stream(self, session_id: str, websocket):
        """
        Process video stream and send LRCN results via WebSocket
        
        Args:
            session_id: Session identifier
            websocket: FastAPI WebSocket connection
        """
        session = self.get_session(session_id)
        
        if not session:
            await websocket.send_json({
                "type": "error",
                "data": {"message": "Session not found"}
            })
            return
        
        frame_count = 0
        
        try:
            # Send start status
            await websocket.send_json({
                "type": "status",
                "data": {
                    "message": "Processing started",
                    "session_id": session_id
                }
            })
            
            while session.is_active:
                ret, frame = session.video_cap.read()
                
                if not ret:
                    # End of video
                    await websocket.send_json({
                        "type": "complete",
                        "data": {
                            "message": "Video processing complete",
                            "total_frames": frame_count,
                            "statistics": session.action_detector.get_statistics()
                        }
                    })
                    break
                
                frame_count += 1
                
                # Process frame with LRCN
                result = session.action_detector.process_single_frame(frame)
                
                # Prepare WebSocket message
                ws_message = {
                    "type": "lrcn_result",
                    "data": {
                        "frame_number": frame_count,
                        "action": result['action'],
                        "confidence": result['confidence'],
                        "ready": result['ready'],
                        "is_violent": result['is_violent'],
                        "all_probabilities": result['all_probabilities'],
                        "timestamp": datetime.now().isoformat()
                    }
                }
                
                # Add buffer info if not ready
                if not result['ready']:
                    ws_message['data']['buffer_progress'] = result.get('buffer_progress', 0)
                    ws_message['data']['buffer_size'] = result.get('buffer_size', 0)
                
                # Send via WebSocket
                await websocket.send_json(ws_message)
                
                # Small delay to prevent overwhelming the connection
                await asyncio.sleep(0.01)
        
        except Exception as e:
            print(f"Error processing video: {e}")
            await websocket.send_json({
                "type": "error",
                "data": {"message": str(e)}
            })
        
        finally:
            # Cleanup
            self.stop_session(session_id)


# Global service instance
detection_service = DetectionService()