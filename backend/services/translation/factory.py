from typing import Optional
from backend.configuration.config import settings
from backend.services.translation.base import ITranslationService
from backend.services.translation.translator_service import DeepTranslatorService

_translation_instance: Optional[ITranslationService] = None

def get_translation_service() -> ITranslationService:
    """
    Factory method to retrieve or instantiate the configured Translation service singleton.
    """
    global _translation_instance
    if _translation_instance is not None:
        return _translation_instance
        
    _translation_instance = DeepTranslatorService()
    return _translation_instance
