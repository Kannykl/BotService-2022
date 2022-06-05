"""Boost stat tasks module"""
import traceback

import httpx
from asgiref.sync import async_to_sync
from httpx import AsyncClient
from starlette.status import HTTP_200_OK

from api.circuit_breaker import CircuitException
from api.depends import get_cb_for_tasks
from core.celery import app
from core.config import logger
from core.config import settings
from services.vk.bots_creation.bots import CreateVkBotsService
from services.vk.bots_creation.phone_stock import OnlineSimPhoneStockService
from services.vk.exceptions import StopBoostException
from services.vk.exceptions import TaskFailed
from services.vk.stat_boost.vk_boost import VKBoostService
from services.vk.vk_service import VKService


async def async_get_bot_for_work():
    """Async request to db to get free bot"""
    try:
        bot = await AsyncClient(base_url=settings.BASE_DB_URL).get(
            "/get_bot_for_work/"
        )

    except (httpx.ConnectTimeout, httpx.ConnectError, Exception):
        logger.error("Can not connect to db service and get bot for work")
        raise TaskFailed
    return bot.json()


async def set_free(bot: dict):
    """Async request to db to set free bot status"""
    try:
        response = await AsyncClient(base_url=settings.BASE_DB_URL).patch(
            f"update_bot/free/?username={bot['username']}"
        )

    except (httpx.ConnectTimeout, httpx.ConnectError):
        logger.error(
            "Can not connect to db service and set free status to bot"
        )
        raise TaskFailed

    return response


async def delete_bot(username: str):
    """Async request to db to delete one bot"""
    try:
        response = await AsyncClient(base_url=settings.BASE_DB_URL).patch(
            f"/update_bot/delete/?username={username}"
        )

    except (httpx.ConnectTimeout, httpx.ConnectError):
        logger.error("Can not connect to db service and delete bot")
        raise TaskFailed

    return response


async def get_free_bots():
    """Async request to db to get bots"""
    try:
        response = await AsyncClient(base_url=settings.BASE_DB_URL).get(
            "/get_free_bots/"
        )

    except (httpx.ConnectTimeout, httpx.ConnectError):
        logger.error("Can not connect to db service and get free bots")
        raise TaskFailed

    return response


@app.task(name="boost_stat", throws=(TaskFailed, CircuitException))
def boost_stat_task(boost_link: str, boost_type: str):
    """Boost stat task"""
    phone_stock = OnlineSimPhoneStockService()
    bot_service = CreateVkBotsService(phone_stock)
    vk_service = VKService(bot_service)

    func_name = traceback.extract_stack()[1][-2]
    circuit_breaker = get_cb_for_tasks(func_name)

    with circuit_breaker:

        bot = async_to_sync(async_get_bot_for_work)()

        if bot:
            try:
                vk_service.boost_statistics(boost_link, boost_type, bot)

                response = async_to_sync(set_free)(bot)

                if response.status_code == HTTP_200_OK:
                    logger.info(f"Bot {bot['username']} is free")

            except StopBoostException:
                logger.error("Error during boost task")

                response = async_to_sync(set_free)(bot)

                if response.status_code == HTTP_200_OK:
                    logger.info(f"Bot {bot['username']} is free")

                raise TaskFailed()

        else:
            logger.info("Bots are not available now")
            raise TaskFailed()


@app.task(name="inspect_bots", throws=(TaskFailed, CircuitException))
def inspect_bots_task():
    """Inspect bots accounts."""
    func_name = traceback.extract_stack()[1][-2]
    circuit_breaker = get_cb_for_tasks(func_name)

    with circuit_breaker:
        bot = async_to_sync(async_get_bot_for_work)()

        if bot:

            try:
                VKBoostService(
                    username=bot["username"],
                    password=bot["password"],
                    inspect=True,
                )
                logger.info(f"Bot {bot['username']} is valid")

            except StopBoostException:
                response = async_to_sync(delete_bot)(bot["username"])

                if response.status_code == HTTP_200_OK:
                    logger.info(f"Bot {bot['username']} has been deleted")

            finally:
                response = async_to_sync(set_free)(bot)

                if response.status_code == HTTP_200_OK:
                    logger.info(f"Bot {bot['username']} is free")

        else:
            logger.info("Bots are not available now")
            raise TaskFailed()


@app.task(
    name="inspect_bots_at_midnight", throws=(TaskFailed, CircuitException)
)
def inspect_bots_task_at_midnight():
    """Inspect bots accounts."""
    count = 0

    func_name = traceback.extract_stack()[1][-2]
    circuit_breaker = get_cb_for_tasks(func_name)

    with circuit_breaker:

        response = async_to_sync(get_free_bots)()

        if response.status_code == HTTP_200_OK:
            bots = response.json()
            count = len(bots)

        for _ in range(count):
            bot = async_to_sync(async_get_bot_for_work)()

            if bot:

                try:
                    VKBoostService(
                        username=bot["username"],
                        password=bot["password"],
                        inspect=True,
                    )
                    logger.info(f"Bot {bot['username']} is valid")

                    response = async_to_sync(set_free)(bot)

                    if response.status_code == HTTP_200_OK:
                        logger.info(f"Bot {bot['username']} is free")

                except StopBoostException:
                    response = async_to_sync(delete_bot)(bot["username"])

                    if response.status_code == HTTP_200_OK:
                        logger.info(f"Bot {bot['username']} has been deleted")
