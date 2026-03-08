from __future__ import annotations

from typing import Iterable, Tuple
from motor.core import AgnosticDatabase
from pymongo import ASCENDING, DESCENDING, GEOSPHERE, IndexModel


async def _ensure_collection(db: AgnosticDatabase, name: str) -> None:
    try:
        await db.create_collection(name)
    except Exception:
        pass


async def _create_indexes(db: AgnosticDatabase, coll_name: str, indexes: Iterable[IndexModel]) -> None:
    if not indexes:
        return
    try:
        await db[coll_name].create_indexes(list(indexes))
    except Exception:
        pass


async def ensure_all(db: AgnosticDatabase) -> None:


    await _ensure_collection(db, "users")
    user_indexes = [
        IndexModel([("email", ASCENDING)], unique=True, name="ux_users_email"),
        IndexModel([("role", ASCENDING)], name="ix_users_role"),
        IndexModel([("location", GEOSPHERE)], name="gx_users_location"),
    ]
    await _create_indexes(db, "users", user_indexes)

    
    await _ensure_collection(db, "incidents")
    incident_indexes = [
        IndexModel([("status", ASCENDING), ("score", DESCENDING)], name="ix_incidents_status_score"),
        IndexModel([("reported_at", DESCENDING)], name="ix_incidents_reported_at"),
        IndexModel([("location", GEOSPHERE)], name="gx_incidents_location"), 
        IndexModel([("source", ASCENDING)], name="ix_incidents_source"),
        IndexModel([("camera_risk_class", ASCENDING)], name="ix_incidents_risk"),
        IndexModel([("severity_grade", ASCENDING)], name="ix_incidents_severity"),
    ]
    await _create_indexes(db, "incidents", incident_indexes)

    await _ensure_collection(db, "assignments")
    assignment_indexes = [
        IndexModel([("incident_id", ASCENDING)], name="ix_assignments_incident"),
        IndexModel([("responder_id", ASCENDING)], name="ix_assignments_responder"),
        IndexModel([("at", DESCENDING)], name="ix_assignments_at"),
    ]
    await _create_indexes(db, "assignments", assignment_indexes)
    
    await _ensure_collection(db, "notifications")
    notif_indexes = [
        IndexModel([("to", ASCENDING), ("created_at", DESCENDING)], name="ix_notifications_to_created"),
        IndexModel([("delivered", ASCENDING)], name="ix_notifications_delivered"),
    ]
    await _create_indexes(db, "notifications", notif_indexes)