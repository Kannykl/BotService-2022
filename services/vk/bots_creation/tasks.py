from fastapi import Depends
from core.celery import app
from api.depends import get_vk_service
from services.vk.vk_service import VKService


@app.task(name="create_bots")
async def create_bots_task(count: int, vk_service: VKService = Depends(get_vk_service)):
    """Create bots task."""
    bots = await vk_service.create_bots(count)

    return bots
