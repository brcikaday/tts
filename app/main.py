import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api_routes.admin import admin_router
from api_routes.ai import ai_router
from api_routes.auth import auth_router
from api_routes.documents import documents_router
from api_routes.library import library_router
from api_routes.scrape import scrape_router
from api_routes.tts import tts_router
from api_routes.upload import upload_router
from core.config import settings
from core.logging_setup import access_logger, current_user_email, setup_logging
from core.security import decode_access_token
from db.base import Base, engine
from models.conversion import ConversionHistory
from models.user import User
from services.ai_service import load_groq
from services.detection_service import load_model

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    try:
        await load_model()
    except Exception as exc:
        logger.warning("Model startup failed; continuing without pretrained detection model: %s", exc)
    try:
        load_groq()
    except Exception as exc:
        logger.warning("Groq startup failed; AI endpoints will fail only when used: %s", exc)
    yield

app = FastAPI(title="TTS API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Adjust this to your needs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def bind_user_to_logs(request: Request, call_next):
    email = None
    auth_header = request.headers.get("authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        payload = decode_access_token(auth_header.split(" ", 1)[1])
        if payload:
            email = payload.get("sub")

    token = current_user_email.set(email)
    try:
        response = await call_next(request)
        access_logger.info(f"{request.method} {request.url.path} -> {response.status_code}")
        return response
    finally:
        current_user_email.reset(token)


app.include_router(auth_router)
app.include_router(upload_router)
app.include_router(library_router)
app.include_router(ai_router)
app.include_router(tts_router)
app.include_router(scrape_router)
app.include_router(admin_router)
app.include_router(documents_router)
app.mount("/audio", StaticFiles(directory=settings.AUDIO_STORAGE_PATH), name="audio")

