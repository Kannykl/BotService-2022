import pytest
from httpx import AsyncClient
from core.config import settings
from main import app


@pytest.fixture()
def db_client():
    app.db_client = AsyncClient(base_url=settings.BASE_DB_URL)
    return app.db_client
