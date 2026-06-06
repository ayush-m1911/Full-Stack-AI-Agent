"""FastAPI application entry point."""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.core.config import settings
from app.core.cors import add_cors_middleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup / shutdown lifecycle."""
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    print(f"[OK] {settings.APP_NAME} v{settings.APP_VERSION} started -- upload dir: {settings.UPLOAD_DIR}")
    yield
    print("[STOP] Shutting down...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Production-ready AI Agent API scaffold. Plug in your LLM / agent logic in `services/agent_service.py`.",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


add_cors_middleware(app)


app.include_router(api_router)


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "docs": "/docs",
        "health": "/api/v1/health",
    }
