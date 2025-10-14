# app/db/init_indexes.py
import app.db.mongodb as mongodb

async def ensure_indexes():
    db = mongodb.db
    if db is None:
        # extra safety guard so the error is clearer if connect_to_mongo wasn't awaited
        raise RuntimeError("Mongo database is not initialized. Call connect_to_mongo() first.")

    # Users
    await db.users.create_index("email", unique=True)
    await db.users.create_index("nic", unique=True)

    # Vehicles
    await db.vehicles.create_index("plateNo", unique=True)
    await db.vehicles.create_index([("ownerId", 1)])
