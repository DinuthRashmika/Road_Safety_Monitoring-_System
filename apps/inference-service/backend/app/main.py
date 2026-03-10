from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.db.mongodb import connect_to_mongo, close_mongo_connection, get_database
from app.core.config import settings
from app.utils.images import ensure_dir
from app.core.security import hash_password
from app.models.user_model import user_doc
import logging
import os
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Road Safety Monitoring System API",
    description="API for vehicle plate detection, owner management, and CCTV integration",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8000",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ensure_dir(settings.UPLOAD_DIR)
app.mount("/static", StaticFiles(directory=settings.UPLOAD_DIR), name="static")

@app.on_event("startup")
async def startup():
    logger.info("Starting Road Safety Monitoring System...")

    try:
        ensure_dir(settings.UPLOAD_DIR)
        ensure_dir(os.path.join(settings.UPLOAD_DIR, "owners"))
        ensure_dir(os.path.join(settings.UPLOAD_DIR, "vehicles"))
        ensure_dir(os.path.join(settings.UPLOAD_DIR, "detections"))
        logger.info(f"✓ Upload directory: {settings.UPLOAD_DIR}")
    except Exception as e:
        logger.error(f"✗ Failed to create upload directories: {e}")

    try:
        connected = await connect_to_mongo()
        if connected:
            logger.info("✓ Connected to MongoDB")

            database = get_database()
            if database is not None:
                admin_email = "admin@example.com"

                try:
                    admin_user = await database.users.find_one({"email": admin_email})

                    admin_id = None
                    if not admin_user:
                        logger.info("Creating System Admin user...")
                        admin_data = user_doc(
                            fullName="System Administrator",
                            email=admin_email,
                            phone="0000000000",
                            address="System HQ",
                            nic="ADMIN001",
                            passwordHash=hash_password("admin@123")
                        )
                        admin_data["role"] = "admin"
                        result = await database.users.insert_one(admin_data)
                        admin_id = result.inserted_id
                        logger.info(f"✅ Admin user created: {admin_email}")
                    else:
                        admin_id = admin_user["_id"]
                        logger.info("✓ Admin user already exists")

                    if admin_id:
                        existing_owner_profile = await database.owners.find_one({"user_id": str(admin_id)})

                        if not existing_owner_profile:
                            logger.info("Creating Admin Owner Profile (Critical for API)...")
                            owner_profile = {
                                "user_id": str(admin_id),
                                "name": "System Administrator",
                                "email": admin_email,
                                "phone": "0000000000",
                                "address": "System HQ",
                                "nic": "ADMIN001",
                                "role": "admin",
                                "is_active": True,
                                "createdAt": datetime.utcnow()
                            }
                            await database.owners.insert_one(owner_profile)
                            logger.info("✅ Admin owner profile created successfully")
                        else:
                            logger.info("✓ Admin owner profile already exists")

                except Exception as e:
                    logger.error(f"Error seeding admin user: {e}")
        else:
            logger.error("✗ Failed to connect to MongoDB")
    except Exception as e:
        logger.error(f"✗ MongoDB connection error: {e}")

    logger.info("✅ Application startup complete")

@app.on_event("shutdown")
async def shutdown():
    logger.info("Shutting down...")
    await close_mongo_connection()
    logger.info("✅ Application shutdown complete")

from app.routes.auth import router as auth_router
from app.routes.owners import router as owners_router
from app.routes.vehicles import router as vehicles_router
from app.routes.violations import router as violations_router
from app.routes.detection import router as detection_router
from app.routes.admin import router as admin_router
from app.routes.camera_integration import router as camera_integration_router
from app.routes.mobile_notifications import router as notifications_router
from app.routes.payments import router as payments_router
from app.routes import sessions_rest, sessions_ws, debug_yolo
from app.routes.protective_alerts import router as protective_alerts_router

app.include_router(auth_router)
app.include_router(owners_router)
app.include_router(vehicles_router)
app.include_router(violations_router)
app.include_router(detection_router)
app.include_router(admin_router)
app.include_router(camera_integration_router)
app.include_router(notifications_router)
app.include_router(payments_router)
app.include_router(sessions_rest.router)
app.include_router(sessions_ws.router)
app.include_router(debug_yolo.router)
app.include_router(protective_alerts_router)

logger.info("✓ All routers loaded successfully")

@app.get("/")
async def root():
    return {
        "message": "Road Safety Monitoring System API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}