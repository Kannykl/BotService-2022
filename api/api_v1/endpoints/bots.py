"""Endpoints for work with bots"""

from fastapi import APIRouter, status, Depends, Request
from api.depends import get_vk_service
from schemas.task import Task
from services.vk.vk_service import VKService
from core.config import logger
from services.vk.bots_creation.tasks import create_bots_task
from core.celery import Status


router = APIRouter()


@router.post(
    "/create_bots/{count}",
    response_model=Task,
    status_code=status.HTTP_200_OK
)
async def run_create_bots_task(count: int, request: Request):
    """Create one bot in social net VK."""
    db_client = request.app.db_client

    created_task = create_bots_task.delay(count)

    task = Task(
        _id=created_task.id,
        owner="stub_user",
        status=Status.PENDING
    )

    created_bots = []

    for bot in created_task.result:
        response = await db_client.post(f"create_bot/", json={
            "bot": {
                "username": f"+7{bot[0]}",
                "password": bot[1]
            }})

        logger.info(f"Created new bot {bot[0]}")

        created_bots.append(response.json())

    return created_bots


@router.post(
    "/boost_stat/{boot_type}/{link}/{count}",
    response_model=Task,
    status_code=status.HTTP_200_OK
)
async def boost_stat(
        boost_type: str,
        link: str,
        count: int,
        request: Request,
        vk_service: VKService = Depends(get_vk_service)
):
    db_client = request.app.db_client
    free_bots = await db_client.get(f"/db/get_free_bots/?count={count}")

    for bot in free_bots:
        await db_client.patch(f"/db/update_bot/busy/?username={bot['username']}")

        logger.info(f"Bot {bot['username']} has been updated status to busy")

    await vk_service.boost_statistics(link, count, boost_type, free_bots)
