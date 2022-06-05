import uuid

import uvicorn
from fastapi import FastAPI
from fastapi import Request
from httpx import AsyncClient
from starlette.middleware.cors import CORSMiddleware

from api.api_v1.api import api_router
from core.config import settings


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_PREFIX}/openapi.json",
    docs_url=f"{settings.API_PREFIX}/docs",
)

if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            str(origin) for origin in settings.BACKEND_CORS_ORIGINS
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.API_PREFIX)


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add request id"""
    request.headers.__dict__["_list"].append(
        (b"x-request-id", f"{uuid.uuid4()}".encode())
    )
    response = await call_next(request)
    return response


@app.on_event("startup")
async def start_up_db_client():
    app.db_client = AsyncClient(base_url=settings.BASE_DB_URL)


if __name__ == "__main__":
    uvicorn.run("main:app", port=8001, host="0.0.0.0", reload=True)
