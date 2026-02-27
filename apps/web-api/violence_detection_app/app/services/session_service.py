import asyncio
from datetime import datetime
from typing import Dict, Optional
import uuid
import cv2
import base64
import httpx

from violence_detection_app.app.services.detection_session import DetectionSession
from violence_detection_app.src.fusion.model_stats import ModelStatistics

class SessionService:
    """Manages many DetectionSession objects (many sessions)"""
    
    def __init__(self):
        # Keeps all active sessions in memory.
        self.active_sessions: Dict[str, DetectionSession] = {}
        
        # YOLO service configuration
        self.yolo_service_url = "http://localhost:8001/detect"
        self.yolo_enabled = True  # Set to False to disable YOLO
    

    def create_session(self, source_path: str) -> str:
        """Create a new detection session"""
        session_id = f"session_{uuid.uuid4().hex[:12]}"
        session = DetectionSession(session_id, source_path)
        
        if session.initialize():
            self.active_sessions[session_id] = session
            return session_id
        else:
            raise Exception("Failed to initialize detection session")
    

    def get_session(self, session_id: str) -> Optional[DetectionSession]:
        """Give a session ID, get the/an active session object."""
        return self.active_sessions.get(session_id)
    

    def stop_session(self, session_id: str):
        """Stop and cleanup a session"""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            session.cleanup()
            del self.active_sessions[session_id]
            print(f" Session {session_id} stopped and cleaned up")
    

    async def call_yolo_service(self, frame) -> list:
        """
        Call YOLO microservice to detect objects in frame
        
        Args:
            frame: OpenCV frame (numpy array)
            
        Returns:
            List of detections or empty list if service unavailable
        """
        print("call_yolo_service() worked!!")
        if not self.yolo_enabled:
            return []
        
        try:
            # Encode frame to base64
            _, buffer = cv2.imencode('.jpg', frame)
            frame_base64 = base64.b64encode(buffer).decode('utf-8')
            
            # Call YOLO service with timeout
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(
                    self.yolo_service_url,
                    json={"frame_base64": frame_base64}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if result.get("success"):
                        return result.get("detections", [])
                    else:
                        print(f" YOLO service error: {result.get('error')}")
                        return []
                else:
                    print(f" YOLO service returned {response.status_code}")
                    return []
                    
        except httpx.ConnectError:
            if self.yolo_enabled:
                print(" YOLO service not available (is it running on port 8001?)")
                self.yolo_enabled = False  # Disable for this session
            return []
        except httpx.TimeoutException:
            print(" YOLO service timeout")
            return []
        except Exception as e:
            print(f" YOLO service call failed: {e}")
            return []
    

    async def process_video_stream(self, session_id: str, websocket):
        """
        Processes one video stream and send lrcn + yolo results via WebSocket
        """
        session = self.get_session(session_id)
        
        if not session:
            await websocket.send_json({
                "type": "error",
                "data": {"message": "Session not found"}
            })
            return
        
        frame_count = 0
        stats = ModelStatistics()
        
        try:
            # Send start status
            await websocket.send_json({
                "type": "status",
                "data": {
                    "message": "Processing started",
                    "session_id": session_id
                }
            })
            
            while session.is_active and not session.should_stop:
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
                
                # Check if stop was requested
                if session.should_stop:
                    await websocket.send_json({
                        "type": "status",
                        "data": {
                            "message": "Processing stopped by user",
                            "total_frames": frame_count
                        }
                    })
                    print(f"⏹️ Session {session_id} stopped by user at frame {frame_count}")
                    break
                
                frame_count += 1
                
                # 1. Process frame with LRCN
                # ==========================================
                # lrcn_result = session.action_detector.process_single_frame(frame)

                # 2. Process frame with YOLO 
                # ==========================================
                yolo_detections = await self.call_yolo_service(frame)
                
                # 3. Fusion results
                # ==========================================
                # fusion_result = fusion.combine_results(yolo_detections, lrcn_result)
                # violence_score = fusion_result['threat_score']
                # threat_level = fusion_result['threat_level']

                # 4. Model stats
                # ==========================================
                # if lrcn_result.get('ready') and lrcn_result.get('is_violent'):
                #     stats.update_lrcn_stats(lrcn_result, ready=True)

                # cumulative_stats = self.get_cumulative_stats(stats, frame_count)

                # 5. Prepare WebSocket message
                ws_message = {
                    "type": "lrcn_result",
                    "data": {
                        "frame_number": frame_count,
                        "timestamp": datetime.now().isoformat(),
                        
                        # LRCN Results
                        # "lrcn": {
                        #     "action": lrcn_result['action'],
                        #     "confidence": lrcn_result['confidence'],
                        #     "ready": lrcn_result['ready'],
                        #     "is_violent": lrcn_result['is_violent'],
                        #     "all_probabilities": lrcn_result.get('all_probabilities', {})
                        # },
                        
                        # YOLO Results
                        # "yolo": {
                        #     "detections": yolo_detections,
                        #     "total_objects": len(yolo_detections)
                        # }
                    }
                }
                
                # Add buffer info if not ready
                # if not lrcn_result['ready']:
                #     ws_message['data']['buffer_progress'] = lrcn_result.get('buffer_progress', 0)
                #     ws_message['data']['buffer_size'] = lrcn_result.get('buffer_size', 0)
                
                # 6. Send via WebSocket
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
            print(f"🧹 Cleaning up session {session_id}")
            self.stop_session(session_id)


    def get_cumulative_stats(self, stats: 'ModelStatistics', current_frame: int) -> Dict:
        """Get cumulative statistics up to the current frame"""
        
        # LRCN Cumulative Statistics
        lrcn_cumulative = {
            "detections_by_action": dict(stats.lrcn_stats['detection_by_action']),
            "total_detections": len(stats.lrcn_stats['lrcn_confidences']),
            "confidence": {
                "min": stats.lrcn_stats['min_confidence'] if stats.lrcn_stats['min_confidence'] is not None else 0.0,
                "max": stats.lrcn_stats['max_confidence'] if stats.lrcn_stats['max_confidence'] is not None else 0.0,
                "avg": stats.lrcn_stats['avg_confidence']
            }
        }
        
        # YOLO Cumulative Statistics
        yolo_cumulative = {
            "detections_by_object": dict(stats.yolo_stats['detection_by_object']),
            "total_detections": len(stats.yolo_stats['yolo_confidences']),
            "confidence": {
                "min": stats.yolo_stats['min_confidence'] if stats.yolo_stats['min_confidence'] is not None else 0.0,
                "max": stats.yolo_stats['max_confidence'] if stats.yolo_stats['max_confidence'] is not None else 0.0,
                "avg": stats.yolo_stats['avg_confidence']
            }
        }
        
        return {
            "lrcn": lrcn_cumulative,
            "yolo": yolo_cumulative,
            "frames_processed": current_frame
        }


# Global service instance
detection_service = SessionService()
