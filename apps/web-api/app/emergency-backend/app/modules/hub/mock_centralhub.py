import asyncio
from datetime import datetime, timezone
from app.utils.ids import emg_id
from app.modules.incidents.schemas import Incident, Location, Accident, Violence, Media
from app.modules.incidents.service import compute_scores
from app.modules.incidents.repo import insert_incident
from app.modules.incidents.broadcast import broadcast_incident_update

async def drip_once():
    # Alternate between accident and violence
    now = datetime.now(timezone.utc).isoformat()
    if int(datetime.now().timestamp()) % 2 == 0:
        inc = Incident(
            id=emg_id(),
            source="traffic",
            reported_at=now,
            location=Location(lat=6.9271, lng=79.8612, address="Junction A"),
            severity_grade="medium",
            camera_risk_class="high",
            accident=Accident(vehicles_involved=2, fire_present=False),
            media=Media(image_url=None)
        )
    else:
        inc = Incident(
            id=emg_id(),
            source="violence",
            reported_at=now,
            location=Location(lat=6.9100, lng=79.8600, address="Market B"),
            severity_grade="high",
            camera_risk_class="medium",
            violence=Violence(participants_count=3, weapon_conf=0.7),
            media=Media(image_url=None)
        )
    inc = compute_scores(inc)
    doc = inc.model_dump()
    _id = await insert_incident({**doc})
    doc["mongo_id"] = _id
    await broadcast_incident_update(doc)

async def drip_loop(interval_seconds: int, stop_evt: asyncio.Event):
    while not stop_evt.is_set():
        await drip_once()
        try:
            await asyncio.wait_for(stop_evt.wait(), timeout=interval_seconds)
        except asyncio.TimeoutError:
            pass
