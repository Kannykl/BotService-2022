from fastapi import HTTPException
from lasier.adapters.caches import RedisAdapter
from lasier.circuit_breaker.rules import MaxFailuresRule
from redis import Redis
from starlette.status import HTTP_423_LOCKED

from core.config import settings


cache = RedisAdapter(
    Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_CB_DB,
    )
)


class CircuitException(HTTPException):
    """Throws when circuit breaker is open."""

    def __init__(self):
        super().__init__(
            status_code=HTTP_423_LOCKED,
            detail="This endpoint is not working"
                   " right now, please try again later",
        )


def max_failures_rule_factory(name: str) -> MaxFailuresRule:
    """Return instance of MaxFailuresRule with configured name"""
    return MaxFailuresRule(
        max_failures=settings.CIRCUIT_BREAKER_MAX_FAILURES_COUNT,
        failure_cache_key=name,
    )
