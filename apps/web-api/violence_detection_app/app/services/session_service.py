"""
session_service.py
──────────────────
Frame-skip architecture + alert engine integration.

YOLO runs every N frames; last result is reused in between.
Alert engine is called every frame with the latest fusion data.
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional
import uuid
import cv2
import base64

from violence_detection_app.app.services.detection_session import DetectionSession
from violence_detection_app.src.fusion.model_stats import ModelStatistics
from violence_detection_app.src.fusion.model_fusion import ModelFusion
from violence_detection_app.app.services.alert_engine import alert_engine


class SessionService:
    """Manages DetectionSession objects — one per active video/camera stream."""

    def __init__(self):
        self.active_sessions: Dict[str, DetectionSession] = {}
        self.fusion = ModelFusion()

        # ── Frame encoding ────────────────────────────────────
        self.jpeg_quality       = 65
        self.frame_resize_width = 640   # None = no resize

        # ── YOLO cadence ──────────────────────────────────────
        # Run YOLO once every N frames; reuse last result otherwise.
        # 3 = recommended sweet spot for most hardware
        self.yolo_every_n_frames: int = 3

        # ── WebSocket throttle ────────────────────────────────
        self.ws_throttle_seconds: float = 0.01

    # ─────────────────────────────────────────
    #  Session lifecycle
    # ─────────────────────────────────────────
    def create_session(self, source_path: str) -> str:
        session_id = f"session_{uuid.uuid4().hex[:12]}"
        session    = DetectionSession(session_id, source_path)
        if session.initialize():
            self.active_sessions[session_id] = session
            return session_id
        raise Exception("Failed to initialize detection session")

    def get_session(self, session_id: str) -> Optional[DetectionSession]:
        return self.active_sessions.get(session_id)

    def stop_session(self, session_id: str):
        if session_id in self.active_sessions:
            self.active_sessions[session_id].cleanup()
            del self.active_sessions[session_id]
        alert_engine.remove_session(session_id)
        print(f"Session {session_id} stopped and cleaned up")

    # ─────────────────────────────────────────
    #  Frame encoding
    # ─────────────────────────────────────────
    def encode_frame(self, frame) -> Optional[str]:
        try:
            if self.frame_resize_width is not None:
                h, w = frame.shape[:2]
                if w > self.frame_resize_width:
                    scale    = self.frame_resize_width / w
                    new_size = (self.frame_resize_width, int(h * scale))
                    frame    = cv2.resize(frame, new_size, interpolation=cv2.INTER_AREA)
            ok, buf = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, self.jpeg_quality])
            return base64.b64encode(buf).decode('utf-8') if ok else None
        except Exception as e:
            print(f"Frame encoding error: {e}")
            return None

    # ─────────────────────────────────────────
    #  Main streaming loop
    # ─────────────────────────────────────────
    async def process_video_stream(self, session_id: str, websocket):
        """
        Reads every frame. LRCN every frame. YOLO every N frames.
        Alert engine called every frame.

        WebSocket message schema (type: "lrcn_result"):
        {
          frame_number, timestamp,
          frame,           # base64 JPEG
          lrcn:  { action, confidence, ready, is_violent, all_probabilities },
          yolo:  { detections, total_objects },
          fusion: { threat_score, weight_level, lrcn_contribution,
                    yolo_contribution, synergy_bonus } | null,
          alert_progress: {
              is_cooling, cooldown_remaining, cooldown_total, cooldown_pct,
              streak_secs, required_secs, progress_pct, alert_count
          },
          alert_dispatch: {          # only present when alert fires this frame
              payload: { ...full alert payload... },
              result:  { success, status_code, error }
          } | null
        }
        """
        session = self.get_session(session_id)
        if not session:
            await websocket.send_json({"type": "error", "data": {"message": "Session not found"}})
            return

        frame_count          = 0
        last_yolo_detections: List = []

        try:
            await websocket.send_json({
                "type": "status",
                "data": {"message": "Processing started", "session_id": session_id}
            })

            while session.is_active and not session.should_stop:

                ret, frame = session.video_cap.read()

                if not ret:
                    await websocket.send_json({
                        "type": "complete",
                        "data": {
                            "message":      "Video processing complete",
                            "total_frames": frame_count,
                            "statistics":   session.action_detector.get_statistics(),
                        }
                    })
                    break

                if session.should_stop:
                    await websocket.send_json({
                        "type": "status",
                        "data": {"message": "Processing stopped by user", "total_frames": frame_count}
                    })
                    break

                frame_count += 1

                # ── 1. LRCN every frame ───────────────────────────────────
                lrcn_result = session.action_detector.process_single_frame(frame)

                # ── 2. YOLO every N frames; reuse last result otherwise ────
                if frame_count % self.yolo_every_n_frames == 0:
                    last_yolo_detections = session.object_detector.detect_in_frame(frame)

                yolo_result = {
                    "detections":    last_yolo_detections,
                    "total_objects": len(last_yolo_detections),
                }

                # ── 3. Annotate frame ─────────────────────────────────────
                annotated = frame
                if last_yolo_detections:
                    annotated = session.object_detector.draw_detections_on_frame(
                        frame, last_yolo_detections, frame_count
                    )

                # ── 4. Encode frame ───────────────────────────────────────
                frame_b64 = self.encode_frame(annotated)

                # ── 5. Fusion ─────────────────────────────────────────────
                fusion_data = None
                if lrcn_result.get("ready"):
                    try:
                        raw       = self.fusion.combine_results({"detections": last_yolo_detections}, lrcn_result)
                        obj_score = self.fusion.calculate_yolo_threat_score({"detections": last_yolo_detections})
                        act_score = self.fusion.calculate_lrcn_threat_score(lrcn_result)
                        yolo_c    = obj_score * self.fusion.object_detection_weight
                        lrcn_c    = act_score * self.fusion.action_recognition_weight
                        synergy   = max(raw["threat_score"] - (yolo_c + lrcn_c), 0.0)

                        fusion_data = {
                            "threat_score":      round(raw["threat_score"], 4),
                            "weight_level":      raw["weight_level"],
                            "lrcn_contribution": round(lrcn_c, 4),
                            "yolo_contribution": round(yolo_c, 4),
                            "synergy_bonus":     round(synergy, 4),
                        }
                    except Exception as fe:
                        print(f"Fusion error frame {frame_count}: {fe}")

                # ── 6. Alert engine — every frame ─────────────────────────
                alert_payload  = alert_engine.process_frame(
                    session_id    = session_id,
                    fusion_result = fusion_data,
                    lrcn_result   = lrcn_result,
                    yolo_result   = {"detections": last_yolo_detections},
                    frame_number  = frame_count,
                )
                alert_progress = alert_engine.get_progress(session_id)

                alert_dispatch = None
                if alert_payload:
                    send_result    = await alert_engine.send_to_hub(alert_payload)
                    alert_dispatch = {"payload": alert_payload, "result": send_result}

                # ── 7. Build & send WebSocket message ─────────────────────
                msg = {
                    "type": "lrcn_result",
                    "data": {
                        "frame_number":   frame_count,
                        "timestamp":      datetime.now().isoformat(),
                        "frame":          frame_b64,
                        "lrcn": {
                            "action":            lrcn_result["action"],
                            "confidence":        lrcn_result["confidence"],
                            "ready":             lrcn_result["ready"],
                            "is_violent":        lrcn_result["is_violent"],
                            "all_probabilities": lrcn_result.get("all_probabilities", {}),
                        },
                        "yolo":           yolo_result,
                        "fusion":         fusion_data,
                        "alert_progress": alert_progress,
                        "alert_dispatch": alert_dispatch,
                    }
                }

                if not lrcn_result["ready"]:
                    msg["data"]["buffer_progress"] = lrcn_result.get("buffer_progress", 0)
                    msg["data"]["buffer_size"]     = lrcn_result.get("buffer_size", 0)

                await websocket.send_json(msg)
                await asyncio.sleep(self.ws_throttle_seconds)

        except Exception as e:
            print(f"Error processing session {session_id}: {e}")
            await websocket.send_json({"type": "error", "data": {"message": str(e)}})

        finally:
            self.stop_session(session_id)

    # ─────────────────────────────────────────
    #  Stats helper
    # ─────────────────────────────────────────
    def get_cumulative_stats(self, stats: "ModelStatistics", current_frame: int) -> Dict:
        return {
            "lrcn": {
                "detections_by_action": dict(stats.lrcn_stats["detection_by_action"]),
                "total_detections":     len(stats.lrcn_stats["lrcn_confidences"]),
                "confidence": {
                    "min": stats.lrcn_stats["min_confidence"] or 0.0,
                    "max": stats.lrcn_stats["max_confidence"] or 0.0,
                    "avg": stats.lrcn_stats["avg_confidence"],
                },
            },
            "yolo": {
                "detections_by_object": dict(stats.yolo_stats["detection_by_object"]),
                "total_detections":     len(stats.yolo_stats["yolo_confidences"]),
                "confidence": {
                    "min": stats.yolo_stats["min_confidence"] or 0.0,
                    "max": stats.yolo_stats["max_confidence"] or 0.0,
                    "avg": stats.yolo_stats["avg_confidence"],
                },
            },
            "frames_processed": current_frame,
        }


# Global service instance
detection_service = SessionService()