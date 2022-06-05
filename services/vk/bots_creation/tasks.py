"""Celery tasks module"""
import traceback
from enum import Enum

import httpx
from asgiref.sync import async_to_sync
from httpx import AsyncClient
from starlette.status import HTTP_200_OK

from api.circuit_breaker import CircuitException
from api.depends import get_cb_for_tasks
from core.celery import app
from core.config import logger
from core.config import settings
from schemas.task import Task
from services.vk.bots_creation.bots import CreateVkBotsService
from services.vk.bots_creation.phone_stock import OnlineSimPhoneStockService
from services.vk.exceptions import StopCreatingBotsException
from services.vk.exceptions import TaskFailed
from services.vk.vk_service import VKService


class Status(str, Enum):
    SUCCESS: str = "SUCCESS"
    FAILURE: str = "FAILURE"
    CB_STATUS: str = "Service is not working now, try again later."


@app.task
def error_handler(request, exc, _):
    """Error handler for tasks group. If one task failed this handler works."""
    circuit_exception_name: str = "CircuitException"

    if circuit_exception_name in repr(exc):
        async_to_sync(async_update_task_status)(request.id, Status.CB_STATUS)

    else:
        async_to_sync(async_update_task_status)(request.id, Status.FAILURE)


@app.task(bind=True)
def success_handler(self, *args, **kwargs):
    """Success handler for group tasks."""
    async_to_sync(async_update_task_status)(self.request.id, Status.SUCCESS)


async def create_bot(bot: tuple) -> None:
    """Send async request to db to create a bot."""

    try:
        await AsyncClient(base_url=settings.BASE_DB_URL).post(
            "create_bot/",
            json={"bot": {"username": bot[0], "password": bot[1]}},
        )

    except (httpx.ConnectTimeout, httpx.ConnectError):
        logger.error("Can not connect to db service and create_bot")
        raise TaskFailed()


async def async_get_task_by_id(task_id: str) -> Task | None:
    """Send async request to db to get a task."""
    try:
        response = await AsyncClient(base_url=settings.BASE_DB_URL).get(
            f"get_task_by_id/?task_id={task_id}",
        )

        return response.json() if response.status_code == HTTP_200_OK else None

    except (httpx.ConnectTimeout, httpx.ConnectError):
        logger.error("Can not connect to db service and create_bot")
        raise TaskFailed()


async def async_update_task_status(task_id: str, status: str) -> None:
    """Async request to db to update task status."""
    try:
        await AsyncClient(base_url=settings.BASE_DB_URL).patch(
            f"update_task/?task_id={task_id}&task_status={status}"
        )

    except (httpx.ConnectTimeout, httpx.ConnectError):
        logger.error("Can not connect to db service and update task status")
        raise TaskFailed()


@app.task(name="create_bots", throws=(TaskFailed, CircuitException))
def create_bots_task():
    """Start creating bots."""
    func_name = traceback.extract_stack()[1][-2]
    circuit_breaker = get_cb_for_tasks(func_name)

    phone_stock = OnlineSimPhoneStockService()
    bot_service = CreateVkBotsService(phone_stock)

    with circuit_breaker:
        try:
            bot = VKService(bot_service).create_bot()
            async_to_sync(create_bot)(bot)

        except StopCreatingBotsException:
            logger.error("Create bots tasks failed")

            raise TaskFailed
