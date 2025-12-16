import os
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseModel):
    APP_NAME: str = os.getenv("APP_NAME", "ERS Backend")
    ENV: str = os.getenv("ENV", "development")
    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    DB_NAME: str = os.getenv("DB_NAME", "emergency_db")

    JWT_SECRET: str = os.getenv("JWT_SECRET", "change-me")
    JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "480"))

    # Removed ROUTING_MODE as we default to Google + Fallback
    GOOGLE_MAPS_API_KEY: str | None = os.getenv("GOOGLE_MAPS_API_KEY")
    
    # --- NEW: Path to your YOLO model ---
    # Put your 'best.pt' file in the 'app' folder or specify the full path here
    FIRE_MODEL_PATH: str = os.getenv("FIRE_MODEL_PATH", "app/best.pt")
    FIRE_CONF_THRESHOLD: float = 0.4  # Confidence required to say "Yes, this is fire"

    CORS_ORIGINS: list[str] = [
        "http://localhost:5173" 
    ]

settings = Settings()