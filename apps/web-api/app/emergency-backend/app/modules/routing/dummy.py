from __future__ import annotations
from app.utils.geo import haversine_km

DEFAULT_SPEED_KMH = 30.0

async def eta(from_lat: float, from_lng: float, to_lat: float, to_lng: float) -> dict:
    km = haversine_km(from_lat, from_lng, to_lat, to_lng)
    minutes = round((km / DEFAULT_SPEED_KMH) * 60.0, 1) if km > 0 else 0.0
    return {
        "distance_km": round(km, 2),
        "eta_min": minutes,
        "mode": "dummy",
        "provider": "haversine",
    }

async def route(from_lat: float, from_lng: float, to_lat: float, to_lng: float) -> dict:
    km = haversine_km(from_lat, from_lng, to_lat, to_lng)
    minutes = round((km / DEFAULT_SPEED_KMH) * 60.0, 1) if km > 0 else 0.0
    return {
        "distance_km": round(km, 2),
        "eta_min": minutes,
        "mode": "dummy",
        "provider": "haversine",
        "polyline": None,  # we return a simple path array in dummy mode
        "path": [
            {"lat": from_lat, "lng": from_lng},
            {"lat": to_lat, "lng": to_lng},
        ],
        "steps": [],
    }
