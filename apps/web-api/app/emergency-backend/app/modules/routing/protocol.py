from typing import Protocol, TypedDict

class RouteResult(TypedDict):
    distance_km: float
    eta_min: float
    mode: str          # adapter name, e.g., "dummy" or "google"
    provider: str      # "haversine" | "google_directions" | "fallback"

class RoutingAdapter(Protocol):
    async def eta(self, from_lat: float, from_lng: float, to_lat: float, to_lng: float) -> RouteResult: ...
