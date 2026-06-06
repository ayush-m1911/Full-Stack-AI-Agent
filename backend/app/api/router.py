
from fastapi import APIRouter
from app.api.routes import health, chat, upload, pdf, image, audio, analyze

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(health.router)
api_router.include_router(chat.router)
api_router.include_router(upload.router)
api_router.include_router(pdf.router)
api_router.include_router(image.router)
api_router.include_router(audio.router)
api_router.include_router(analyze.router)
