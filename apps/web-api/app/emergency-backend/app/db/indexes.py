# app/db/indexes.py
from __future__ import annotations

from typing import Iterable, Tuple
from motor.core import AgnosticDatabase
from pymongo import ASCENDING, DESCENDING, GEOSPHERE, IndexModel


async def _ensure_collection(db: AgnosticDatabase, name: str) -> None:
    """Create the collection if it does not exist (idempotent)."""
    try:
        await db.create_collection(name)
    except Exception:
        # Ignore "NamespaceExists" or any already-exists condition
        pass


async def _create_indexes(db: AgnosticDatabase, coll_name: str, indexes: Iterable[IndexModel]) -> None:
    if not indexes:
        return
    try:
        await db[coll_name].create_indexes(list(indexes))
    except Exception:
        # In dev environments we prefer not to crash on index races.
        # Log in production if you have a logger wired.
        pass


async def ensure_all(db: AgnosticDatabase) -> None:
    """
    Create all collections and indexes used by the service.
    Call this once at startup (e.g., in app startup event).
    """

    # -----------------
    # users
    # -----------------
    await _ensure_collection(db, "users")
    user_indexes = [
        IndexModel([("email", ASCENDING)], unique=True, name="ux_users_email"),
        IndexModel([("role", ASCENDING)], name="ix_users_role"),
    ]
    await _create_indexes(db, "users", user_indexes)

    # -----------------
    # units (physical responder units/crews)
    # -----------------
    await _ensure_collection(db, "units")
    unit_indexes = [
        IndexModel([("type", ASCENDING), ("status", ASCENDING)], name="ix_units_type_status"),
        IndexModel([("code", ASCENDING)], unique=True, name="ux_units_code"),
    ]
    await _create_indexes(db, "units", unit_indexes)

    # -----------------
    # incidents
    # -----------------
    await _ensure_collection(db, "incidents")
    incident_indexes = [
        IndexModel([("status", ASCENDING), ("score", DESCENDING)], name="ix_incidents_status_score"),
        IndexModel([("reported_at", DESCENDING)], name="ix_incidents_reported_at"),
        IndexModel([("location", GEOSPHERE)], name="gx_incidents_location"),  # 2dsphere for geo queries
        IndexModel([("source", ASCENDING)], name="ix_incidents_source"),
        IndexModel([("camera_risk_class", ASCENDING)], name="ix_incidents_risk"),
        IndexModel([("severity_grade", ASCENDING)], name="ix_incidents_severity"),
    ]
    await _create_indexes(db, "incidents", incident_indexes)

    # -----------------
    # assignments (status timeline / responder progress)
    # -----------------
    await _ensure_collection(db, "assignments")
    assignment_indexes = [
        IndexModel([("incident_id", ASCENDING)], name="ix_assignments_incident"),
        IndexModel([("unit_id", ASCENDING)], name="ix_assignments_unit"),
        IndexModel([("at", DESCENDING)], name="ix_assignments_at"),
    ]
    await _create_indexes(db, "assignments", assignment_indexes)

    # -----------------
    # notifications (optional; safe if unused)
    # -----------------
    await _ensure_collection(db, "notifications")
    notif_indexes = [
        IndexModel([("to", ASCENDING), ("created_at", DESCENDING)], name="ix_notifications_to_created"),
        IndexModel([("delivered", ASCENDING)], name="ix_notifications_delivered"),
    ]
    await _create_indexes(db, "notifications", notif_indexes)
