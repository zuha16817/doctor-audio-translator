import re
import asyncio
import logging
import httpx
from backend.services.translation.base import ITranslationService
from backend.configuration.config import settings

logger = logging.getLogger("doctor_translator.translation")

class DeepTranslatorService(ITranslationService):
    """
    High-Reliability Multi-Engine Translation Service.
    Engine Chain:
    1. Google Neural Endpoint (dict-chrome-ex API) - Sub-200ms, accurate, no rate-limits
    2. MyMemory Direct API
    3. Deep-Translator Google Engine
    4. Deep-Translator MyMemory Engine
    """
    
    # 2-letter ISO codes map
    LANGUAGE_MAP_ISO = {
        "ar": "ar",
        "ur": "ur",
        "en": "en",
        "es": "es",
        "fr": "fr",
        "de": "de",
        "tr": "tr",
        "arabic": "ar",
        "urdu": "ur",
        "english": "en",
        "french": "fr",
        "spanish": "es",
        "german": "de",
        "auto": "auto"
    }

    def _normalize_iso(self, lang: str) -> str:
        clean = (lang or "").lower().strip()
        return self.LANGUAGE_MAP_ISO.get(clean, clean if clean else "auto")

    def _is_mostly_english(self, text: str) -> bool:
        """Check if text is primarily English/Latin characters."""
        if not text:
            return False
        letters = re.findall(r'[a-zA-Z]', text)
        arabic_urdu = re.findall(r'[\u0600-\u06FF\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF]', text)
        return len(letters) > len(arabic_urdu) and len(letters) > 4

    def _clean_text(self, text: str) -> str:
        """Clean leading punctuation anomalies."""
        cleaned = text.strip()
        if cleaned.startswith("?") and len(cleaned) > 1 and not cleaned.endswith("?"):
            cleaned = cleaned.lstrip("? \t")
        return cleaned

    def _sync_translate(self, text: str, source_language: str, target_language: str) -> str:
        cleaned_text = self._clean_text(text)
        src_iso = self._normalize_iso(source_language)
        tgt_iso = self._normalize_iso(target_language)
        
        # 1. Identity Check
        if src_iso == tgt_iso and src_iso != "auto":
            return cleaned_text
            
        # 2. If target is English and text is already predominantly in English
        if tgt_iso == "en" and self._is_mostly_english(cleaned_text):
            logger.info("Transcribed text is already primarily English; returning text directly.")
            return cleaned_text

        effective_src = src_iso if src_iso != "auto" else "auto"

        # Strategy 1: Google Neural Endpoint (dict-chrome-ex) - Fastest & Highest Uptime
        try:
            url = "https://clients5.google.com/translate_a/t"
            params = {
                "client": "dict-chrome-ex",
                "sl": effective_src,
                "tl": tgt_iso,
                "q": cleaned_text
            }
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            with httpx.Client(timeout=6.0) as client:
                resp = client.get(url, params=params, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    if isinstance(data, list) and len(data) > 0 and isinstance(data[0], str):
                        translated_text = " ".join(data).strip()
                        if translated_text and translated_text != cleaned_text:
                            logger.info(f"Google dict-chrome-ex translation ({effective_src} -> {tgt_iso}): {len(translated_text)} chars")
                            return translated_text
        except Exception as e:
            logger.warning(f"Google dict-chrome-ex attempt error: {e}")

        # Strategy 2: MyMemory Direct API
        try:
            url = "https://api.mymemory.translated.net/get"
            langpair = f"{effective_src if effective_src != 'auto' else 'ur'}|{tgt_iso}"
            params = {"q": cleaned_text, "langpair": langpair}
            with httpx.Client(timeout=6.0) as client:
                resp = client.get(url, params=params)
                if resp.status_code == 200:
                    res_data = resp.json().get("responseData", {})
                    translated_text = res_data.get("translatedText", "")
                    if translated_text and not translated_text.startswith("MYMEMORY WARNING") and translated_text != cleaned_text:
                        logger.info(f"MyMemory API translation ({langpair}): {len(translated_text)} chars")
                        return translated_text
        except Exception as e:
            logger.warning(f"MyMemory API attempt error: {e}")

        # Strategy 3: Deep-Translator Google Engine
        try:
            from deep_translator import GoogleTranslator
            translator = GoogleTranslator(source=effective_src, target=tgt_iso)
            res = translator.translate(cleaned_text)
            if res and res != cleaned_text:
                logger.info(f"DeepTranslator Google ({effective_src} -> {tgt_iso}): {len(res)} chars")
                return res
        except Exception as e:
            logger.warning(f"DeepTranslator Google attempt error: {e}")

        # Strategy 4: Deep-Translator MyMemory Engine
        try:
            from deep_translator import MyMemoryTranslator
            src_full = "arabic" if effective_src == "ar" else "urdu" if effective_src == "ur" else "auto"
            tgt_full = "english" if tgt_iso == "en" else "arabic" if tgt_iso == "ar" else "urdu"
            translator = MyMemoryTranslator(source=src_full, target=tgt_full)
            res = translator.translate(cleaned_text)
            if res and not res.startswith("MYMEMORY WARNING"):
                logger.info(f"DeepTranslator MyMemory ({src_full} -> {tgt_full}): {len(res)} chars")
                return res
        except Exception as e:
            logger.warning(f"DeepTranslator MyMemory attempt error: {e}")

        logger.error(f"All translation strategies failed for text: {cleaned_text}")
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
            logger.error(f"Translation pipeline error: {e}", exc_info=True)
            return self._clean_text(text)
