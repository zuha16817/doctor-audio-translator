from abc import ABC, abstractmethod

class ITranslationService(ABC):
    """
    Abstract Base Class for Translation Service Providers.
    Allows seamlessly swapping translation backends (Google, DeepL, OpenAI, Local models).
    """
    
    @abstractmethod
    async def translate(self, text: str, source_language: str, target_language: str) -> str:
        """
        Translates text from source_language to target_language.
        
        Args:
            text: Transcribed text string.
            source_language: Source language code (e.g., 'ar', 'ur', 'auto').
            target_language: Target language code (e.g., 'en', 'ar', 'ur', 'fr', 'es').
            
        Returns:
            str: Translated text string.
            
        Raises:
            Exception: If translation fails.
        """
        pass
