"""Endpoints for work with bots"""
import httpx
from celery import group
from celery.result import AsyncResult
from fastapi import APIRouter
from fastapi import Body
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Request
from fastapi import Security
from lasier.circuit_breaker.asyncio import CircuitBreaker
from starlette.status import HTTP_200_OK
from starlette.status import HTTP_502_BAD_GATEWAY

from api.depends import get_circuit_breaker
from api.depends import get_current_user
from core.config import logger
from schemas.task import BoostTask
from schemas.task import BoostTaskIn
from schemas.task import Task
from schemas.user import User
from services.vk.bots_creation.tasks import create_bots_task
from services.vk.bots_creation.tasks import error_handler
from services.vk.bots_creation.tasks import success_handler
from services.vk.stat_boost.tasks import boost_stat_task
from services.vk.stat_boost.tasks import inspect_bots_task

router = APIRouter()


@router.post("/create_bots", response_model=Task, status_code=HTTP_200_OK)
async def run_create_bots_task(
    count: int,
    request: Request,
    circuit_breaker: CircuitBreaker = Depends(get_circuit_breaker),
    current_user: User = Security(
        get_current_user,
        scopes=[
            "admin",
        ],
    ),
):
    """Create bots in social net VK."""
    with circuit_breaker:

        tasks_group = group(create_bots_task.s() for _ in range(count))

        task_chord = (
            tasks_group | success_handler.s().on_error(error_handler.s())
        ).delay()

        task = {
            "_id": task_chord.id,
            "owner": current_user.email,
            "status": AsyncResult(task_chord.id).status,
            "count": count,
        }

        try:
            response = await request.app.db_client.post(
                "create_task/bot/", json={"task": task}
            )
            logger.info(
                f"Create task for creating bots"
                f" with request_id={request.headers['x-request-id']}"
            )

        except (httpx.ConnectTimeout, httpx.ConnectError):
            logger.error(
                f"Create task for creating bots"
                f" failed with request_id={request.headers['x-request-id']}"
            )
            raise HTTPException(
                status_code=HTTP_502_BAD_GATEWAY,
                detail="Can not connect to db service!",
            )

        if response.status_code != HTTP_200_OK:
            logger.error(
                f"Create task for creating bots"
                f" failed with request_id={request.headers['x-request-id']}"
            )
            raise HTTPException(
                status_code=response.status_code,
                detail="Create task for creating bots failed",
            )

    return Task.parse_obj(response.json())


@router.post(
    "/boost_stat",
    response_model=BoostTask,
    status_code=HTTP_200_OK,
)
async def boost_stat(
    request: Request,
    boost_info: BoostTaskIn = Body(..., embed=True),
    circuit_breaker: CircuitBreaker = Depends(get_circuit_breaker),
    current_user: User = Security(
        get_current_user,
        scopes=[
            "admin",
        ],
    ),
):
    """Boost sub to a profile or add like to the post"""
    db_client = request.app.db_client

    with circuit_breaker:

        tasks_group = group(
            boost_stat_task.signature((boost_info.link, boost_info.boost_type))
            for _ in range(boost_info.count)
        )

        task_chord = (
            tasks_group | success_handler.s().on_error(error_handler.s())
        ).delay()

        task = {
            "_id": task_chord.id,
            "owner": current_user.email,
            "status": AsyncResult(task_chord.id).status,
            "count": boost_info.count,
            "boost_type": boost_info.boost_type,
            "link": boost_info.link,
        }

        try:
            response = await db_client.post(
                "create_task/boost/", json={"task": task}
            )
            logger.info(
                f"Create task for boost stat"
                f" with request_id={request.headers['x-request-id']}"
            )

        except (httpx.ConnectTimeout, httpx.ConnectError):
            logger.error(
                f"Create task for boost stat failed"
                f" with request_id={request.headers['x-request-id']}"
            )
            raise HTTPException(
                status_code=HTTP_502_BAD_GATEWAY,
                detail="Can not connect to db service!",
            )

        if response.status_code != HTTP_200_OK:
            logger.error(
                f"Create task for boost stat failed with"
                f" request_id={request.headers['x-request-id']}"
            )
            raise HTTPException(
                status_code=response.status_code,
                detail="Create task for boost stat failed",
            )

    return BoostTask.parse_obj(response.json())


@router.post("/inspect_bots")
async def inspect_bots(
    request: Request,
    count: int,
    circuit_breaker: CircuitBreaker = Depends(get_circuit_breaker),
    current_user: User = Security(
        get_current_user,
        scopes=[
            "admin",
        ],
    ),
):
    """Check bots account"""

    with circuit_breaker:

        tasks_group = group(
            inspect_bots_task.signature() for _ in range(count)
        )

        task_chord = (
            tasks_group | success_handler.s().on_error(error_handler.s())
        ).delay()

        task = {
            "_id": task_chord.id,
            "owner": current_user.email,
            "status": AsyncResult(task_chord.id).status,
            "count": count,
        }

        try:
            response = await request.app.db_client.post(
                "create_task/bot/", json={"task": task}
            )
            logger.info(
                f"Created task for inspect bots with"
                f" request_id={request.headers['x-request-id']}"
            )

        except (httpx.ConnectTimeout, httpx.ConnectError):
            logger.error(
                f"Failed during create task for inspect bots"
                f" with request_id={request.headers['x-request-id']}"
            )
            raise HTTPException(
                status_code=HTTP_502_BAD_GATEWAY,
                detail="Can not connect to db service",
            )

        if response.status_code != HTTP_200_OK:
            logger.error(
                f"Failed during create task for inspect bots"
                f" with request_id={request.headers['x-request-id']}"
            )
            raise HTTPException(
                status_code=response.status_code,
                detail="Unsuccessful create inspect task",
            )

    return Task.parse_obj(response.json())
