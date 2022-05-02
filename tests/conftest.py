import pytest
from httpx import AsyncClient

from main import app


@pytest.fixture()
def db_client():
    app.db_client = AsyncClient(base_url="http://localhost:8003/db/")
    return app.db_client
