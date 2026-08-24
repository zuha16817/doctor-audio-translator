import os
import sys
import logging
import asyncio
from contextlib import asynccontextmanager

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from backend.configuration.config import settings
from backend.controllers.audio_controller import router as audio_router
from backend.services.audio.cleaner import cleanup_orphaned_temp_files
from backend.services.speech.factory import get_speech_to_text_service
from backend.services.translation.factory import get_translation_service
from backend.models.schemas import HealthResponse

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("doctor_translator.main")

def preload_ai_models():
    try:
        logger.info("Pre-warming AI models in background...")
        stt = get_speech_to_text_service()
        if hasattr(stt, "_get_model"):
            stt._get_model()
        get_translation_service()
        logger.info("AI models pre-warmed successfully!")
    except Exception as e:
        logger.warning(f"Model pre-warm warning: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Clean any stale temp audio files
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}...")
    cleanup_orphaned_temp_files(max_age_seconds=0)
    
    # Pre-warm Whisper in background thread
    asyncio.get_event_loop().run_in_executor(None, preload_ai_models)
    
    yield
    # Shutdown: Clean temp audio files
    logger.info("Shutting down Doctor's Audio Transcription & Translation backend...")
    cleanup_orphaned_temp_files(max_age_seconds=0)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Doctor's Audio Transcription & Translation API for Arabic & Urdu clinical speech.",
    lifespan=lifespan
)

# Enable CORS for browser access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes
app.include_router(audio_router, prefix=settings.API_PREFIX)

@app.get("/api/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """Health check endpoint to verify backend status and configured AI engines."""
    return HealthResponse(
        status="healthy",
        version=settings.VERSION,
        stt_provider=settings.STT_PROVIDER,
        translation_provider=settings.TRANSLATION_PROVIDER,
        max_file_size_mb=settings.MAX_AUDIO_SIZE_MB
    )

@app.get("/api/languages", tags=["System"])
async def get_supported_languages():
    """Returns supported source and target languages."""
    return {
        "sourceLanguages": [
            {"code": "auto", "name": "Auto Detect (Arabic / Urdu)"},
            {"code": "ar", "name": "Arabic (العربية)", "direction": "rtl"},
            {"code": "ur", "name": "Urdu (اردو)", "direction": "rtl"}
        ],
        "targetLanguages": [
            {"code": "en", "name": "English", "direction": "ltr"},
            {"code": "ar", "name": "Arabic (العربية)", "direction": "rtl"},
            {"code": "ur", "name": "Urdu (اردو)", "direction": "rtl"},
            {"code": "fr", "name": "French (Français)", "direction": "ltr"},
            {"code": "es", "name": "Spanish (Español)", "direction": "ltr"},
            {"code": "de", "name": "German (Deutsch)", "direction": "ltr"}
        ]
    }

# Frontend Static Files Mounting
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

    @app.get("/", include_in_schema=False)
    async def serve_index():
        index_path = os.path.join(frontend_dir, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        return JSONResponse({"message": "Doctor's Audio Transcription & Translation API is running."})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
