# app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal

class Settings(BaseSettings):
    # Tell pydantic-settings v2 where the .env is
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",          # ignore unexpected env vars
    )

    # Env variables (must exist in .env or OS env)
    MONGODB_URI: str
    MONGODB_DB: str = "road_safety"

    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    UPLOAD_DIR: str = "uploads"
    ENVIRONMENT: Literal["development", "production"] = "development"  # ← ADDED
    
    # ---- DMS (seatbelt/phone stage) ----
    YOLO_MODEL: str = "weights/best.pt"  # path to your trained model
    MAX_FPS: int = 2
    LOG_LEVEL: str = "INFO"

    @property
    def BASE_URL(self) -> str:
        if self.ENVIRONMENT == "production":
            return "https://your-production-domain.com"  # Your production URL
        else:
            return "http://10.0.2.2:8000"  # Default for Android emulator

settings = Settings()