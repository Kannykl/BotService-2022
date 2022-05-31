"""Boost stat tasks module"""
from asgiref.sync import async_to_sync
from httpx import AsyncClient
from starlette.status import HTTP_200_OK

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
    bot = await AsyncClient(base_url=settings.BASE_DB_URL).get(
        "get_bot_for_work/"
    )

    return bot.json()


async def set_free(bot: dict):
    """Async request to db to set free bot status"""
    response = await AsyncClient(base_url=settings.BASE_DB_URL).patch(
        f"update_bot/free/?username={bot['username']}"
    )

    return response


async def delete_bot(username: str):
    """Async request to db to delete one bot"""
    response = await AsyncClient(base_url=settings.BASE_DB_URL).patch(
        f"/update_bot/delete/?username={username}"
    )

    return response


async def get_bots():
    """Async request to db to get bots"""
    response = await AsyncClient(base_url=settings.BASE_DB_URL).get(
        "/get_bots/"
    )

    return response


@app.task(name="boost_stat")
def boost_stat_task(boost_link: str, boost_type: str):
    """Boost stat task"""
    phone_stock = OnlineSimPhoneStockService()
    bot_service = CreateVkBotsService(phone_stock)
    vk_service = VKService(bot_service)

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


@app.task(name="inspect_bots")
def inspect_bots_task():
    """Inspect bots accounts."""
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


@app.task(name="inspect_bots_at_midnight")
def inspect_bots_task_at_midnight():
    """Inspect bots accounts."""
    count = 0

    response = async_to_sync(get_bots)()

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
