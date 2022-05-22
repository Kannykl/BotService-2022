from loguru import logger
from pydantic import AnyHttpUrl, BaseSettings


class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Bot service"
    BACKEND_CORS_ORIGINS: list[AnyHttpUrl] = ["http://localhost:8003", "http://localhost:8001"]
    PHONE_STOCK_API_KEY: str = "7c9843e906424458ef8cdb3f5e2d405e"
    CELERY_BROKER_URL: str = "redis://localhost:6379"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379"
    BASE_DB_URL: str = "http://web:8000/db"
    BASE_AUTH_URL: str = "http://web:8000/auth"

    class Config:
        case_sensitive = True


logger.add(
    "bot_service_logs.log",
    format="{time:YYYY-MM-DD at HH:mm:ss} {level} {message}",
    level="DEBUG",
    rotation="10 MB",
    compression="zip",
    serialize=True,
)

settings = Settings()
