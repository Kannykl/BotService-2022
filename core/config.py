from loguru import logger
from pydantic import AnyHttpUrl
from pydantic import BaseSettings


class Settings(BaseSettings):
    API_PREFIX: str = "/api/bots"
    PROJECT_NAME: str = "Bot service"
    BACKEND_CORS_ORIGINS: list[AnyHttpUrl] = []
    PHONE_STOCK_API_KEY: str = "7c9843e906424458ef8cdb3f5e2d405e"
    CELERY_BROKER_URL: str = "redis://localhost:6379"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379"
    BASE_DB_URL: str = "http://web:8001/db"
    BASE_AUTH_URL: str = "http://web:8001/auth"
    DEBUG: bool = True

    class Config:
        case_sensitive = True


settings = Settings()

logger.add(
    "bot_service_logs.log",
    format="{time:YYYY-MM-DD at HH:mm:ss} {level} {message}",
    level="DEBUG" if settings.DEBUG else "INFO",
    rotation="10 MB",
    compression="zip",
    serialize=True,
)
