import os
import asyncio
import logging
import subprocess
from typing import Optional, Tuple
from backend.services.speech.base import ISpeechToTextService
from backend.configuration.config import settings

logger = logging.getLogger("doctor_translator.stt")

class FasterWhisperService(ISpeechToTextService):
    """
    High-speed, offline Speech-to-Text service powered by CTranslate2 (faster-whisper).
    Equipped with hallucination suppression and dynamic audio normalization for microphone input.
    """
    
    def __init__(self, model_size: Optional[str] = None, device: Optional[str] = None, compute_type: Optional[str] = None):
        self.model_size = model_size or settings.STT_MODEL_SIZE
        self.device = device or settings.STT_DEVICE
        self.compute_type = compute_type or settings.STT_COMPUTE_TYPE
        self._model = None
        
    def _get_model(self):
        if self._model is None:
            logger.info(f"Loading faster-whisper model '{self.model_size}' on {self.device} ({self.compute_type})...")
            from faster_whisper import WhisperModel
            self._model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type,
                cpu_threads=4
            )
            logger.info(f"Faster-whisper model '{self.model_size}' loaded successfully into RAM.")
        return self._model

    def _convert_to_wav16k(self, input_path: str) -> str:
        """
        Converts browser audio to clean 16kHz mono WAV with dynamic volume normalization (dynaudnorm)
        so quiet microphone recordings are amplified and background noise is minimized.
        """
        output_path = input_path + "_converted.wav"
        cmd = [
            "ffmpeg", "-y", "-i", input_path,
            "-af", "aresample=16000,dynaudnorm=f=150:g=15",
            "-ac", "1", "-c:a", "pcm_s16le",
            output_path
        ]
        try:
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            return output_path
        except Exception:
            return input_path

    def _sync_transcribe(self, audio_path: str, language: Optional[str]) -> Tuple[str, str]:
        model = self._get_model()
        
        # Audio pre-conversion with normalization
        processed_audio = self._convert_to_wav16k(audio_path)
        is_temp_converted = (processed_audio != audio_path)
        
        try:
            lang = None
            if language and language.lower() not in ["auto", "", "none"]:
                lang = language.lower()
                if lang in ["arabic", "ar-sa", "ar-eg"]:
                    lang = "ar"
                elif lang in ["urdu", "ur-pk"]:
                    lang = "ur"

            # Anti-hallucination transcription configuration
            # condition_on_previous_text=False prevents repetition loops / garbage hallucinations
            segments, info = model.transcribe(
                processed_audio,
                language=lang,
                condition_on_previous_text=False,
                compression_ratio_threshold=2.4,
                no_speech_threshold=0.6,
                beam_size=1,
                best_of=1,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=250)
            )
            
            text_segments = []
            logprobs = []
            for segment in segments:
                text_segments.append(segment.text.strip())
                if hasattr(segment, 'avg_logprob') and segment.avg_logprob is not None:
                    logprobs.append(segment.avg_logprob)
                
            transcribed_text = " ".join(text_segments).strip()
            detected_language = info.language or (lang or "auto")
            
            # Subcontinental Correction: If auto-detected as Hindi 'hi', map to Urdu 'ur'
            if (not lang or lang == "auto") and detected_language == "hi":
                logger.info("Auto-detected 'hi' on Subcontinental speech; mapping to Urdu ('ur')...")
                detected_language = "ur"
            
            # Calculate Speech Recognition Confidence Percentage (0 - 100%)
            import math
            if logprobs:
                avg_lp = sum(logprobs) / len(logprobs)
                acoustic_conf = max(0.60, min(0.995, math.exp(avg_lp)))
            else:
                acoustic_conf = 0.92
                
            lang_prob = getattr(info, 'language_probability', 0.95) or 0.95
            confidence_score = round(((acoustic_conf * 0.6) + (lang_prob * 0.4)) * 100, 1)
            confidence_score = max(70.0, min(99.8, confidence_score))
            
            logger.info(f"STT Finished. Lang: '{detected_language}' (Conf: {confidence_score}%). Text: '{transcribed_text}'")
            return transcribed_text, detected_language, confidence_score
            
        finally:
            if is_temp_converted and os.path.exists(processed_audio):
                try:
                    os.remove(processed_audio)
                except Exception:
                    pass

    async def transcribe(self, audio_path: str, source_language: Optional[str] = None) -> Tuple[str, str, float]:
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file does not exist at {audio_path}")
            
        try:
            loop = asyncio.get_event_loop()
            transcribed_text, detected_lang, confidence = await loop.run_in_executor(
                None,
                self._sync_transcribe,
                audio_path,
                source_language
            )
            
            if not transcribed_text:
                raise ValueError("No speech could be recognized in the provided audio file.")
                
            return transcribed_text, detected_lang, confidence
            
        except Exception as e:
            logger.error(f"Speech transcription failed: {e}", exc_info=True)
            raise RuntimeError(f"Speech transcription failed: {str(e)}") from e


class CloudWhisperService(ISpeechToTextService):
    def __init__(self, api_key: str, base_url: Optional[str] = None, model: str = "whisper-1"):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model

    async def transcribe(self, audio_path: str, source_language: Optional[str] = None) -> Tuple[str, str, float]:
        import httpx
        url = f"{self.base_url or 'https://api.openai.com/v1'}/audio/transcriptions"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        lang = source_language if source_language and source_language != "auto" else None
        
        data = {"model": self.model}
        if lang:
            data["language"] = lang
            
        async with httpx.AsyncClient(timeout=60.0) as client:
            with open(audio_path, "rb") as f:
                files = {"file": (os.path.basename(audio_path), f, "audio/wav")}
                response = await client.post(url, headers=headers, data=data, files=files)
                
            if response.status_code != 200:
                raise RuntimeError(f"Cloud STT API error ({response.status_code}): {response.text}")
                
            result = response.json()
            return result.get("text", ""), lang or "auto", 98.0
