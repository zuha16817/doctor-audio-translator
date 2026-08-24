import re
import asyncio
import logging
from backend.services.translation.base import ITranslationService
from backend.configuration.config import settings

logger = logging.getLogger("doctor_translator.translation")

class DeepTranslatorService(ITranslationService):
    """
    Ultra-Resilient Multi-Engine Translation Service.
    Features:
    - Multi-provider fallback (MyMemory, GoogleTranslator, Auto-detect Google).
    - Intelligent language code normalization.
    - Graceful fallback to original text if translation service has temporary network limits.
    """
    
    LANGUAGE_MAP = {
        "ar": "arabic",
        "ur": "urdu",
        "en": "english",
        "es": "spanish",
        "fr": "french",
        "de": "german",
        "tr": "turkish",
        "auto": "auto"
    }

    def _normalize_lang(self, lang: str) -> str:
        clean = (lang or "").lower().strip()
        return self.LANGUAGE_MAP.get(clean, clean if clean else "auto")

    def _is_mostly_english(self, text: str) -> bool:
        """Check if text is primarily English/Latin characters."""
        if not text:
            return False
        letters = re.findall(r'[a-zA-Z]', text)
        arabic_urdu = re.findall(r'[\u0600-\u06FF\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF]', text)
        return len(letters) > len(arabic_urdu)

    def _clean_text(self, text: str) -> str:
        """Clean leading punctuation anomalies."""
        cleaned = text.strip()
        # Clean weird leading punctuation like '?beet!' -> 'beet!'
        if cleaned.startswith("?") and len(cleaned) > 1 and not cleaned.endswith("?"):
            cleaned = cleaned.lstrip("? \t")
        return cleaned

    def _sync_translate(self, text: str, source_language: str, target_language: str) -> str:
        cleaned_text = self._clean_text(text)
        src = self._normalize_lang(source_language)
        tgt = self._normalize_lang(target_language)
        
        # 1. Identity Check
        if src == tgt and src != "auto":
            return cleaned_text
            
        # 2. If target is English and text is already in English/Latin
        if tgt == "english" and self._is_mostly_english(cleaned_text):
            logger.info("Transcribed text is already primarily in English; returning cleaned text.")
            return cleaned_text

        # 3. Strategy 1: MyMemoryTranslator
        try:
            from deep_translator import MyMemoryTranslator
            source_p = src if src != "auto" else "arabic"
            translator = MyMemoryTranslator(source=source_p, target=tgt)
            res = translator.translate(cleaned_text)
            if res and not res.startswith("MYMEMORY WARNING"):
                logger.info(f"MyMemory translation ({source_p} -> {tgt}): {len(res)} chars")
                return res
        except Exception as e:
            logger.warning(f"MyMemory translation attempt error: {e}")

        # 4. Strategy 2: GoogleTranslator (with explicit source)
        try:
            from deep_translator import GoogleTranslator
            source_p = src if src != "auto" else "auto"
            translator = GoogleTranslator(source=source_p, target=tgt)
            res = translator.translate(cleaned_text)
            if res:
                logger.info(f"GoogleTranslator ({source_p} -> {tgt}): {len(res)} chars")
                return res
        except Exception as e:
            logger.warning(f"GoogleTranslator explicit source error: {e}")

        # 5. Strategy 3: GoogleTranslator (with auto source)
        try:
            from deep_translator import GoogleTranslator
            translator = GoogleTranslator(source="auto", target=tgt)
            res = translator.translate(cleaned_text)
            if res:
                logger.info(f"GoogleTranslator auto-detect ({tgt}): {len(res)} chars")
                return res
        except Exception as e:
            logger.warning(f"GoogleTranslator auto-detect error: {e}")

        # 6. Graceful Degradation Fallback: Return original text rather than breaking UX
        logger.warning(f"All translation engines exhausted. Returning original transcription for: {cleaned_text}")
        return cleaned_text

    async def translate(self, text: str, source_language: str, target_language: str) -> str:
        if not text or not text.strip():
            return ""
            
        try:
            loop = asyncio.get_event_loop()
            translated = await loop.run_in_executor(
                None,
                self._sync_translate,
                text,
                source_language,
                target_language
            )
            return translated
        except Exception as e:
            logger.error(f"Unexpected translation pipeline error: {e}", exc_info=True)
            return self._clean_text(text)
