"""
YOLOv8 inference for seatbelt / phone using your trained weights (best.pt).
- We only compute two outputs: phone_conf (max) and seatbelt_present (bool).
"""
import numpy as np
from ultralytics import YOLO
from app.core.config import settings

class SeatbeltPhoneDetector:
    def __init__(self):
        # Load once per worker
        self.model = YOLO(settings.YOLO_MODEL)

        # Resolve class names
        names = getattr(self.model, "names", None) or getattr(self.model.model, "names", {})
        self.names = {int(i): str(n).lower() for i, n in names.items()}

        # Common aliases (adjust if your dataset uses different terms)
        seatbelt_aliases = {"seatbelt", "seat_belt", "belt"}
        phone_aliases = {"phone", "cell_phone", "mobile_phone", "smartphone"}
        drowsiness_aliases = {"drowsiness", "drowsy"}
        yawning_aliases = {"yawning", "yawn"}
        headpose_aliases = {"headpose", "head_pose"}

        # Find IDs for seatbelt & phone
        self.seatbelt_ids = {i for i, n in self.names.items() if n in seatbelt_aliases}
        self.phone_ids    = {i for i, n in self.names.items() if n in phone_aliases}
        self.drowsiness_ids = {i for i, n in self.names.items() if n in drowsiness_aliases}
        self.yawning_ids = {i for i, n in self.names.items() if n in yawning_aliases}   
        self.headpose_ids = {i for i, n in self.names.items() if n in headpose_aliases}

        # Fallback in case names are missing
        if not self.seatbelt_ids and not self.phone_ids and not self.drowsiness_ids and not self.yawning_ids and not self.headpose_ids:
            self.seatbelt_ids = {6}
            self.phone_ids = {5}
            self.drowsiness_ids = {0}
            self.yawning_ids = {4}
            self.headpose_ids = {2}

    def run(self, bgr: np.ndarray) -> dict:
        """
        Returns:
          {
            "phone_conf": float,            # 0..1 (max conf of phone in frame)
            "seatbelt_present": bool        # True if any seatbelt detected
          }
        """
        # YOLO expects RGB
        rgb = bgr[:, :, ::-1]

        # imgsz 480 is fine for ROI  (adjust if your ROI is smaller/bigger)
        results = self.model.predict(source=rgb, imgsz=480, conf=0.5, verbose=False)

        phone_conf = 0.0
        seatbelt_present = False
        drowsiness_present = False
        yawning_present = False 
        headpose_present = False

        if not results:
            return {"phone_conf": phone_conf, "seatbelt_present": seatbelt_present}

        for r in results:
            if r.boxes is None:
                continue
            for b in r.boxes:
                cls_id = int(b.cls.item())
                conf = float(b.conf.item())
                if cls_id in self.phone_ids:
                    phone_conf = max(phone_conf, conf)
                if cls_id in self.seatbelt_ids:
                    seatbelt_present = True
                # if cls_id in self.drowsiness_ids:
                #     drowsiness_present = True
                # if cls_id in self.yawning_ids:
                #     yawning_present = True
                # if cls_id in self.headpose_ids:
                #     headpose_present = True

        return {"phone_conf": phone_conf, "seatbelt_present": seatbelt_present, "drowsiness_present": drowsiness_present, "yawning_present": yawning_present, "headpose_present": headpose_present}