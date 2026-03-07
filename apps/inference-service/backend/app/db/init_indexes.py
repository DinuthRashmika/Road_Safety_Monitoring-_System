import app.db.mongodb as mongodb
from pymongo import ASCENDING, DESCENDING

async def ensure_indexes():
    """Create necessary database indexes"""
    if mongodb.db is None:
        return

    database = mongodb.db.db  # ✅ real motor database

    # Users collection indexes
    await mongodb.db.users.create_index("email", unique=True)
    await mongodb.db.users.create_index("nic", unique=True)
    await mongodb.db.users.create_index("phone")

    # Vehicles collection indexes
    await mongodb.db.vehicles.create_index("plateNo", unique=True)
    await mongodb.db.vehicles.create_index("ownerId")
    await mongodb.db.vehicles.create_index([("plateNo", ASCENDING), ("status", ASCENDING)])

    # Violations collection indexes
    await mongodb.db.violations.create_index("plateNumber")
    await mongodb.db.violations.create_index("detectionTime", DESCENDING)
    await mongodb.db.violations.create_index("vehicleId")
    await mongodb.db.violations.create_index([("plateNumber", ASCENDING), ("notified", ASCENDING)])
    await mongodb.db.violations.create_index([("detectionTime", DESCENDING), ("location", ASCENDING)])

    # ✅ Notifications collection indexes (NEW)
    await mongodb.db.notifications.create_index([("ownerId", ASCENDING), ("createdAt", DESCENDING)])
    await mongodb.db.notifications.create_index([("type", ASCENDING), ("createdAt", DESCENDING)])
    await mongodb.db.notifications.create_index("violationId")

    # ✅ Protective Alerts collection indexes (NEW)  ✅✅✅
    await mongodb.db.protective_alerts.create_index([("ownerId", ASCENDING), ("createdAt", DESCENDING)])
    await mongodb.db.protective_alerts.create_index([("ownerId", ASCENDING), ("isRead", ASCENDING), ("createdAt", DESCENDING)])
    await mongodb.db.protective_alerts.create_index("violationId")

    # ✅ DMS
    await database.sessions.create_index([("ownerId", 1), ("startedAt", -1)])
    await database.events.create_index([("sessionId", 1), ("createdAt", -1)])