from typing import Protocol, TypedDict

class RouteResult(TypedDict):
    distance_km: float
    eta_min: float
    mode: str         
    provider: str      

class RoutingAdapter(Protocol):
    async def eta(self, from_lat: float, from_lng: float, to_lat: float, to_lng: float) -> RouteResult: ...
