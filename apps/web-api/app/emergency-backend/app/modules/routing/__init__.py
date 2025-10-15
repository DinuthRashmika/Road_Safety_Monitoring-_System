from app.config import settings
from . import dummy, google

async def eta(from_lat: float, from_lng: float, to_lat: float, to_lng: float) -> dict:
    if settings.ROUTING_MODE.lower().strip() == "google":
        return await google.eta(from_lat, from_lng, to_lat, to_lng)
    return await dummy.eta(from_lat, from_lng, to_lat, to_lng)

async def route(from_lat: float, from_lng: float, to_lat: float, to_lng: float) -> dict:
    if settings.ROUTING_MODE.lower().strip() == "google":
        return await google.route(from_lat, from_lng, to_lat, to_lng)
    return await dummy.route(from_lat, from_lng, to_lat, to_lng)

__all__ = ["eta", "route"]
