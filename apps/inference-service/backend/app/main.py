# app/main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware   # <-- add this
from app.db.mongodb import connect_to_mongo, close_mongo_connection
from app.db.init_indexes import ensure_indexes
from app.routes import auth, owners, vehicles
from app.core.config import settings
from app.utils.images import ensure_dir
# new DMS routers
from app.routes import sessions_rest, sessions_ws, debug_yolo

app = FastAPI(title="Road Safety – Owner & Vehicles API", version="1.0.0")

# CORS (set your mobile/web origins here)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*",                    # or e.g. "http://localhost:3000", "http://10.0.2.2:8080"
    ],
    allow_credentials=True,
    allow_methods=["*"],       # enables OPTIONS, POST, etc.
    allow_headers=["*"],       # e.g., Authorization, Content-Type
)

app.mount("/static", StaticFiles(directory=settings.UPLOAD_DIR), name="static")

@app.on_event("startup")
async def startup():
    ensure_dir(settings.UPLOAD_DIR)
    await connect_to_mongo()
    await ensure_indexes()

@app.on_event("shutdown")
async def shutdown():
    await close_mongo_connection()

app.include_router(auth.router)
app.include_router(owners.router)
app.include_router(vehicles.router)

# DMS
app.include_router(sessions_rest.router)
app.include_router(sessions_ws.router)
app.include_router(debug_yolo.router)


