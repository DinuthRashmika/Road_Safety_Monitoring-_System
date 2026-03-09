from typing import List
from pydantic_settings import BaseSettings
from pydantic import field_validator

class Settings(BaseSettings):
    API_PREFIX: str = "/api"
    DEBUG: bool = False

    # Make optional / safe defaults
    DATABASE_URL: str = ""
    ORIGIN_API_KEY: str = ""

    ALLOWED_ORIGINS: str = {
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    }

    @field_validator("ALLOWED_ORIGINS")
    def parse_allowed_origins(cls, v: str) -> List[str]:
        return [origin.strip() for origin in v.split(",")] if v else []

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

settings = Settings()
