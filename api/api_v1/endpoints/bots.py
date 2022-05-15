"""Endpoints for work with bots"""
from celery import group, chord
from celery.result import AsyncResult
from fastapi import APIRouter, status, Request, Body
from schemas.task import Task, BoostTask, BoostTaskIn
from services.vk.stat_boost.tasks import boost_stat_task, free_bot

from services.vk.bots_creation.tasks import (
    create_bots_task,
    create_bots_listener,
    update_task_status,
)

router = APIRouter()


@router.post(
    "/create_bots/{count}", response_model=Task, status_code=status.HTTP_200_OK
)
async def run_create_bots_task(count: int, request: Request):
    """Create bots in social net VK."""

    created_tasks = group(
        create_bots_task.signature(link=create_bots_listener.s()) for _ in range(count)
    )()

    created_tasks.save()

    task = {
        "_id": created_tasks.id,
        "owner": "user_stub@mail.ru",
        "status": AsyncResult(created_tasks.id).status,
        "count": count,
    }

    response = await request.app.db_client.post("create_task/bot/", json={"task": task})

    update_task_status.delay(created_tasks.id)

    return Task.parse_obj(response.json())


@router.post(
    "/boost_stat/",
    response_model=BoostTask,
    status_code=status.HTTP_200_OK,
)
async def boost_stat(
    request: Request,
    boost_info: BoostTaskIn = Body(..., embed=True),
):
    """Boost sub to a profile or add like to the post"""
    db_client = request.app.db_client

    created_tasks = chord(
        (
            boost_stat_task.signature((boost_info.link, 1, boost_info.boost_type))
            for _ in range(boost_info.count)
        ),
        free_bot.s(),
    )()

    task = {
        "_id": created_tasks.id,
        "owner": "user_stub@mail.ru",
        "status": AsyncResult(created_tasks.id).status,
        "count": boost_info.count,
        "boost_type": boost_info.boost_type,
        "link": boost_info.link,
    }

    response = await db_client.post("create_task/boost/", json={"task": task})
    update_task_status.delay(created_tasks.id)

    return BoostTask.parse_obj(response.json())
