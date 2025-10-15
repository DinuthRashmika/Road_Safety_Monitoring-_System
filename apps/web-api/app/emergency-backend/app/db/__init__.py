"""Database bootstrap & index helpers (Motor)."""
from .mongo import get_db, get_client, ensure_indexes
from .collections import USERS, UNITS, INCIDENTS, ASSIGNMENTS

__all__ = ["get_db", "get_client", "ensure_indexes", "USERS", "UNITS", "INCIDENTS", "ASSIGNMENTS"]
