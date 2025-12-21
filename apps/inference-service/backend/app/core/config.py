from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal
import os

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # MongoDB
    MONGODB_URI: str
    MONGODB_DB: str = "road_safety"

    # JWT (for admin/owner portal only)
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24 * 7

    # File uploads
    UPLOAD_DIR: str = "uploads"
    ENVIRONMENT: Literal["development", "production"] = "development"
    
    # Plate Detection Model
    YOLO_MODEL: str = "weights/licence.pt"
    
    # Notification settings
    SEND_NOTIFICATIONS: bool = True
    NOTIFICATION_MESSAGE: str = "Your vehicle has been detected by our road safety monitoring system."
    
    # CCTV/Webcam settings
    WEBCAM_SOURCE: int = 0
    DETECTION_CONFIDENCE: float = 0.5
    FRAME_SKIP: int = 5
    SAVE_DETECTED_IMAGES: bool = True
    DETECTED_IMAGES_DIR: str = "detections"
    
    # API Server
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    

settings = Settings()