from fastapi.testclient import TestClient
from httpx import AsyncClient
import pytest
from main import app
from services.vk.vk_service import VKService


client = TestClient(app)


async def bot_data():
    """Bot data."""

    return [
        ("bot_name", "bot_password"),
    ]


def mock_create_bot(*args, **kwargs):
    """Mock create bot."""

    return bot_data()


@pytest.mark.asyncio
async def test_create_one_bot(monkeypatch, db_client):
    """Test create one bot."""
    monkeypatch.setattr(VKService, "create_bots", mock_create_bot)
    monkeypatch.setattr(app, "db_client", db_client)

    response = client.post("/api/v1/create_bots/1")

    username = response.json()[0]["username"]

    assert response.status_code == 200

    async with AsyncClient(base_url="http://localhost:8003/db/") as async_client:
        response_ = await async_client.get(f"get_bot_by_username/?username={username}")

    assert response_.status_code == 200

    assert response_.json() is not None
    assert response_.json()["username"] is not None
