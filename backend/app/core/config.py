# core/config.py
# Central configuration — reads from environment variables

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    APP_NAME: str = "MedDevice Risk Predictor"
    APP_VERSION: str = "1.0.0"

    # MySQL
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = ""
    DB_NAME: str = "meddevice"

    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]

    # ML model paths
    MODEL_PATH: str = "app/ml/model.pkl"
    PIPELINE_PATH: str = "app/ml/pipeline.pkl"

    # Auth
    SECRET_KEY: str = "sentrymed-secret-key-change-in-prod"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    ALERT_PROB_THRESHOLD: float = 0.42

    class Config:
        env_file = ".env"


settings = Settings()
