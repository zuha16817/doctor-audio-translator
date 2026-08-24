from typing import Optional
from backend.configuration.config import settings
from backend.services.speech.base import ISpeechToTextService
from backend.services.speech.whisper_service import FasterWhisperService, CloudWhisperService

_stt_instance: Optional[ISpeechToTextService] = None

def get_speech_to_text_service() -> ISpeechToTextService:
    """
    Factory method to retrieve or instantiate the configured STT service singleton.
    """
    global _stt_instance
    if _stt_instance is not None:
        return _stt_instance
        
    provider = settings.STT_PROVIDER.lower()
    
    if provider == "groq" and settings.GROQ_API_KEY:
        _stt_instance = CloudWhisperService(
            api_key=settings.GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1",
            model="whisper-large-v3"
        )
    elif provider == "openai" and settings.OPENAI_API_KEY:
        _stt_instance = CloudWhisperService(
            api_key=settings.OPENAI_API_KEY,
            model="whisper-1"
        )
    else:
        # Default: FasterWhisperService (offline, fast, accurate)
        _stt_instance = FasterWhisperService(
            model_size=settings.STT_MODEL_SIZE,
            device=settings.STT_DEVICE,
            compute_type=settings.STT_COMPUTE_TYPE
        )
        
    return _stt_instance
