from typing import Protocol

class RoutingAdapter(Protocol):
    async def eta_minutes(self, from_lat: float, from_lng: float, to_lat: float, to_lng: float) -> float: ...
