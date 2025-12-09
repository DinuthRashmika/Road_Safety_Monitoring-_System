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

    GOOGLE_MAPS_API_KEY: str | None = os.getenv("GOOGLE_MAPS_API_KEY")

    CORS_ORIGINS: list[str] = [
        "http://localhost:5173" 
    ]

settings = Settings()
