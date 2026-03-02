import asyncio
from datetime import datetime
from typing import Dict, Optional
import uuid
import cv2
import base64
import threading
from queue import Queue, Empty
from collections import deque

from violence_detection_app.app.services.detection_session import DetectionSession
from violence_detection_app.src.fusion.model_stats import ModelStatistics
from violence_detection_app.src.fusion.model_fusion import ModelFusion


class SessionService:
    """
    PRODUCTION-READY: Manages detection sessions with proper async/threading
    """

    def __init__(self):
        self.active_sessions: Dict[str, DetectionSession] = {}
        self.fusion = ModelFusion()

        # Frame encoding settings
        self.jpeg_quality = 65
        self.frame_resize_width = 640
        
        # Real-time optimization settings
        self.yolo_frame_skip = 5  # Run YOLO every 5th frame
        self.max_frame_queue_size = 2  # Keep only 2 latest frames


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
        return self.active_sessions.get(session_id)


    def stop_session(self, session_id: str):
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            session.cleanup()
            del self.active_sessions[session_id]
            print(f"Session {session_id} stopped and cleaned up")


    def encode_frame_fast(self, frame) -> Optional[str]:
        """
        OPTIMIZED: Fast frame encoding with minimal blocking
        
        Args:
            frame: numpy array (BGR, from cv2)
            
        Returns:
            base64-encoded JPEG string, or None on failure
        """
        try:
            # Resize if needed (uses INTER_AREA for downscaling - fastest)
            if self.frame_resize_width is not None:
                h, w = frame.shape[:2]
                if w > self.frame_resize_width:
                    scale = self.frame_resize_width / w
                    new_size = (self.frame_resize_width, int(h * scale))
                    frame = cv2.resize(frame, new_size, interpolation=cv2.INTER_AREA)

            # Fast JPEG encoding
            encode_params = [
                cv2.IMWRITE_JPEG_QUALITY, self.jpeg_quality,
                cv2.IMWRITE_JPEG_OPTIMIZE, 0  # Disable optimization for speed
            ]
            success, buffer = cv2.imencode('.jpg', frame, encode_params)

            if not success:
                return None

            return base64.b64encode(buffer).decode('utf-8')

        except Exception as e:
            print(f"Frame encoding error: {e}")
            return None


    async def process_video_stream(self, session_id: str, websocket):
        """
        PRODUCTION VERSION: Proper async processing with threading
        
        Architecture:
        Thread 1: Capture frames → frame_queue
        Thread 2: YOLO detection → yolo_results_queue  
        Main Loop: LRCN + Fusion + WebSocket send (async)
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

        # ══════════════════════════════════════════════════════
        # QUEUES & THREADING SETUP
        # ══════════════════════════════════════════════════════
        
        # Keep only latest frames (drops old ones automatically)
        frame_queue = deque(maxlen=self.max_frame_queue_size)
        
        # YOLO results queue
        yolo_results_queue = Queue(maxsize=10)
        
        # Latest YOLO result (shared across frames)
        latest_yolo_detections = []
        
        # Stop event for threads
        stop_event = threading.Event()

        # ══════════════════════════════════════════════════════
        # THREAD 1: FRAME CAPTURE
        # ══════════════════════════════════════════════════════
        def capture_frames():
            """Continuously grab frames from video"""
            while not stop_event.is_set() and session.is_active and not session.should_stop:
                ret, frame = session.video_cap.read()
                
                if not ret:
                    stop_event.set()
                    break
                
                # Add to queue (automatically drops oldest if full)
                if len(frame_queue) >= self.max_frame_queue_size:
                    frame_queue.popleft()  # Drop oldest
                frame_queue.append(frame.copy())

        # ══════════════════════════════════════════════════════
        # THREAD 2: YOLO DETECTION (Background)
        # ══════════════════════════════════════════════════════
        def yolo_worker():
            """Run YOLO detection in background"""
            local_frame_count = 0
            
            while not stop_event.is_set():
                try:
                    # Get latest frame from queue (non-blocking)
                    if len(frame_queue) == 0:
                        asyncio.sleep(0.01)
                        continue
                    
                    frame = frame_queue[-1].copy()  # Get latest frame
                    local_frame_count += 1
                    
                    # Only run YOLO every Nth frame
                    if local_frame_count % self.yolo_frame_skip == 0:
                        detections = session.object_detector.detect_in_frame(frame)
                        
                        # Put result in queue
                        try:
                            yolo_results_queue.put((local_frame_count, detections), block=False)
                        except:
                            pass  # Queue full, skip this result
                    
                    asyncio.sleep(0.001)  # Tiny sleep to prevent CPU spin
                    
                except Exception as e:
                    if not stop_event.is_set():
                        print(f"YOLO worker error: {e}")

        # ══════════════════════════════════════════════════════
        # START THREADS
        # ══════════════════════════════════════════════════════
        capture_thread = threading.Thread(target=capture_frames, daemon=True)
        yolo_thread = threading.Thread(target=yolo_worker, daemon=True)
        
        capture_thread.start()
        yolo_thread.start()

        try:
            # ══════════════════════════════════════════════════════
            # SEND START STATUS
            # ══════════════════════════════════════════════════════
            await websocket.send_json({
                "type": "status",
                "data": {
                    "message": "Processing started",
                    "session_id": session_id
                }
            })

            # ══════════════════════════════════════════════════════
            # MAIN PROCESSING LOOP (ASYNC)
            # ══════════════════════════════════════════════════════
            while session.is_active and not session.should_stop and not stop_event.is_set():
                
                # ── Check if we have frames ──
                if len(frame_queue) == 0:
                    await asyncio.sleep(0.01)
                    continue
                
                # ── Get latest frame (NON-BLOCKING) ──
                frame = frame_queue[-1].copy()
                frame_count += 1

                # ── 1. LRCN (Fast, runs every frame) ──────────────
                lrcn_result = session.action_detector.process_single_frame(frame)

                # ── 2. Get latest YOLO result (NON-BLOCKING) ──────
                try:
                    while not yolo_results_queue.empty():
                        _, detections = yolo_results_queue.get_nowait()
                        latest_yolo_detections = detections
                except Empty:
                    pass  # Use previous YOLO result

                yolo_result = {
                    "detections": latest_yolo_detections,
                    "total_objects": len(latest_yolo_detections)
                }

                # ── 3. Draw annotations (ONLY if YOLO detected something) ──
                annotated_frame = frame
                if latest_yolo_detections:
                    annotated_frame = session.object_detector.draw_detections_on_frame_test(
                        frame, latest_yolo_detections, frame_count
                    )

                # ── 4. Encode frame (Fast JPEG) ───────────────────
                frame_base64 = self.encode_frame_fast(annotated_frame)

                # ── 5. Fusion (only if LRCN ready) ────────────────
                fusion_data = None
                if lrcn_result.get('ready'):
                    try:
                        fusion_input_yolo = {"detections": latest_yolo_detections}
                        fusion_raw = self.fusion.combine_results(fusion_input_yolo, lrcn_result)

                        # Calculate contribution breakdown
                        object_score = self.fusion.calculate_yolo_threat_score(fusion_input_yolo)
                        action_score = self.fusion.calculate_lrcn_threat_score(lrcn_result)
                        yolo_contrib = object_score * self.fusion.object_detection_weight
                        lrcn_contrib = action_score * self.fusion.action_recognition_weight
                        base_score = yolo_contrib + lrcn_contrib
                        synergy_bonus = max(fusion_raw['threat_score'] - base_score, 0.0)

                        fusion_data = {
                            "threat_score": round(fusion_raw['threat_score'], 4),
                            "weight_level": fusion_raw['weight_level'],
                            "lrcn_contribution": round(lrcn_contrib, 4),
                            "yolo_contribution": round(yolo_contrib, 4),
                            "synergy_bonus": round(synergy_bonus, 4),
                        }
                    except Exception as fe:
                        print(f"Fusion error: {fe}")

                # ── 6. Build WebSocket message ────────────────────
                ws_message = {
                    "type": "lrcn_result",
                    "data": {
                        "frame_number": frame_count,
                        "timestamp": datetime.now().isoformat(),
                        "frame": frame_base64,

                        "lrcn": {
                            "action": lrcn_result['action'],
                            "confidence": lrcn_result['confidence'],
                            "ready": lrcn_result['ready'],
                            "is_violent": lrcn_result['is_violent'],
                            "all_probabilities": lrcn_result.get('all_probabilities', {})
                        },

                        "yolo": yolo_result,
                        "fusion": fusion_data,
                    }
                }

                if not lrcn_result['ready']:
                    ws_message['data']['buffer_progress'] = lrcn_result.get('buffer_progress', 0)
                    ws_message['data']['buffer_size'] = lrcn_result.get('buffer_size', 0)

                # ── 7. Send (Async, non-blocking) ─────────────────
                await websocket.send_json(ws_message)

                # ── 8. Throttle to prevent overwhelming WebSocket ──
                await asyncio.sleep(0.01)  # ~100 FPS max send rate

        except Exception as e:
            print(f"Error processing video: {e}")
            import traceback
            traceback.print_exc()
            await websocket.send_json({
                "type": "error",
                "data": {"message": str(e)}
            })

        finally:
            # ══════════════════════════════════════════════════════
            # CLEANUP
            # ══════════════════════════════════════════════════════
            stop_event.set()
            
            # Wait for threads to finish
            capture_thread.join(timeout=2)
            yolo_thread.join(timeout=2)
            
            # Send completion message
            try:
                await websocket.send_json({
                    "type": "complete",
                    "data": {
                        "message": "Video processing complete",
                        "total_frames": frame_count,
                        "statistics": session.action_detector.get_statistics()
                    }
                })
            except:
                pass
            
            print(f"Cleaning up session {session_id}")
            self.stop_session(session_id)


    def get_cumulative_stats(self, stats: 'ModelStatistics', current_frame: int) -> Dict:
        """Get cumulative statistics up to the current frame"""

        lrcn_cumulative = {
            "detections_by_action": dict(stats.lrcn_stats['detection_by_action']),
            "total_detections": len(stats.lrcn_stats['lrcn_confidences']),
            "confidence": {
                "min": stats.lrcn_stats['min_confidence'] or 0.0,
                "max": stats.lrcn_stats['max_confidence'] or 0.0,
                "avg": stats.lrcn_stats['avg_confidence']
            }
        }

        yolo_cumulative = {
            "detections_by_object": dict(stats.yolo_stats['detection_by_object']),
            "total_detections": len(stats.yolo_stats['yolo_confidences']),
            "confidence": {
                "min": stats.yolo_stats['min_confidence'] or 0.0,
                "max": stats.yolo_stats['max_confidence'] or 0.0,
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