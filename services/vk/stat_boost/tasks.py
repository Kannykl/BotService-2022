"""Boost stat tasks module"""

from httpx import AsyncClient
from asgiref.sync import async_to_sync
from core.celery import app
from core.config import settings, logger
from services.vk.vk_service import VKService
from services.vk.bots_creation.bots import CreateVkBotsService
from services.vk.bots_creation.phone_stock import OnlineSimPhoneStockService
from fastapi import status


async def async_get_free_bots(count: int):
    """Async request to db to get free bots."""
    free_bots = await AsyncClient(base_url=settings.BASE_DB_URL).get(f"get_free_bots/?count={count}")

    return free_bots.json()


async def set_busy(bot: dict):
    """Async request to set busy bot status"""
    response = await AsyncClient(base_url=settings.BASE_DB_URL).patch(f"update_bot/busy/?username={bot['username']}")

    return response


async def set_free(bot: dict):
    """Async request to db to set free bot status"""
    response = await AsyncClient(base_url=settings.BASE_DB_URL).patch(f"update_bot/free/?username={bot['username']}")

    return response


@app.task(name="boost_stat")
def boost_stat_task(boost_link: str, count: int, boost_type: str):
    """Boost stat task"""
    phone_stock = OnlineSimPhoneStockService()
    bot_service = CreateVkBotsService(phone_stock)
    vk_service = VKService(bot_service)

    free_bots = async_to_sync(async_get_free_bots)(count)

    if free_bots:

        for bot in free_bots:

            response = async_to_sync(set_busy)(bot)

            if response.status_code == status.HTTP_200_OK:
                logger.info(f"Bot {bot['username']} has been updated status to busy")
                vk_service.boost_statistics(boost_link, count, boost_type, free_bots)

    return free_bots


@app.task(name="free_bot")
def free_bot(results: list):
    """Set free status task."""
    for result in results:
        for bot in result:
            async_to_sync(set_free)(bot)
