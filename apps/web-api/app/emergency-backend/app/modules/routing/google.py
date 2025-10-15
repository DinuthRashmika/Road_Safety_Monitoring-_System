from __future__ import annotations
from app.config import settings
from app.utils.geo import haversine_km

def _try_google_client():
    try:
        import googlemaps  # type: ignore
        if not settings.GOOGLE_MAPS_API_KEY:
            return None
        return googlemaps.Client(key=settings.GOOGLE_MAPS_API_KEY)
    except Exception:
        return None

async def eta(from_lat: float, from_lng: float, to_lat: float, to_lng: float) -> dict:
    client = _try_google_client()
    if client:
        try:
            res = client.directions(
                (from_lat, from_lng),
                (to_lat, to_lng),
                mode="driving",
                alternatives=False,
                departure_time="now",
            )
            if res and res[0]["legs"]:
                leg = res[0]["legs"][0]
                distance_km = round(leg["distance"]["value"] / 1000.0, 2)
                eta_min = round(leg["duration"]["value"] / 60.0, 1)
                return {
                    "distance_km": distance_km,
                    "eta_min": eta_min,
                    "mode": "google",
                    "provider": "google_directions",
                }
        except Exception:
            pass

    km = haversine_km(from_lat, from_lng, to_lat, to_lng)
    minutes = round((km / 30.0) * 60.0, 1) if km > 0 else 0.0
    return {
        "distance_km": round(km, 2),
        "eta_min": minutes,
        "mode": "google",
        "provider": "fallback",
    }

async def route(from_lat: float, from_lng: float, to_lat: float, to_lng: float) -> dict:
    """
    Returns a route with encoded polyline (overview), bounds, distance, duration.
    Falls back to straight-line path if Google is unavailable.
    """
    client = _try_google_client()
    if client:
        try:
            res = client.directions(
                (from_lat, from_lng),
                (to_lat, to_lng),
                mode="driving",
                alternatives=False,
                departure_time="now",
            )
            if res and res[0]["legs"]:
                leg = res[0]["legs"][0]
                overview = res[0].get("overview_polyline", {})
                bounds = res[0].get("bounds", {})
                steps = []
                for s in leg.get("steps", []):
                    steps.append({
                        "html_instructions": s.get("html_instructions"),
                        "distance_m": s["distance"]["value"],
                        "duration_s": s["duration"]["value"],
                        "start": {"lat": s["start_location"]["lat"], "lng": s["start_location"]["lng"]},
                        "end": {"lat": s["end_location"]["lat"], "lng": s["end_location"]["lng"]},
                    })
                return {
                    "distance_km": round(leg["distance"]["value"] / 1000.0, 2),
                    "eta_min": round(leg["duration"]["value"] / 60.0, 1),
                    "mode": "google",
                    "provider": "google_directions",
                    "polyline": overview.get("points"),  # Encoded polyline string
                    "bounds": bounds,
                    "start": leg.get("start_location"),
                    "end": leg.get("end_location"),
                    "steps": steps,
                }
        except Exception:
            pass

    # Fallback: straight line polyline not encoded (keep simple)
    km = haversine_km(from_lat, from_lng, to_lat, to_lng)
    minutes = round((km / 30.0) * 60.0, 1) if km > 0 else 0.0
    return {
        "distance_km": round(km, 2),
        "eta_min": minutes,
        "mode": "google",
        "provider": "fallback",
        "polyline": None,
        "path": [  # simple 2-point path (frontend can draw a line)
            {"lat": from_lat, "lng": from_lng},
            {"lat": to_lat, "lng": to_lng},
        ],
        "steps": [],
    }
