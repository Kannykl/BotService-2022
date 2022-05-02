"""Service dependencies"""

from fastapi import Depends
from services.vk.vk_service import VKService
from services.vk.bots_creation.bots import CreateVkBotsService
from services.vk.bots_creation.phone_stock import OnlineSimPhoneStockService, PhoneStockService
from httpx import AsyncClient


def get_phone_stock():
    """Get phone stock instance."""
    phone_stock = OnlineSimPhoneStockService()
    return phone_stock


def get_vk_bot_service(phone_stock: PhoneStockService = Depends(get_phone_stock)):
    """Get vk bot service."""
    bot_service = CreateVkBotsService(phone_stock)
    return bot_service


def get_vk_service(bot_service: CreateVkBotsService = Depends(get_vk_bot_service)):
    """Get vk service."""
    vk_service = VKService(bot_service)
    return vk_service


async def get_current_user():
    """Get current user."""
    client = AsyncClient(base_url="http://localhost:8003/auth/")

    response = await client.get("get_current_user/")
    user = response.json()

    return user
