# THIS is where app actually lives
# THIS is what uvicorn must load
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from typing import List
# from violence_detection_app.app.config.config import settings
from violence_detection_app.app.api.routes.video_route import router as video_router
from violence_detection_app.app.api.routes.lrcn_routes import router as detection_router
from violence_detection_app.app.api.routes.lrcn_routes import ws_router
# from violence_detection_app.app.api.routes.websocket_route import ws_router

app = FastAPI(
    title = "Violence Detection APp",
    description="Violence",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.include_router(video_router)
app.include_router(ws_router)
app.include_router(detection_router)

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins= origins,
    allow_credentials=True,
    allow_methods=["*"], #delete, put, post
    allow_headers=["*"] #block unrequired headers
)

@app.get("/")
def root():
    return {"message": "Hi Pmalai Sapu API running"}

@app.on_event("startup")
async def show_routes():
    print("\n" + "="*60)
    print("🔍 ALL REGISTERED ROUTES:")
    print("="*60)
    for route in app.routes:
        if hasattr(route, 'path'):
            print(f"  {route.path}")
    print("="*60 + "\n")





