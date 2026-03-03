from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
import logging

from app.config import settings
from app.db.mongo import get_db
from app.db.indexes import ensure_all
from app.modules.auth.routes import router as auth_router
from app.modules.responders.routes import router as responders_router
from app.modules.incidents.routes import router as incidents_router
from app.modules.assignments.routes import router as assignments_router
from app.modules.telemetry.routes import router as telemetry_router
from app.modules.hub.ingest_routes import router as hub_router
from app.modules.routing.routes import router as routing_router
from app.seed.seed_cli import create_admin
from app.jobs.scheduler import start_scheduler

# Setup logging
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
    await start_scheduler()  # Make sure this is awaitable
    
    logger.info("✅ System startup complete")

@app.on_event("shutdown")
async def on_shutdown():
    """Cleanup on shutdown"""
    logger.info("Shutting down Emergency Response System...")
    # Add any cleanup code here if needed

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

# Include all routers
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(responders_router, prefix="/api", tags=["responders"])
app.include_router(incidents_router, prefix="/api", tags=["incidents"])
app.include_router(assignments_router, prefix="/api", tags=["assignments"])
app.include_router(telemetry_router, prefix="/api", tags=["telemetry"])
app.include_router(routing_router, prefix="/api", tags=["routing"])
app.include_router(hub_router, prefix="/hub", tags=["hub"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True if settings.ENV == "development" else False
    )