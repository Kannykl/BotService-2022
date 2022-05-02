"""Router aggregator"""

from fastapi import APIRouter
from api.api_v1.endpoints import bots

api_router = APIRouter()

api_router.include_router(bots.router, prefix="", tags=["bot"])
