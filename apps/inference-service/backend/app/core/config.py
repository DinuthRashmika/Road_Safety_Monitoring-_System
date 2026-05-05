from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal, Dict, Optional
import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]


def configure_ultralytics_dir() -> None:
    """Keep Ultralytics runtime settings inside the backend workspace."""
    config_dir = os.environ.get("YOLO_CONFIG_DIR")
    if not config_dir:
        config_dir = str(BASE_DIR / ".ultralytics")
        os.environ["YOLO_CONFIG_DIR"] = config_dir
    os.makedirs(config_dir, exist_ok=True)


configure_ultralytics_dir()

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
    YOLO_MODELS: str = "weights/licence.pt"
    
    # --- NEW: Violation Model & Fines ---
    VIOLATION_MODEL: str = "weights/bests.pt"

    # Violation Fines (Currency: LKR)
    # Make sure these keys match the CLASS NAMES inside your violation.pt model
    VIOLATION_FINES: Dict[str, float] = {
        "single_line_cross": 2000.0,
        "double_line_cross": 5000.0,
        "no_helmet": 1000.0,
        "triple_riding": 1500.0, # 2+ persons on bike
        "default": 1000.0
    }
    # ------------------------------------
    
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

    # Payments
    STRIPE_SECRET_KEY: Optional[str] = None

# ---- DMS (seatbelt/phone stage) ----
    YOLO_MODEL: str = "weights/best.pt"  # path to your trained model
    MAX_FPS: int = 2
    LOG_LEVEL: str = "INFO"
    

settings = Settings()
