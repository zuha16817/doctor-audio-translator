from abc import ABC, abstractmethod
from typing import Optional, Tuple

class ISpeechToTextService(ABC):
    """
    Abstract Base Class for Speech-to-Text Service Providers.
    Allows easy swapping between local models (Faster-Whisper), Cloud APIs (OpenAI, Groq), or Custom models.
    """
    
    @abstractmethod
    async def transcribe(self, audio_path: str, source_language: Optional[str] = None) -> Tuple[str, str, float]:
        """
        Transcribes the audio at audio_path.
        
        Args:
            audio_path: Absolute path to the temporary audio file.
            source_language: Optional language hint (e.g., 'ar', 'ur', 'auto', None).
            
        Returns:
            Tuple[str, str, float]: (transcribed_text, detected_language_code, confidence_score)
            
        Raises:
            Exception: If speech recognition fails.
        """
        pass
