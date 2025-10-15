from app.utils.geo import haversine_km

async def eta_minutes(from_lat, from_lng, to_lat, to_lng, speed_kmh=30.0) -> float:
    km = haversine_km(from_lat, from_lng, to_lat, to_lng)
    return round((km / speed_kmh) * 60, 1)
