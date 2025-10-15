from fastapi import APIRouter, UploadFile, File, HTTPException
import numpy as np, cv2
from app.services.inference.yolo import SeatbeltPhoneDetector

router = APIRouter(prefix="/api/debug", tags=["Debug"])
detector = SeatbeltPhoneDetector()

@router.post("/yolo")
async def debug_yolo(image: UploadFile = File(...)):
    """
    POST a single image to verify your best.pt works as expected.
    Returns phone_conf and seatbelt_present.
    """
    data = await image.read()
    arr = np.frombuffer(data, np.uint8)
    bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if bgr is None:
        raise HTTPException(400, "Invalid image")
    out = detector.run(bgr)
    return out
