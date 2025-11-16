import asyncio, argparse
from app.db.mongo import get_db
from app.db.indexes import ensure_all # Use the new ensure_all

async def create_admin():
    db = get_db()
    await ensure_all(db) # Use ensure_all
    if await db["users"].count_documents({"email": "admin@example.com"}):
        print("🟡 Admin user already exists.")
        return

    # DEV: store plaintext to avoid bcrypt at startup
    await db["users"].insert_one({
        "name": "System Admin",
        "email": "admin@example.com",
        "role": "admin",
        "password_hash": "Admin@123",
        "location": {"lat": 0.0, "lng": 0.0, "address": "Default Admin Location"} # <-- ADDED
    })
    print("✅ Admin user: admin@example.com / Admin@123 created successfully.")

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--create-admin", action="store_true")
    args = parser.parse_args()
    if args.create_admin:
        await create_admin()

if __name__ == "__main__":
    asyncio.run(main())