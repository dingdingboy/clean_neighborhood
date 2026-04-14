from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "Violation Reporter"
    DEBUG: bool = False
    VERSION: str = "0.1.0"

    # Database
    DATABASE_URL: str = "sqlite:///storage/db.sqlite"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # AI Model
    MODEL_PATH: str = "./models/qwen3_5_vl_openvino"
    OPENVINO_DEVICE: str = "CPU"

    # Storage
    STORAGE_PATH: Path = Path("./storage/uploads")
    MAX_UPLOAD_SIZE: int = 104_857_600  # 100MB

    # Security
    API_KEY: Optional[str] = None
    API_KEY_HEADER: str = "X-API-Key"
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    # Celery
    CELERY_BROKER_URL: Optional[str] = None
    CELERY_RESULT_BACKEND: Optional[str] = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Derive Celery URLs from REDIS_URL if not set
        if not self.CELERY_BROKER_URL:
            self.CELERY_BROKER_URL = self.REDIS_URL
        if not self.CELERY_RESULT_BACKEND:
            self.CELERY_RESULT_BACKEND = self.REDIS_URL


settings = Settings()
