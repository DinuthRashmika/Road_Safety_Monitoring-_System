from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

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
    db = get_db()
    await ensure_all(db)
    await create_admin()  

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/version")
async def version():
    return {"app": settings.APP_NAME, "env": settings.ENV}

app.include_router(auth_router,        prefix="/api/auth", tags=["auth"])
app.include_router(responders_router,  prefix="/api",      tags=["responders"])
app.include_router(incidents_router,   prefix="/api",      tags=["incidents"])
app.include_router(assignments_router, prefix="/api",      tags=["assignments"])
app.include_router(telemetry_router,   prefix="/api",      tags=["telemetry"])
app.include_router(routing_router,     prefix="/api",      tags=["routing"])
app.include_router(hub_router,         prefix="/hub",      tags=["hub"])