"""
alert_engine.py (v3 - BALANCED)
────────────────────────────────
Sustain timings matched to new fusion design:

  CRITICAL (shooting/attacking+knife): 0s  → instant
  HIGH (attacking+gun/stick, fighting+gun/knife): 0s if weapon, else 10s
  MEDIUM (attacking alone, fighting alone/+stick, running+gun/knife): 30s
  LOW: never alerts (engine filters)
  NONE: never alerts

Temporal escalation:
  MEDIUM sustained ~2.5 min → crosses into HIGH
  HIGH sustained ~3 min     → crosses into CRITICAL
  (fusion handles the math — engine just tracks time and passes it in)
"""

import time
import httpx
from datetime import datetime
from typing import Dict, Optional
from dataclasses import dataclass, field
from violence_detection_app.app.database.database import save_alert
import asyncio


@dataclass
class AlertConfig:
    hub_url: str = "http://localhost:9000/api/alerts"
    hub_api_key: str = ""
    hub_extra_headers: Dict[str, str] = field(default_factory=dict)
    send_timeout: float = 6.0

    # Sustain before first alert fires
    sustained_critical: float = 0.0    # instant
    sustained_high: float     = 0.0    # instant if weapon, 10s if no weapon
    sustained_medium: float   = 30.0   # 30s before MEDIUM alert fires
    sustained_low: float      = 999.0  # effectively never

    # Cooldowns after alert fires
    cooldown_critical: float = 15.0
    cooldown_high: float     = 25.0
    cooldown_medium: float   = 45.0
    cooldown_low: float      = 60.0

    camera_label: str   = "Main Camera"
    location_label: str = "Zone A"


@dataclass
class AlertState:
    streak_start: Optional[float]     = None
    last_fire_time: Optional[float]   = None
    last_alert_level: Optional[str]   = None
    alert_count: int                  = 0


def build_human_readable_summary(
    fusion_result: Dict,
    lrcn_result: Dict,
    yolo_result: Dict,
    config: AlertConfig,
    sustained_secs: float,
) -> str:
    now       = datetime.now()
    time_str  = now.strftime("%I:%M %p")
    hour      = now.hour

    if   0 <= hour < 6:   time_ctx = "late night — higher risk window"
    elif 6 <= hour < 9:   time_ctx = "early morning"
    elif 9 <= hour < 17:  time_ctx = "business hours"
    elif 17 <= hour < 21: time_ctx = "evening"
    else:                 time_ctx = "night"

    action       = lrcn_result.get("action", "unknown").upper()
    action_conf  = lrcn_result.get("confidence", 0.0)
    threat_level = fusion_result.get("weight_level", "UNKNOWN")
    base_level   = fusion_result.get("base_level", threat_level)
    threat_score = fusion_result.get("threat_score", 0.0)

    detections   = yolo_result.get("detections", [])
    object_names = [d.get("object", "").lower() for d in detections]
    object_confs = [d.get("confidence", 0.0) for d in detections]

    if sustained_secs < 0.5:
        duration_str = "immediately"
    elif sustained_secs < 60:
        duration_str = f"for {sustained_secs:.0f} seconds"
    else:
        duration_str = f"for {sustained_secs/60:.1f} minutes"

    # Escalation note
    escalation_note = ""
    if base_level != threat_level:
        escalation_note = f" (escalated from {base_level} after sustained activity)"

    if object_names:
        obj_str = " and ".join(f"a {o}" for o in object_names)
        s1 = (f"At {time_str} ({time_ctx}), {config.camera_label} at {config.location_label} "
              f"detected a person {action} {duration_str} with {obj_str} present{escalation_note}.")
    else:
        s1 = (f"At {time_str} ({time_ctx}), {config.camera_label} at {config.location_label} "
              f"detected a person performing {action} {duration_str}{escalation_note}.")

    conf_parts = [f"action {action_conf*100:.0f}%"]
    for name, conf in zip(object_names, object_confs):
        conf_parts.append(f"{name} {conf*100:.0f}%")
    s2 = "Confidence — " + ", ".join(conf_parts) + "."

    verdicts = {
        "CRITICAL": "IMMEDIATE RESPONSE REQUIRED — potential life-threatening situation",
        "HIGH":     "URGENT RESPONSE RECOMMENDED — active violence detected",
        "MEDIUM":   "MONITORING REQUIRED — suspicious activity detected",
        "LOW":      "AWARENESS REQUIRED — low-level concern",
    }
    s3 = f"Threat score: {threat_score*100:.0f}% ({threat_level}). {verdicts.get(threat_level, '')}"

    return f"{s1} {s2} {s3}"


class AlertEngine:

    def __init__(self, config: AlertConfig = None):
        self.config  = config or AlertConfig()
        self._states: Dict[str, AlertState] = {}

    def _get_state(self, session_id: str) -> AlertState:
        if session_id not in self._states:
            self._states[session_id] = AlertState()
        return self._states[session_id]

    def remove_session(self, session_id: str):
        self._states.pop(session_id, None)

    def get_required_sustain_time(self, threat_level: str, has_weapon: bool) -> float:
        if threat_level == "CRITICAL":
            return self.config.sustained_critical        # Always instant
        elif threat_level == "HIGH":
            return self.config.sustained_critical if has_weapon else 10.0
        elif threat_level == "MEDIUM":
            return self.config.sustained_medium          # 30s
        elif threat_level == "LOW":
            return self.config.sustained_low             # Never
        return 999.0

    def get_cooldown_time(self, threat_level: str) -> float:
        return {
            "CRITICAL": self.config.cooldown_critical,
            "HIGH":     self.config.cooldown_high,
            "MEDIUM":   self.config.cooldown_medium,
            "LOW":      self.config.cooldown_low,
        }.get(threat_level, 30.0)

    def process_frame(
        self,
        session_id: str,
        fusion_result: Optional[Dict],
        lrcn_result: Dict,
        yolo_result: Dict,
        frame_number: int,
    ) -> Optional[Dict]:
        state = self._get_state(session_id)
        now   = time.monotonic()

        # Cooldown check
        if state.last_fire_time is not None:
            cooldown = self.get_cooldown_time(state.last_alert_level or "MEDIUM")
            if (now - state.last_fire_time) < cooldown:
                state.streak_start = None
                return None

        if not fusion_result:
            state.streak_start = None
            return None

        threat_level = fusion_result.get("weight_level", "NONE")

        # Only track CRITICAL, HIGH, MEDIUM
        if threat_level not in ["CRITICAL", "HIGH", "MEDIUM"]:
            state.streak_start = None
            return None

        has_weapon       = len(yolo_result.get("detections", [])) > 0
        required_sustain = self.get_required_sustain_time(threat_level, has_weapon)

        # Maintain streak
        if state.streak_start is None:
            state.streak_start = now
            streak_secs = 0.0
        else:
            streak_secs = now - state.streak_start

        # Not sustained long enough yet
        if streak_secs < required_sustain:
            return None

        # FIRE
        state.streak_start    = None
        state.last_fire_time  = now
        state.last_alert_level = threat_level
        state.alert_count     += 1
        fired_at               = datetime.now()

        human_summary = build_human_readable_summary(
            fusion_result, lrcn_result, yolo_result, self.config, streak_secs
        )

        payload = {
            "alert_id":            f"{session_id}_alert_{state.alert_count}",
            "session_id":          session_id,
            "timestamp":           fired_at.isoformat(),
            "camera":              self.config.camera_label,
            "location":            self.config.location_label,
            "threat_level":        threat_level,
            "base_level":          fusion_result.get("base_level", threat_level),
            "threat_score":        fusion_result.get("threat_score", 0.0),
            "sustained_seconds":   round(streak_secs, 2),
            "action":              lrcn_result.get("action", "unknown"),
            "action_confidence":   lrcn_result.get("confidence", 0.0),
            "objects_detected":    [
                {"object": d.get("object"), "confidence": d.get("confidence")}
                for d in yolo_result.get("detections", [])
            ],
            "action_contribution": fusion_result.get("action_contribution", 0.0),
            "object_contribution": fusion_result.get("object_contribution", 0.0),
            "synergy_bonus":       fusion_result.get("synergy_bonus", 0.0),
            "temporal_bonus":      fusion_result.get("temporal_bonus", 0.0),
            "reasoning":           fusion_result.get("reasoning", ""),
            "human_summary":       human_summary,
            "frame_number":        frame_number,
            "alert_number":        state.alert_count,
            "has_weapon":          has_weapon,
            "required_sustain_s":  required_sustain,
        }

        hub_payload = {
            "alert_id":            payload["alert_id"],
            "session_id":          payload["session_id"],
            "timestamp":           payload["timestamp"],
            "camera":              payload["camera"],
            "location":            payload["location"],
            "threat_level":        payload["threat_level"],
            "threat_score":        payload["threat_score"],
            "sustained_seconds":   payload["sustained_seconds"],
            "action":              payload["action"],
            "action_confidence":   payload["action_confidence"],
            "objects_detected":    payload["objects_detected"],
            "action_contribution": payload["action_contribution"],
            "object_contribution": payload["object_contribution"],
            "reasoning":           payload["reasoning"],
            "human_summary":       payload["human_summary"],
            "alert_number":        payload["alert_number"],
            "has_weapon":          payload["has_weapon"],
        }

        # ── Save to MongoDB (fire-and-forget, won't block detection loop) ──
        print("Saved to mongodb")
        try:
            asyncio.ensure_future(save_alert(payload))
        except Exception as e:
            print(f"[DB] Could not schedule save: {e}")

        return payload, hub_payload

    def process_frame_with_temporal(
        self,
        session_id: str,
        fusion_module,           # ModelFusion instance
        lrcn_result: Dict,
        yolo_result: Dict,
        frame_number: int,
    ) -> Optional[Dict]:
        """
        Enhanced version: passes current streak_secs into fusion
        so temporal escalation is calculated with live sustain time.
        Use this instead of process_frame when using v3 fusion.
        """
        state = self._get_state(session_id)
        now   = time.monotonic()

        # Cooldown check
        if state.last_fire_time is not None:
            cooldown = self.get_cooldown_time(state.last_alert_level or "MEDIUM")
            if (now - state.last_fire_time) < cooldown:
                state.streak_start = None
                return None

        # Calculate current streak before fusion
        if state.streak_start is not None:
            current_streak = now - state.streak_start
        else:
            current_streak = 0.0

        # Run fusion WITH current sustained time
        fusion_result = fusion_module.combine_results(
            yolo_result, lrcn_result,
            sustained_seconds=current_streak    # temporal escalation input
        )

        return self.process_frame(
            session_id, fusion_result, lrcn_result, yolo_result, frame_number
        )

    async def send_to_hub(self, payload: Dict) -> Dict:
        headers = {"Content-Type": "application/json"}
        if self.config.hub_api_key:
            headers["Authorization"] = self.config.hub_api_key
        headers.update(self.config.hub_extra_headers)

        try:
            async with httpx.AsyncClient(timeout=self.config.send_timeout) as client:
                response = await client.post(self.config.hub_url, json=payload, headers=headers)
                if response.status_code in (200, 201, 202):
                    return {"success": True,  "status_code": response.status_code, "error": None}
                return {"success": False, "status_code": response.status_code,
                        "error": f"Hub returned HTTP {response.status_code}"}
        except httpx.ConnectError:
            return {"success": False, "status_code": None, "error": "Coordination hub unreachable"}
        except httpx.TimeoutException:
            return {"success": False, "status_code": None, "error": f"Timed out after {self.config.send_timeout}s"}
        except Exception as e:
            return {"success": False, "status_code": None, "error": str(e)}

    def get_progress(self, session_id: str) -> Dict:
        state = self._get_state(session_id)
        now   = time.monotonic()

        if state.last_fire_time is not None:
            cooldown    = self.get_cooldown_time(state.last_alert_level or "MEDIUM")
            cd_elapsed  = now - state.last_fire_time
            cd_remaining = max(cooldown - cd_elapsed, 0.0)
            if cd_remaining > 0:
                return {
                    "is_cooling":         True,
                    "cooldown_remaining": round(cd_remaining, 1),
                    "cooldown_total":     cooldown,
                    "cooldown_pct":       round((cd_remaining / cooldown) * 100),
                    "streak_secs":        0.0,
                    "required_secs":      0.0,
                    "progress_pct":       0,
                    "alert_count":        state.alert_count,
                }

        streak_secs  = (now - state.streak_start) if state.streak_start else 0.0
        progress_pct = min(round((streak_secs / 30.0) * 100), 100)

        return {
            "is_cooling":         False,
            "cooldown_remaining": 0.0,
            "cooldown_total":     0.0,
            "cooldown_pct":       0,
            "streak_secs":        round(streak_secs, 1),
            "required_secs":      30.0,
            "progress_pct":       progress_pct,
            "alert_count":        state.alert_count,
        }


alert_engine = AlertEngine(AlertConfig(
    # hub_url = "https://httpbin.org/post",   # echoes your POST back
    hub_url = "http://localhost:9000/api/alerts" # if using mock_hub

    # hub_url     = "http://localhost:8000/api/alerts/path", real kavi one
    # hub_api_key = "if_he_requires_one",
))