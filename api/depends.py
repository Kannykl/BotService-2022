"""Service dependencies"""
import httpx
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Request
from fastapi.security import SecurityScopes
from httpx import AsyncClient
from lasier.circuit_breaker.sync import CircuitBreaker
from starlette.status import HTTP_401_UNAUTHORIZED
from starlette.status import HTTP_403_FORBIDDEN
from starlette.status import HTTP_502_BAD_GATEWAY

from api.circuit_breaker import cache
from api.circuit_breaker import CircuitException
from api.circuit_breaker import max_failures_rule_factory
from core.config import settings
from services.vk.bots_creation.bots import CreateVkBotsService
from services.vk.bots_creation.phone_stock import OnlineSimPhoneStockService
from services.vk.bots_creation.phone_stock import PhoneStockService
from services.vk.exceptions import StopBoostException
from services.vk.exceptions import StopCreatingBotsException
from services.vk.exceptions import TaskFailed
from services.vk.vk_service import VKService


def get_phone_stock():
    """Get phone stock instance."""
    phone_stock = OnlineSimPhoneStockService()
    return phone_stock


def get_vk_bot_service(
    phone_stock: PhoneStockService = Depends(get_phone_stock),
):
    """Get vk bot service."""
    bot_service = CreateVkBotsService(phone_stock)
    return bot_service


def get_vk_service(
    bot_service: CreateVkBotsService = Depends(get_vk_bot_service),
):
    """Get vk service."""
    vk_service = VKService(bot_service)
    return vk_service


async def get_current_user(security_scopes: SecurityScopes, request: Request):
    """Get current user."""
    client = AsyncClient(base_url=settings.BASE_AUTH_URL)

    token = request.cookies["Token"]
    try:
        response = await client.get(
            "get_current_user",
            headers={
                "Authorization": f"Bearer {token}",
                "security-scopes": security_scopes.scope_str,
            },
        )
    except (httpx.ConnectTimeout, httpx.ConnectError):
        raise HTTPException(
            status_code=HTTP_502_BAD_GATEWAY,
            detail="Can not connect to db auth service, try again later.",
        )

    if response.status_code == HTTP_403_FORBIDDEN:
        raise HTTPException(
            status_code=response.status_code,
            detail="Not enough permissions or invalid token",
        )
    if response.status_code == HTTP_401_UNAUTHORIZED:
        raise HTTPException(
            status_code=response.status_code,
            detail="Could not validate credentials",
        )

    return response.json()


def get_circuit_breaker(request: Request) -> CircuitBreaker:
    """Get circuit breaker."""
    rule_name: str = request.scope.get("path").split("/")[-1]

    rule = max_failures_rule_factory(name=rule_name)

    return CircuitBreaker(
        cache=cache,
        failure_exception=CircuitException,
        catch_exceptions=(HTTPException,),
        failure_timeout=30,
        rule=rule,
    )


def get_cb_for_tasks(rule_name: str) -> CircuitBreaker:
    """Get circuit breaker for tasks."""

    rule = max_failures_rule_factory(name=rule_name)

    return CircuitBreaker(
        cache=cache,
        failure_exception=CircuitException,
        catch_exceptions=(
            TaskFailed,
            StopBoostException,
            StopCreatingBotsException,
        ),
        failure_timeout=60,
        rule=rule,
    )
