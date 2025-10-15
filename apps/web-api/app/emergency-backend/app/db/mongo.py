from motor.motor_asyncio import AsyncIOMotorClient
from motor.core import AgnosticDatabase
from app.config import settings

_client: AsyncIOMotorClient | None = None

def get_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(settings.MONGODB_URI)
    return _client

def get_db() -> AgnosticDatabase:
    return get_client()[settings.DB_NAME]

async def ensure_indexes():
    db = get_db()
    # users
    try:
        await db.create_collection("users")
    except Exception:
        pass
    await db["users"].create_index("email", unique=True)

    # units
    try:
        await db.create_collection("units")
    except Exception:
        pass
    await db["units"].create_index([("type", 1), ("status", 1)])

    # incidents
    try:
        await db.create_collection("incidents")
    except Exception:
        pass
    await db["incidents"].create_index([("status", 1), ("score", -1)])
    await db["incidents"].create_index([("reported_at", -1)])
    try:
        await db["incidents"].create_index([("location", "2dsphere")])
    except Exception:
        pass

    # assignments
    try:
        await db.create_collection("assignments")
    except Exception:
        pass
    await db["assignments"].create_index([("incident_id", 1)])
    await db["assignments"].create_index([("unit_id", 1)])
