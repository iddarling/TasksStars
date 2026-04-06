from pydantic_settings import BaseSettings
from typing import List
from pydantic import field_validator


class Settings(BaseSettings):
    PROJECT_NAME: str = "TaskStars"
    SECRET_KEY: str = "0eb5475143912dc2ee158798d4c009e8"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 1 week

    DATABASE_URL: str = "postgresql+asyncpg://postgresql://taskstars_db_user:mNmJnwHFJCReTek6T1OdEJMWIRlfYWVo@dpg-d77u6a75r7bs739k9lkg-a/taskstars_db"

    VAPID_PRIVATE_KEY: str = "f5fbe89b376274602f22b54f65eff87d"
    VAPID_PUBLIC_KEY: str = "17d2b5d5e8320ffc6560d297a3786230"
    VAPID_EMAIL: str = "stepan555bal@gmail.com"

    # CORS origins - включаем localhost и production URL
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "https://tasksstars-1.onrender.com"
    ]

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def set_async_driver(cls, v: str) -> str:
        """Ensure PostgreSQL URL uses asyncpg driver."""
        if v.startswith("postgresql+psycopg2://"):
            return v.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)
        elif v.startswith("postgresql://"):
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    class Config:
        env_file = ".env"


settings = Settings()
