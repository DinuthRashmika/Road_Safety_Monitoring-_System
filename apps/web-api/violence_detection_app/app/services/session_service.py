import asyncio
from datetime import datetime
from typing import Dict, Optional
import uuid
from violence_detection_app.app.services.detection_session import DetectionSession
from violence_detection_app.src.model_fusion.model_stats import ModelStatistics

class SessionService:
    """Manages many DetectionSession objects (many sessions)"""
    
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
    

    # REAL SERVICE --->
    # CONNECTS ALL LRCN + YOLO + FUSION(half impl) + STATS(half impl)
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

        # Initialize weight calculater

        # Initialize stats 
        # from violence_detection_app.src.model_fusion.model_stats import ModelStatistics
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
                
                # 1. Process frame with LRCN
                # ==========================================
                lrcn_result = session.action_detector.process_single_frame(frame)

                # 2. Process each frame with YOLO
                # ==========================================
                # yolo_result = session.object_detector.detect_in_frame(frame)
                
                # 3. fusion results
                # ==========================================
                # fusion_result = fusion.combine_results(yolo_result, lrcn_result)
                # violence_score = fusion_result['threat_score']  # 0-1 scale
                # threat_level = fusion_result['threat_level'] 


                # 4. Model stats
                # ==========================================
                if lrcn_result.get('ready') and lrcn_result.get('is_violent'):
                    stats.update_lrcn_stats(lrcn_result, ready=True)

                # if yolo_result.get('detections'):
                #     stats.update_yolo_stats(yolo_result)

                # if combining weights also, get combine_weigghts()


                cumulative_stats = self.get_cumulative_stats(stats, frame_count)

                # 5. Prepare WebSocket message
                ws_message = {
                    "type": "lrcn_result",
                    "data": {
                        "frame_number": frame_count,
                        "timestamp": datetime.now().isoformat(),
                        
                        # LRCN Results
                        "lrcn": {
                            "action": lrcn_result['action'],
                            "confidence": lrcn_result['confidence'],
                            "ready": lrcn_result['ready'],
                            "is_violent": lrcn_result['is_violent'],
                            "all_probabilities": lrcn_result.get('all_probabilities', {})
                        },
                        
                        # YOLO Results
                        # "yolo": {
                        #     "detections": yolo_result.get('detections', []),
                        #     "total_objects": len(yolo_result.get('detections', []))
                        # },
                        
                        # Violence Assessment
                        # "violence_assessment": {
                        #     "score": round(violence_score * 100, 2),  # 0-100 scale
                        #     "level": threat_level,
                        #     "is_violent": violence_score >= 0.6  # High/Critical threshold
                        # },
                        
                        # Cumulative Statistics (up to this frame)
                        # "cumulative_statistics": cumulative_stats
                    }
                }
                
                # Add buffer info if not ready
                if not lrcn_result['ready']:
                    ws_message['data']['buffer_progress'] = lrcn_result.get('buffer_progress', 0)
                    ws_message['data']['buffer_size'] = lrcn_result.get('buffer_size', 0)
                
                # 5. Send via WebSocket
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


    def get_cumulative_stats(self, stats: 'ModelStatistics', current_frame: int) -> Dict:
        """
        Get cumulative statistics up to the current frame
        
        Returns 
        What has been detected SO FAR (not just this frame)
        Running min/max/avg confidences
        Action/object counts accumulated over all frames

        """
        
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
        
        # Combined Violence Score Statistics
        violence_cumulative = {
            "frames_processed": current_frame,
            "scores": {
                "min": min(stats.combined_stats['weighted_scores']) if stats.combined_stats['weighted_scores'] else 0.0,
                "max": max(stats.combined_stats['weighted_scores']) if stats.combined_stats['weighted_scores'] else 0.0,
                "avg": sum(stats.combined_stats['weighted_scores']) / len(stats.combined_stats['weighted_scores']) if stats.combined_stats['weighted_scores'] else 0.0
            },
        }
        
        # Overall Assessment (so far)
        # overall_risk = self._calculate_overall_risk(stats, current_frame)
        
        return {
            "lrcn": lrcn_cumulative,
            "yolo": yolo_cumulative,
            "violence_assessment": violence_cumulative,
            # "overall_risk_level": overall_risk
        }
    

    def _calculate_overall_risk(self, stats: ModelStatistics, current_frame: int) -> str:
        """
        Calculate overall risk level based on cumulative statistics
        """
        if current_frame == 0:
            return "unknown"
        
        # For now, base it on violent action detection rate
        # (since we don't have violence scores yet)
        violent_detections = sum(
            count for action, count in stats.lrcn_stats['detection_by_action'].items()
            if action in ['shooting', 'fighting', 'attacking']  # violent actions
        )
        
        total_detections = len(stats.lrcn_stats['lrcn_confidences'])
        
        if total_detections == 0:
            return "unknown"
        
        violence_rate = (violent_detections / total_detections) * 100
        
        # Categorize based on violence rate
        if violence_rate > 50:
            return "high"
        elif violence_rate > 25:
            return "medium"
        else:
            return "low"
    


# Global service instance
detection_service = SessionService()