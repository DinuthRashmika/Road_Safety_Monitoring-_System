from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
import logging
from datetime import datetime

from app.config import settings
from app.db.mongo import get_db
from app.db.indexes import ensure_all
from app.modules.auth.routes import router as auth_router
from app.modules.responders.routes import router as responders_router
from app.modules.incidents.routes import router as incidents_router
from app.modules.assignments.routes import router as assignments_router
from app.modules.telemetry.routes import router as telemetry_router
from app.modules.hub.ingest_routes import router as hub_router
from app.modules.hub.h_route import router as human_router
from app.modules.routing.routes import router as routing_router
from app.routes.images import router as images_router  # Custom images router
from app.seed.seed_cli import create_admin
from app.jobs.scheduler import start_scheduler, poll_shenal_database_once
from app.jobs.h_scheduler import start_human_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("ers")

app = FastAPI(title=settings.APP_NAME, default_response_class=ORJSONResponse)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup():
    """Initialize database, create indexes, and start background workers"""
    logger.info("Starting Emergency Response System...")
    
    # Initialize database
    db = get_db()
    await ensure_all(db)
    await create_admin()
    
    # Start background workers
    logger.info("Starting Shenal's Database Polling Worker...")
    await start_scheduler()
    
    logger.info("Starting Human Behavior Database Polling Worker...")
    await start_human_scheduler()
    
    logger.info("✅ System startup complete")

@app.on_event("shutdown")
async def on_shutdown():
    """Cleanup on shutdown"""
    logger.info("Shutting down Emergency Response System...")

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "env": settings.ENV
    }

@app.get("/version")
async def version():
    """Version information"""
    return {
        "app": settings.APP_NAME,
        "env": settings.ENV,
        "version": "1.0.0"
    }

@app.post("/api/demo/force-refresh")
async def force_refresh_incidents():
    """Manually trigger processing of ALL violations (for demo purposes)"""
    try:
        logger.info("Force refresh triggered")
        result = await poll_shenal_database_once()
        return {
            "success": True,
            "message": f"Processed {result} violations",
            "count": result
        }
    except Exception as e:
        logger.error(f"Force refresh failed: {e}")
        return {
            "success": False,
            "message": str(e)
        }

@app.post("/api/demo/force-ignore-normal")
async def force_ignore_normal():
    """Force ignore the latest violation - PERMANENTLY marks it as normal vehicle"""
    from app.db.mongo import get_client
    from bson import ObjectId
    
    client = get_client()
    shenal_db = client["road_safety"]
    violations_collection = shenal_db["violations"]
    emergency_db = client["emergency_db"]
    incidents_collection = emergency_db["incidents"]
    
    latest = await violations_collection.find_one(
        sort=[("_id", -1)]
    )
    
    if latest:
        # Check if this violation already created an incident
        report_id = f"VIOLATION-{str(latest['_id'])}"
        existing_incident = await incidents_collection.find_one({"report_id": report_id})
        
        if existing_incident:
            # Delete the incident if it exists
            await incidents_collection.delete_one({"_id": existing_incident["_id"]})
            logger.info(f"🗑️ Deleted incident for violation: {latest['_id']}")
        
        # Mark it as PERMANENTLY ignored with a special flag
        await violations_collection.update_one(
            {"_id": latest["_id"]},
            {
                "$set": {
                    "emergency_processed": True,
                    "emergency_processed_at": datetime.now().isoformat(),
                    "emergency_success": False,
                    "emergency_note": "PERMANENT_IGNORE - Normal Vehicle",
                    "emergency_permanent_ignore": True
                }
            }
        )
        logger.info(f"🗑️ Removed false positive detection: {latest['_id']}")
        return {"success": True, "ignored": str(latest["_id"])}
    
    logger.info("⚠️ No accident in violation incident")
    return {"success": False, "message": "No violations to ignore"}

app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(responders_router, prefix="/api", tags=["responders"])
app.include_router(incidents_router, prefix="/api", tags=["incidents"])
app.include_router(assignments_router, prefix="/api", tags=["assignments"])
app.include_router(telemetry_router, prefix="/api", tags=["telemetry"])
app.include_router(routing_router, prefix="/api", tags=["routing"])
app.include_router(images_router, prefix="/api", tags=["images"]) 
app.include_router(hub_router, prefix="/hub", tags=["hub"])
app.include_router(human_router, prefix="/hub", tags=["human"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True if settings.ENV == "development" else False
    )