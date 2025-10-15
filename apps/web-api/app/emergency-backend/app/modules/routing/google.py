import math

# Placeholder. When you wire Google Maps, replace this with real API calls.
async def eta_minutes(from_lat, from_lng, to_lat, to_lng, speed_kmh: float = 30.0) -> float:
    # Fallback to the same logic as dummy so callers don't break.
    dlat = math.radians(to_lat - from_lat)
    dlon = math.radians(to_lng - from_lng)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(from_lat))*math.cos(math.radians(to_lat))*math.sin(dlon/2)**2
    km = 2 * 6371.0 * math.asin(math.sqrt(a))
    return round((km / speed_kmh) * 60, 1)
