"""
session_tracker.py
──────────────────
Tracks live detection data during a session.
Call update_action() and update_object() every frame.
Call finalize() when session ends to get the summary document.
"""

import time
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from violence_detection_app.app.models.session_model import (
    DetectedAction, DetectedObject, ConfidenceDistribution,
    CameraInfo, SessionSummaryDocument
)


@dataclass
class _ActionTracker:
    action: str
    is_violent: bool
    first_seen_ts: str
    last_seen_ts: str
    first_seen_time: float       # monotonic
    last_seen_time: float        # monotonic
    frame_count: int   = 0
    conf_sum: float    = 0.0
    max_conf: float    = 0.0


@dataclass
class _ObjectTracker:
    object_name: str
    first_seen_ts: str
    last_seen_ts: str
    first_seen_time: float
    last_seen_time: float
    frame_count: int   = 0
    conf_sum: float    = 0.0
    max_conf: float    = 0.0


class SessionTracker:
    """
    One instance per active detection session.
    Tracks actions, objects, alerts, and timing.
    """

    def __init__(self, session_id: str, camera_info: CameraInfo):
        self.session_id   = session_id
        self.camera_info  = camera_info
        self.started_at   = datetime.now().isoformat()
        self._start_time  = time.monotonic()

        self._actions: Dict[str, _ActionTracker] = {}
        self._objects: Dict[str, _ObjectTracker] = {}
        self._alert_ids:    List[str] = []
        self._alert_levels: List[str] = []

    # ─────────────────────────────────────────
    #  Called every frame from session_service
    # ─────────────────────────────────────────
    def update_action(self, action: str, confidence: float, is_violent: bool):
        """Call this every frame when LRCN is ready."""
        now_ts   = datetime.now().isoformat()
        now_mono = time.monotonic()

        if action not in self._actions:
            self._actions[action] = _ActionTracker(
                action         = action,
                is_violent     = is_violent,
                first_seen_ts  = now_ts,
                last_seen_ts   = now_ts,
                first_seen_time = now_mono,
                last_seen_time  = now_mono,
            )

        t = self._actions[action]
        t.last_seen_ts   = now_ts
        t.last_seen_time = now_mono
        t.frame_count   += 1
        t.conf_sum       += confidence
        t.max_conf       = max(t.max_conf, confidence)

    def update_objects(self, detections: list):
        """Call this every frame with YOLO detections list."""
        now_ts   = datetime.now().isoformat()
        now_mono = time.monotonic()

        for det in detections:
            name = det.get("object", "unknown").lower()
            conf = det.get("confidence", 0.0)

            if name not in self._objects:
                self._objects[name] = _ObjectTracker(
                    object_name     = name,
                    first_seen_ts   = now_ts,
                    last_seen_ts    = now_ts,
                    first_seen_time = now_mono,
                    last_seen_time  = now_mono,
                )

            o = self._objects[name]
            o.last_seen_ts   = now_ts
            o.last_seen_time = now_mono
            o.frame_count   += 1
            o.conf_sum       += conf
            o.max_conf       = max(o.max_conf, conf)

    def record_alert(self, alert_id: str, threat_level: str):
        """Call this when an alert fires."""
        self._alert_ids.append(alert_id)
        self._alert_levels.append(threat_level)

    # ─────────────────────────────────────────
    #  Confidence distribution helper
    # ─────────────────────────────────────────
    def _conf_distribution(self, trackers) -> ConfidenceDistribution:
        dist = ConfidenceDistribution()
        for t in trackers:
            avg = (t.conf_sum / t.frame_count) if t.frame_count > 0 else 0.0
            if avg < 0.40:   dist.low      += 1
            elif avg < 0.70: dist.medium   += 1
            elif avg < 0.90: dist.high     += 1
            else:            dist.critical += 1
        return dist

    # ─────────────────────────────────────────
    #  Build final document
    # ─────────────────────────────────────────
    def finalize(self, end_reason: str, total_frames: int) -> SessionSummaryDocument:
        ended_at         = datetime.now().isoformat()
        duration_seconds = round(time.monotonic() - self._start_time, 2)

        # Update camera total frames
        self.camera_info.total_frames_processed = total_frames

        # Build detected actions list
        detected_actions = []
        for t in self._actions.values():
            avg_conf = round(t.conf_sum / t.frame_count, 4) if t.frame_count > 0 else 0.0
            duration = round(t.last_seen_time - t.first_seen_time, 2)
            detected_actions.append(DetectedAction(
                action           = t.action,
                first_seen_at    = t.first_seen_ts,
                last_seen_at     = t.last_seen_ts,
                duration_seconds = duration,
                frame_count      = t.frame_count,
                avg_confidence   = avg_conf,
                max_confidence   = round(t.max_conf, 4),
                is_violent       = t.is_violent,
            ))

        # Build detected objects list
        detected_objects = []
        for o in self._objects.values():
            avg_conf = round(o.conf_sum / o.frame_count, 4) if o.frame_count > 0 else 0.0
            duration = round(o.last_seen_time - o.first_seen_time, 2)
            detected_objects.append(DetectedObject(
                object_name      = o.object_name,
                first_seen_at    = o.first_seen_ts,
                last_seen_at     = o.last_seen_ts,
                duration_seconds = duration,
                frame_count      = o.frame_count,
                avg_confidence   = avg_conf,
                max_confidence   = round(o.max_conf, 4),
            ))

        # Highest threat level seen
        level_rank = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1, "NONE": 0}
        highest    = max(self._alert_levels, key=lambda l: level_rank.get(l, 0)) \
                     if self._alert_levels else "NONE"

        return SessionSummaryDocument(
            session_id       = self.session_id,
            started_at       = self.started_at,
            ended_at         = ended_at,
            duration_seconds = duration_seconds,
            end_reason       = end_reason,
            camera           = self.camera_info,

            detected_actions = detected_actions,
            detected_objects = detected_objects,

            highest_threat_level = highest,
            total_alerts_fired   = len(self._alert_ids),
            alert_ids            = self._alert_ids,

            action_confidence_distribution = self._conf_distribution(
                self._actions.values()
            ),
            object_confidence_distribution = self._conf_distribution(
                self._objects.values()
            ),

            action_confidence_breakdown = {
                t.action: round(t.conf_sum / t.frame_count, 4)
                for t in self._actions.values() if t.frame_count > 0
            },
            object_confidence_breakdown = {
                o.object_name: round(o.conf_sum / o.frame_count, 4)
                for o in self._objects.values() if o.frame_count > 0
            },
        )