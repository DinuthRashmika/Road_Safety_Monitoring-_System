# app/modules/incidents/broadcast.py
from __future__ import annotations

import asyncio
import json

_incident_queue: asyncio.Queue[bytes] | None = None

def get_queue() -> asyncio.Queue[bytes]:
    global _incident_queue
    if _incident_queue is None:
        _incident_queue = asyncio.Queue()
    return _incident_queue

async def broadcast_incident_update(doc: dict):
    q = get_queue()
    await q.put(
        json.dumps({"type": "incident_update", "data": doc}, separators=(",", ":"))
        .encode("utf-8")
    )
