# app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

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
    BASE_URL: str = "http://localhost:8000"

settings = Settings()
