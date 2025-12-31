from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from jose import JWTError
from bson import ObjectId
import base64, numpy as np, cv2, time
import app.db.mongodb as mongodb
from app.core.security import decode_token
from app.services.inference.pipeline import DmsPipeline

router = APIRouter(tags=["DMS WebSocket"])
pipeline = DmsPipeline()  # load once

def b64webp_to_bgr(data_b64: str) -> np.ndarray:
    """
    Decode base64-encoded WebP bytes into a BGR numpy image.
    """
    raw = base64.b64decode(data_b64)
    arr = np.frombuffer(raw, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)  # BGR
    return img

@router.websocket("/ws/sessions/{session_id}")
async def ws_session(websocket: WebSocket, session_id: str, token: str):
    """
    WebSocket pipeline:
      - Client connects: ws://host/ws/sessions/{session_id}?token=JWT
      - Sends: {"frame": "<base64-webp>", "ts": <unix>}
      - Receives alerts: {"alert": {"type":"phone","confidence":0.83,"ts":<unix>}}
    """
    await websocket.accept()

    # ---- 1) Auth via JWT ----
    try:
        payload = decode_token(token)
        owner_id = payload.get("sub")
        if not owner_id:
            raise ValueError
    except (JWTError, ValueError):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # ---- 2) Verify session belongs to the owner ----
    if mongodb.db is None:
        await websocket.close()
        return

    sess = await mongodb.db.sessions.find_one({
        "_id": ObjectId(session_id),
        "ownerId": ObjectId(owner_id)
    })
    if not sess:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # ---- 3) Main loop: receive frames, run pipeline, send alerts ----
    try:
         while True:
            # Receive raw bytes directly
            msg_bytes = await websocket.receive_bytes()
            
            if not msg_bytes:
                continue

            # Convert PNG bytes to BGR image using OpenCV
            nparr = np.frombuffer(msg_bytes, np.uint8)
            bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)  # decode PNG to BGR

            if bgr is None:
                continue

            # Process the frame through your pipeline
            events = pipeline.process(bgr)
            now = time.time()

            for e in events:
                # Persist event
                await mongodb.db.events.insert_one({
                    "sessionId": ObjectId(session_id),
                    "type": e["type"],
                    "confidence": float(e["confidence"]),
                    "createdAt": None  # optionally datetime.utcnow()
                })
                # Increment session counters
                await mongodb.db.sessions.update_one(
                    {"_id": ObjectId(session_id)},
                    {"$inc": {f"metrics.{e['type']}": 1}}
                )
                # Push alert to client
                await websocket.send_json({"alert": {**e, "ts": now}})
    except WebSocketDisconnect:
        # Client disconnected gracefully
        pass
