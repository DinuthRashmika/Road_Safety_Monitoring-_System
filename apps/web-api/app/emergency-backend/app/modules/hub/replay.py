import asyncio, json
from datetime import datetime, timezone
from pathlib import Path
from app.modules.incidents.schemas import Incident
from app.modules.incidents.service import compute_scores
from app.modules.incidents.repo import insert_incident
from app.modules.incidents.broadcast import broadcast_incident_update

async def replay_jsonl(path: str, speed: float = 1.0, stop_evt: asyncio.Event | None = None):
    """
    Replays incidents from a .jsonl file. Each line = Incident JSON.
    If the incident has 'reported_at', we try to keep relative timing scaled by `speed`.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(path)

    prev_ts = None
    for line in p.read_text(encoding="utf-8").splitlines():
        if stop_evt and stop_evt.is_set():
            break
        if not line.strip():
            continue
        raw = json.loads(line)
        if "reported_at" not in raw:
            raw["reported_at"] = datetime.now(timezone.utc).isoformat()

        ts = datetime.fromisoformat(raw["reported_at"].replace("Z","+00:00")).timestamp()
        if prev_ts is not None:
            dt = max(0.0, (ts - prev_ts) / max(0.1, speed))
            try:
                await asyncio.wait_for(asyncio.sleep(dt), timeout=dt+1)
            except asyncio.TimeoutError:
                pass
        prev_ts = ts

        inc = Incident(**raw)
        inc = compute_scores(inc)
        doc = inc.model_dump()
        mongo_id = await insert_incident({**doc})
        doc["mongo_id"] = mongo_id
        await broadcast_incident_update(doc)
