"""Service dependencies"""
from fastapi import Depends, Request, status, HTTPException
from fastapi.security import SecurityScopes
from core.config import settings
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


async def get_current_user(security_scopes: SecurityScopes, request: Request):
    """Get current user."""
    client = AsyncClient(base_url=settings.BASE_AUTH_URL)

    token = request.cookies["Token"]

    response = await client.get("get_current_user", headers={
        "Authorization": f"Bearer {token}",
        "security-scopes": security_scopes.scope_str
    })

    if response.status_code == status.HTTP_403_FORBIDDEN:
        raise HTTPException(
            status_code=response.status_code,
            detail="Not enough permissions or invalid token",
        )
    if response.status_code == status.HTTP_401_UNAUTHORIZED:
        raise HTTPException(
            status_code=response.status_code,
            detail="Could not validate credentials",
        )

    return response.json()

