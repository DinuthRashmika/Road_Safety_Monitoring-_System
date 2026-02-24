from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from jose import JWTError
from bson import ObjectId
import base64, numpy as np, cv2, time
import app.db.mongodb as mongodb
from app.core.security import decode_token
from app.services.inference.pipeline import DmsPipeline

router = APIRouter(tags=["DMS WebSocket"])
pipeline = DmsPipeline()  # load once


@router.websocket("/ws/sessions/{session_id}")
async def ws_session(websocket: WebSocket, session_id: str, token: str):
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
    if mongodb.db is None or mongodb.db.db is None:
        await websocket.close()
        return

    database = mongodb.db.db  # ✅ real motor db

    sess = await database.sessions.find_one({  # ✅
        "_id": ObjectId(session_id),
        "ownerId": ObjectId(owner_id)
    })
    if not sess:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # ---- 3) Main loop ----
    try:
        while True:
            msg_bytes = await websocket.receive_bytes()
            if not msg_bytes:
                continue

            nparr = np.frombuffer(msg_bytes, np.uint8)
            bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if bgr is None:
                continue

            events = pipeline.process(bgr)
            now = time.time()

            for e in events:
                # Persist event
                await database.events.insert_one({  # ✅
                    "sessionId": ObjectId(session_id),
                    "type": e["type"],
                    "confidence": float(e["confidence"]),
                    "createdAt": None  # optionally datetime.utcnow()
                })

                # Increment session counters
                await database.sessions.update_one(  # ✅
                    {"_id": ObjectId(session_id)},
                    {"$inc": {f"metrics.{e['type']}": 1}}
                )

                # Push alert
                await websocket.send_json({"alert": {**e, "ts": now}})

    except WebSocketDisconnect:
        pass