"""Routing adapters (dummy / google)."""
from app.config import settings
from . import dummy, google

# Simple selector so callers can do: from app.modules.routing import eta_minutes
async def eta_minutes(from_lat: float, from_lng: float, to_lat: float, to_lng: float) -> float:
    if settings.ROUTING_MODE.lower() == "google":
        return await google.eta_minutes(from_lat, from_lng, to_lat, to_lng)
    return await dummy.eta_minutes(from_lat, from_lng, to_lat, to_lng)

__all__ = ["eta_minutes"]
