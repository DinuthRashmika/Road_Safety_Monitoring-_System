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
        }

    def process(self, bgr: np.ndarray) -> list[dict]:
        """
        Input: BGR image (ROI)
        Output: confirmed events [{"type":"phone","confidence":0.8}, {"type":"seatbelt","confidence":0.9}]
        """
        now = time.time()
        out: list[dict] = []

        y = self.det.run(bgr)
        phone_active = (y.get("phone_conf", 0.0) > 0.6)
        seatbelt_off = (y.get("seatbelt_present", False) is False)

        if self.debouncers["phone"].update(phone_active, now):
            out.append({"type": "phone", "confidence": float(y.get("phone_conf", 0.0))})

        if self.debouncers["seatbelt"].update(seatbelt_off, now):
            out.append({"type": "seatbelt", "confidence": 0.9})

        return out
