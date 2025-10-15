"""Central Hub adapters (ingest + mock/replay + fire detector)."""
from .ingest_routes import router

__all__ = ["router"]
