from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    PROJECT_NAME: str = "TaskStars"
    SECRET_KEY: str = "YOUR_SECRET_KEY_REPLACE_ME"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 1 week

    DATABASE_URL: str = "sqlite+aiosqlite:///./taskstars.db"
    VAPID_PRIVATE_KEY: str = ""
    VAPID_PUBLIC_KEY: str = ""
    VAPID_EMAIL: str = "admin@taskstars.app"

    # CORS origins - включаем localhost и production URL
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "https://taskstars-frontend.onrender.com"
    ]

    class Config:
        env_file = ".env"


settings = Settings()
