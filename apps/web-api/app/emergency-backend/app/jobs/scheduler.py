import asyncio
from fastapi import FastAPI
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.config import settings
from app.modules.hub.mock_centralhub import drip_loop

_scheduler: AsyncIOScheduler | None = None
_stop_evt: asyncio.Event | None = None
_task: asyncio.Task | None = None

async def start_scheduler(app):
    from app.config import settings
    if not settings.USE_MOCK or settings.MOCK_MODE.lower() == "off":
        return
    _stop_evt = asyncio.Event()
    seconds = 5
    rate = settings.MOCK_DRIP_RATE.strip().lower()
    if rate.endswith("s"): seconds = int(rate[:-1])
    _task = asyncio.create_task(drip_loop(seconds, _stop_evt))

async def stop_scheduler():
    global _stop_evt, _task
    if _stop_evt: _stop_evt.set()
    if _task: 
        try: await _task
        except Exception: pass
