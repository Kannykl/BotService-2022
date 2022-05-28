"""Celery tasks module"""

import time
from celery.result import AsyncResult
from httpx import AsyncClient
from asgiref.sync import async_to_sync
from core.celery import app
from services.vk.vk_service import VKService
from services.vk.bots_creation.phone_stock import OnlineSimPhoneStockService
from services.vk.bots_creation.bots import CreateVkBotsService
from core.config import logger, settings
from dataclasses import dataclass


@dataclass
class Status:
    SUCCESS: str = "SUCCESS"
    FAILURE: str = "FAILURE"


async def create_bot(bot: list) -> None:
    """Send async request to db to create a bot."""
    await AsyncClient(base_url=settings.BASE_DB_URL).post(f"create_bot/", json={
        "bot": {
            "username": bot[0],
            "password": bot[1]
        }})


async def async_update_task_status(task_id: str, status: str) -> None:
    await AsyncClient(base_url=settings.BASE_DB_URL).patch(
        f"update_task/?task_id={task_id}&task_status={status}")


@app.task(name="create_bots")
def create_bots_task(count: int = 1) -> list:
    """Start creating bots."""
    phone_stock = OnlineSimPhoneStockService()
    bot_service = CreateVkBotsService(phone_stock)

    bots = VKService(bot_service).create_bots(count)

    return bots


@app.task()
def create_bots_listener(result: str) -> None:
    """After creating all bots send request to db to create bots."""

    for bot in result:
        async_to_sync(create_bot)(bot)
        logger.info(f"{bot[0]} is added in DB!")


@app.task(name="update_task_status")
def update_task_status(task_id: str) -> None:
    """Update group task status."""
    result = AsyncResult(task_id)
    count = 0

    while not result.ready():
        time.sleep(45)
        count += 1

        if count == 4:
            async_to_sync(async_update_task_status)(result.id, Status.FAILURE)
            return

    if result.successful():
        async_to_sync(async_update_task_status)(result.id, Status.SUCCESS)
    elif result.failed():
        async_to_sync(async_update_task_status)(result.id, Status.FAILURE)
