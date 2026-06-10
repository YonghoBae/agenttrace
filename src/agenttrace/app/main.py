from __future__ import annotations

from fastapi import FastAPI

from agenttrace.app.routers.health import router as health_router
from agenttrace.app.routers.summaries import router as summaries_router
from agenttrace.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.service_name)
    app.include_router(health_router)
    app.include_router(summaries_router, prefix="/v1")
    return app


app = create_app()
