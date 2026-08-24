import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Doctor's Audio Transcription & Translation"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    
    # Audio Upload Constraints (Section 2.2 A)
    MAX_AUDIO_SIZE_MB: int = 50
    ALLOWED_EXTENSIONS: List[str] = [".mp3", ".wav", ".m4a", ".webm", ".ogg", ".opus"]
    ALLOWED_MIME_TYPES: List[str] = [
        "audio/mpeg",
        "audio/mp3",
        "audio/wav",
        "audio/x-wav",
        "audio/wave",
        "audio/m4a",
        "audio/mp4",
        "audio/x-m4a",
        "audio/webm",
        "audio/ogg",
        "audio/opus",
        "video/webm",
        "application/octet-stream"
    ]
    
    # Storage
    TEMP_DIR: str = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "temp")
    
    # AI Providers Configuration (Section 8 & 9)
    STT_PROVIDER: str = "faster-whisper"
    STT_MODEL_SIZE: str = "small"  # tiny, base, small, medium
    STT_DEVICE: str = "cpu"  # cpu or cuda
    STT_COMPUTE_TYPE: str = "int8"
    
    # Optional Cloud API credentials
    OPENAI_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    SPEECH_API_URL: str = ""
    SPEECH_API_KEY: str = ""
    
    # Translation Engine
    TRANSLATION_PROVIDER: str = "deep-translator"
    TRANSLATION_API_URL: str = ""
    TRANSLATION_API_KEY: str = ""
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()

# Ensure temp directory exists
os.makedirs(settings.TEMP_DIR, exist_ok=True)
