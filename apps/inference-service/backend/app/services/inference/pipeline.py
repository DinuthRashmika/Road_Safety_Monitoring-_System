"""
Minimal DMS pipeline for this stage:
- Only detects "phone use" and "seatbelt OFF".
- Uses TemporalDebouncer to confirm sustained events (avoid flicker).
"""
import time
import numpy as np
from .yolo import SeatbeltPhoneDetector
from ..temporal import TemporalDebouncer

class DmsPipeline:
    def __init__(self):
        self.det = SeatbeltPhoneDetector()
        # Debounce windows — tweak to taste after testing on your clips.
        self.debouncers = {
            "phone":    TemporalDebouncer(min_secs=1.0, cooldown=2.0),
            "seatbelt": TemporalDebouncer(min_secs=1.0, cooldown=2.0),
            "drowness": TemporalDebouncer(min_secs=1.0, cooldown=2.0),
            "yawning": TemporalDebouncer(min_secs=1.0, cooldown=2.0),
            "headpose": TemporalDebouncer(min_secs=1.0, cooldown=2.0),

        }

    def process(self, bgr: np.ndarray) -> list[dict]:
        """
        Input: BGR image (ROI)
        Output: confirmed events [{"type":"phone","confidence":0.8}, {"type":"seatbelt","confidence":0.9}]
        """
        now = time.time()
        out: list[dict] = []

        y = self.det.run(bgr)
        phone_active = (y.get("phone_conf", 0.0) > 0.1)
        seatbelt_off = (y.get("seatbelt_present", False) is False)
        drowsiness = (y.get("drowsiness_present", False) is True)
        yawning = (y.get("yawning_present", False) is True)
        headpose = (y.get("headpose_present", False) is True)
        
        if self.debouncers["phone"].update(phone_active, now):
            out.append({"type": "phone", "confidence": float(y.get("phone_conf", 0.0))})

        if self.debouncers["seatbelt"].update(seatbelt_off, now):
            out.append({"type": "seatbelt", "confidence": 0.9})
        if self.debouncers["drowness"].update(drowsiness, now):
            out.append({"type": "drowness", "confidence": float(y.get("drowsiness_conf", 0.0))})
        if self.debouncers["yawning"].update(yawning, now):
            out.append({"type": "yawning", "confidence": float(y.get("yawning_conf", 0.0))})
        if self.debouncers["headpose"].update(headpose, now):
            out.append({"type": "headpose", "confidence": float(y.get("headpose_conf", 0.0))})
        return out
