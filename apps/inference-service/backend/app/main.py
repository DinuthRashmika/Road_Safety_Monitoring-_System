# app/main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.db.mongodb import connect_to_mongo, close_mongo_connection
from app.db.init_indexes import ensure_indexes
from app.routes import auth, owners, vehicles
from app.core.config import settings
from app.utils.images import ensure_dir

app = FastAPI(title="Road Safety – Owner & Vehicles API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://10.0.2.2:8000",
        "http://localhost",
        "http://127.0.0.1",
        "http://10.0.2.2",
        "http://192.168.8.196:8000",
        "http://192.168.8.196",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# static mount name must be "static" so request.url_for("static", path=...) works
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
