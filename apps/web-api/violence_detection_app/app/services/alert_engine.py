"""
alert_engine.py
───────────────
Watches the rolling fusion results for a session and fires an alert
when the threat has been sustained above the threshold long enough.

Alert logic
  • Arm:   threat level is HIGH or CRITICAL for >= sustained_seconds wall-clock seconds
  • Fire:  sends the full alert payload to your REST coordination hub via HTTP POST
  • Cool:  after firing, ignores the same session for cooldown_seconds
           (prevents spam if the scene stays violent)

Quick-start configuration
─────────────────────────
Edit AlertConfig below:

    hub_url              = "https://your-hub.example.com/api/alerts"
    hub_api_key          = "Bearer YOUR_TOKEN"   # or "" to skip auth header
    sustained_seconds    = 3.0   # seconds of HIGH/CRITICAL before firing
    cooldown_seconds     = 30.0  # seconds before the same session can fire again
    camera_label         = "Camera 01"
    location_label       = "Entrance — Zone A"
"""

import time
import httpx
from datetime import datetime
from typing import Dict, Optional
from dataclasses import dataclass, field


# ─────────────────────────────────────────────
#  ★  CONFIGURATION — edit this block  ★
# ─────────────────────────────────────────────
@dataclass
class AlertConfig:

    # ── REST endpoint ──────────────────────────────────────────────────────
    # Full URL of your coordination hub's alert endpoint.
    hub_url: str = "http://localhost:9000/api/alerts"

    # Authorization header value sent with every request.
    # Examples:
    #   "Bearer eyJhbGci..."   →  Authorization: Bearer <token>
    #   "ApiKey abc123"        →  Authorization: ApiKey abc123
    #   ""                     →  no Authorization header (skip auth)
    hub_api_key: str = ""

    # Any extra HTTP headers your hub needs (e.g. {"X-Source": "cctv-01"})
    hub_extra_headers: Dict[str, str] = field(default_factory=dict)

    # HTTP timeout in seconds when posting to hub
    send_timeout: float = 6.0

    # ── Trigger thresholds ─────────────────────────────────────────────────
    # Seconds of *continuous* high threat before an alert fires.
    # The timer resets to zero any time threat drops below trigger_levels.
    sustained_seconds: float = 3.0

    # Threat levels that count toward the sustained timer.
    # HIGH and CRITICAL (per your requirement).
    trigger_levels: tuple = ("HIGH", "CRITICAL")

    # Seconds to wait after an alert fires before re-arming for the same session.
    cooldown_seconds: float = 30.0

    # ── Scene metadata ────────────────────────────────────────────────────
    camera_label: str = "Main Camera"
    location_label: str = "Zone A"


# ─────────────────────────────────────────────
#  Per-session runtime state (internal)
# ─────────────────────────────────────────────
@dataclass
class AlertState:
    # Wall-clock timestamp (time.monotonic) when the current HIGH/CRITICAL
    # streak started. None = not currently in a threatening streak.
    streak_start: Optional[float] = None

    # Wall-clock timestamp when the last alert was sent (for cooldown check).
    last_fire_time: Optional[float] = None

    # How many alerts this session has fired total.
    alert_count: int = 0


# ─────────────────────────────────────────────
#  Human-readable summary
# ─────────────────────────────────────────────
def build_human_readable_summary(
    fusion_result: Dict,
    lrcn_result: Dict,
    yolo_result: Dict,
    config: AlertConfig,
    sustained_secs: float,
) -> str:
    """
    Builds a natural language description for the alert, e.g.:

    "At 03:30 AM (late night — higher risk window), Main Camera at Zone A detected
     a person RUNNING for 4.2 seconds with a knife present.
     Confidence — action 86%, knife 74%.
     Threat score: 91% (CRITICAL). Immediate response required."
    """
    now      = datetime.now()
    time_str = now.strftime("%I:%M %p")
    hour     = now.hour

    if   0 <= hour < 6:   time_ctx = "late night — higher risk window"
    elif 6 <= hour < 9:   time_ctx = "early morning"
    elif 9 <= hour < 17:  time_ctx = "business hours"
    elif 17 <= hour < 21: time_ctx = "evening"
    else:                 time_ctx = "night"

    action       = lrcn_result.get("action", "unknown action").upper()
    action_conf  = lrcn_result.get("confidence", 0.0)
    threat_level = fusion_result.get("weight_level", "UNKNOWN")
    threat_score = fusion_result.get("threat_score", 0.0)

    detections   = yolo_result.get("detections", [])
    object_names = [d.get("object", "object").lower() for d in detections]
    object_confs = [d.get("confidence", 0.0) for d in detections]

    duration_str = f"for {sustained_secs:.1f} seconds" if sustained_secs >= 1 else "continuously"

    # S1 — what / where / how long
    if object_names:
        obj_str = " and ".join(f"a {o}" for o in object_names)
        s1 = (
            f"At {time_str} ({time_ctx}), {config.camera_label} at "
            f"{config.location_label} detected a person {action} {duration_str} "
            f"with {obj_str} present."
        )
    else:
        s1 = (
            f"At {time_str} ({time_ctx}), {config.camera_label} at "
            f"{config.location_label} detected a person performing a {action} "
            f"action {duration_str}."
        )

    # S2 — confidence breakdown
    conf_parts = [f"action {action_conf*100:.0f}%"]
    for name, conf in zip(object_names, object_confs):
        conf_parts.append(f"{name} {conf*100:.0f}%")
    s2 = "Confidence — " + ", ".join(conf_parts) + "."

    # S3 — verdict
    if threat_level == "CRITICAL":
        rec = "Immediate response required."
    else:  # HIGH
        rec = "Urgent response recommended."

    s3 = f"Threat score: {threat_score*100:.0f}% ({threat_level}). {rec}"

    return f"{s1} {s2} {s3}"


# ─────────────────────────────────────────────
#  Alert Engine
# ─────────────────────────────────────────────
class AlertEngine:
    """
    One shared instance across all sessions.
    Call process_frame() every frame from session_service.process_video_stream().
    """

    def __init__(self, config: AlertConfig = None):
        self.config = config or AlertConfig()
        self._states: Dict[str, AlertState] = {}

    # ── Lifecycle ────────────────────────────
    def _get_state(self, session_id: str) -> AlertState:
        if session_id not in self._states:
            self._states[session_id] = AlertState()
        return self._states[session_id]

    def remove_session(self, session_id: str):
        """Call when a session is stopped to free memory."""
        self._states.pop(session_id, None)

    # ── Core frame processing ────────────────
    def process_frame(
        self,
        session_id: str,
        fusion_result: Optional[Dict],
        lrcn_result: Dict,
        yolo_result: Dict,
        frame_number: int,
    ) -> Optional[Dict]:
        """
        Call every frame (even while LRCN buffer is filling).

        Returns:
            alert payload dict  — only on the frame that triggers the alert
            None                — all other frames
        """
        state = self._get_state(session_id)
        now   = time.monotonic()

        # ── Cooldown: skip until enough time since last fire ──────────────
        if state.last_fire_time is not None:
            if (now - state.last_fire_time) < self.config.cooldown_seconds:
                state.streak_start = None
                return None

        # ── No fusion result yet (LRCN buffer filling) ────────────────────
        if not fusion_result:
            state.streak_start = None
            return None

        threat_level = fusion_result.get("weight_level", "NONE")

        # ── Maintain the HIGH/CRITICAL time streak ────────────────────────
        if threat_level in self.config.trigger_levels:
            if state.streak_start is None:
                state.streak_start = now          # streak just started
            streak_secs = now - state.streak_start
        else:
            state.streak_start = None             # streak broken — reset
            return None

        # ── Not sustained long enough yet ─────────────────────────────────
        if streak_secs < self.config.sustained_seconds:
            return None

        # ── FIRE ──────────────────────────────────────────────────────────
        state.streak_start   = None               # reset after firing
        state.last_fire_time = now
        state.alert_count   += 1
        fired_at = datetime.now()

        human_summary = build_human_readable_summary(
            fusion_result, lrcn_result, yolo_result,
            self.config, streak_secs
        )

        payload = {
            "alert_id":          f"{session_id}_alert_{state.alert_count}",
            "session_id":        session_id,
            "timestamp":         fired_at.isoformat(),
            "camera":            self.config.camera_label,
            "location":          self.config.location_label,
            "threat_level":      threat_level,
            "threat_score":      fusion_result.get("threat_score", 0.0),
            "sustained_seconds": round(streak_secs, 2),
            "action":            lrcn_result.get("action", "unknown"),
            "action_confidence": lrcn_result.get("confidence", 0.0),
            "objects_detected": [
                {"object": d.get("object"), "confidence": d.get("confidence")}
                for d in yolo_result.get("detections", [])
            ],
            "lrcn_contribution": fusion_result.get("lrcn_contribution", 0.0),
            "yolo_contribution": fusion_result.get("yolo_contribution", 0.0),
            "synergy_bonus":     fusion_result.get("synergy_bonus", 0.0),
            "human_summary":     human_summary,
            "frame_number":      frame_number,
            "alert_number":      state.alert_count,
        }

        return payload

    # ── Send to REST hub ──────────────────────
    async def send_to_hub(self, payload: Dict) -> Dict:
        """
        POST the alert payload to the coordination hub.

        Returns:
            { "success": bool, "status_code": int|None, "error": str|None }
        """
        headers = {"Content-Type": "application/json"}

        if self.config.hub_api_key:
            headers["Authorization"] = self.config.hub_api_key

        headers.update(self.config.hub_extra_headers)

        try:
            async with httpx.AsyncClient(timeout=self.config.send_timeout) as client:
                response = await client.post(
                    self.config.hub_url,
                    json=payload,
                    headers=headers,
                )
                if response.status_code in (200, 201, 202):
                    return {"success": True,  "status_code": response.status_code, "error": None}
                else:
                    return {
                        "success": False,
                        "status_code": response.status_code,
                        "error": f"Hub returned HTTP {response.status_code}",
                    }

        except httpx.ConnectError:
            return {"success": False, "status_code": None,
                    "error": "Coordination hub unreachable — check hub_url in AlertConfig"}
        except httpx.TimeoutException:
            return {"success": False, "status_code": None,
                    "error": f"Request timed out after {self.config.send_timeout}s"}
        except Exception as e:
            return {"success": False, "status_code": None, "error": str(e)}

    # ── Progress for frontend ─────────────────
    def get_progress(self, session_id: str) -> Dict:
        """
        Returns the current arming/cooldown state for the UI arming bar.
        All time values are in seconds.
        """
        state    = self._get_state(session_id)
        now      = time.monotonic()
        required = self.config.sustained_seconds
        cooldown = self.config.cooldown_seconds

        # In cooldown?
        if state.last_fire_time is not None:
            cd_elapsed   = now - state.last_fire_time
            cd_remaining = max(cooldown - cd_elapsed, 0.0)
            if cd_remaining > 0:
                return {
                    "is_cooling":         True,
                    "cooldown_remaining": round(cd_remaining, 1),
                    "cooldown_total":     cooldown,
                    "cooldown_pct":       round((cd_remaining / cooldown) * 100),
                    "streak_secs":        0.0,
                    "required_secs":      required,
                    "progress_pct":       0,
                    "alert_count":        state.alert_count,
                }

        # Building a streak?
        if state.streak_start is not None:
            streak_secs  = now - state.streak_start
            progress_pct = min(round((streak_secs / required) * 100), 100)
        else:
            streak_secs  = 0.0
            progress_pct = 0

        return {
            "is_cooling":         False,
            "cooldown_remaining": 0.0,
            "cooldown_total":     cooldown,
            "cooldown_pct":       0,
            "streak_secs":        round(streak_secs, 1),
            "required_secs":      required,
            "progress_pct":       progress_pct,
            "alert_count":        state.alert_count,
        }


# ─────────────────────────────────────────────
#  Global instance — imported by session_service
# ─────────────────────────────────────────────
alert_engine = AlertEngine(AlertConfig())