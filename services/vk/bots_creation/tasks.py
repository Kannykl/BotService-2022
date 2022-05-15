"""Celery tasks module"""

import time
from celery.result import GroupResult, ResultSet
from httpx import AsyncClient
from asgiref.sync import async_to_sync
from core.celery import app
from services.vk.vk_service import VKService
from services.vk.bots_creation.phone_stock import OnlineSimPhoneStockService
from services.vk.bots_creation.bots import CreateVkBotsService
from core.config import logger, settings


async def create_bot(bot):
    """Send async request to db to create a bot."""
    await AsyncClient(base_url=settings.BASE_DB_URL).post(f"create_bot/", json={
        "bot": {
            "username": f"+7{bot[0]}",
            "password": bot[1]
        }})


async def async_update_task_status(task_id: str, status: str):
    await AsyncClient(base_url=settings.BASE_DB_URL).patch(
        f"update_task/?task_id={task_id}&task_status={status}")


@app.task(name="create_bots")
def create_bots_task(count: int = 1):
    """Start creating bots."""
    phone_stock = OnlineSimPhoneStockService()
    bot_service = CreateVkBotsService(phone_stock)

    bots = VKService(bot_service).create_bots(count)

    return bots


@app.task()
def create_bots_listener(result: str):
    """After creating all bots send request to db to create bots."""

    for bot in result:
        async_to_sync(create_bot)(bot)
        logger.info(f"{bot[0]} is added in DB!")


@app.task(name="update_task_status")
def update_task_status(task_id: str):
    """Update group task status."""
    result = GroupResult.restore(task_id)

    if result:
        result_set = ResultSet(result.results)

        while not result_set.ready():
            time.sleep(45)

        if result_set.successful():
            async_to_sync(async_update_task_status)(result.id, "SUCCESS")
        elif result_set.failed():
            async_to_sync(async_update_task_status)(result.id, "FAILURE")
