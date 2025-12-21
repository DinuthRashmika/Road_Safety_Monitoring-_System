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

# Configure logging
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

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create uploads directory
ensure_dir(settings.UPLOAD_DIR)

# Mount static files
app.mount("/static", StaticFiles(directory=settings.UPLOAD_DIR), name="static")

@app.on_event("startup")
async def startup():
    """Initialize application on startup"""
    logger.info("Starting Road Safety Monitoring System...")
    
    # Create directories
    try:
        ensure_dir(settings.UPLOAD_DIR)
        ensure_dir(os.path.join(settings.UPLOAD_DIR, "owners"))
        ensure_dir(os.path.join(settings.UPLOAD_DIR, "vehicles"))
        ensure_dir(os.path.join(settings.UPLOAD_DIR, "detections"))
        logger.info(f"✓ Upload directory: {settings.UPLOAD_DIR}")
    except Exception as e:
        logger.error(f"✗ Failed to create upload directories: {e}")
    
    # Connect to MongoDB
    try:
        connected = await connect_to_mongo()
        if connected:
            logger.info("✓ Connected to MongoDB")
            
            # --- SEED ADMIN USER ---
            database = get_database()
            if database is not None:
                admin_email = "admin" # Admin Username
                try:
                    existing_admin = await database.users.find_one({"email": admin_email})
                    
                    if not existing_admin:
                        logger.info("Creating System Admin user...")
                        admin_data = user_doc(
                            fullName="System Administrator",
                            email=admin_email,
                            phone="0000000000",
                            address="System HQ",
                            nic="ADMIN001",
                            passwordHash=hash_password("admin@123") # Admin Password
                        )
                        # Force role to admin (override default 'owner' role from user_doc)
                        admin_data["role"] = "admin"
                        
                        await database.users.insert_one(admin_data)
                        logger.info("✅ Admin user created: username='admin', password='admin@123'")
                    else:
                        logger.info("✓ Admin user already exists")
                except Exception as e:
                    logger.error(f"Error seeding admin user: {e}")
            # -----------------------------

        else:
            logger.error("✗ Failed to connect to MongoDB")
    except Exception as e:
        logger.error(f"✗ MongoDB connection error: {e}")
    
    logger.info("✅ Application startup complete")

@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown"""
    logger.info("Shutting down...")
    await close_mongo_connection()
    logger.info("✅ Application shutdown complete")

# Import routers
from app.routes.auth import router as auth_router
from app.routes.owners import router as owners_router
from app.routes.vehicles import router as vehicles_router
from app.routes.violations import router as violations_router
from app.routes.detection import router as detection_router
from app.routes.admin import router as admin_router
from app.routes.camera_integration import router as camera_integration_router
# Import NEW notification router
from app.routes.mobile_notifications import router as notifications_router

# Include routers
app.include_router(auth_router)
app.include_router(owners_router)
app.include_router(vehicles_router)
app.include_router(violations_router)
app.include_router(detection_router)
app.include_router(admin_router)
app.include_router(camera_integration_router)
# Register NEW notification router
app.include_router(notifications_router)

logger.info("✓ All routers loaded successfully")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Road Safety Monitoring System API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running",
        "endpoints": {
            "auth": {
                "register": "/api/auth/register-owner",
                "login": "/api/auth/login"
            },
            "admin": {
                "register_camera": "/api/admin/cameras",
                "list_cameras": "/api/admin/cameras"
            },
            "cctv": {
                "upload": "/api/cctv/{camera_id}/upload-violation"
            },
            "owners": "/api/owners/me",
            "vehicles": {
                "create": "/api/vehicles",
                "list": "/api/vehicles/mine"
            },
            "notifications": {
                "list": "/api/notifications/",
                "read": "/api/notifications/{id}/read"
            },
            "detection": "/api/detection/detect-plate",
            "violations": "/api/violations"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Road Safety Monitoring System API"
    }