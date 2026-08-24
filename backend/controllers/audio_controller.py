import time
import logging
from typing import Optional
from fastapi import APIRouter, File, Form, UploadFile, status
from fastapi.responses import JSONResponse

from backend.configuration.config import settings
from backend.models.schemas import TranscribeTranslateResponse, ErrorResponse, HealthResponse
from backend.services.audio.validator import (
    AudioValidationError,
    UnsupportedAudioFormatError,
    AudioSizeExceededError
)
from backend.services.audio.cleaner import temporary_audio_file
from backend.services.speech.factory import get_speech_to_text_service
from backend.services.translation.factory import get_translation_service
from backend.services.speech.summarizer import generate_clinical_summary

logger = logging.getLogger("doctor_translator.controller")

router = APIRouter(prefix="/audio", tags=["Audio Transcription & Translation"])

LANGUAGE_LABELS = {
    "ar": "Arabic",
    "ur": "Urdu",
    "en": "English",
    "fr": "French",
    "es": "Spanish",
    "de": "German",
    "tr": "Turkish"
}

@router.post(
    "/transcribe-translate",
    response_model=TranscribeTranslateResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Validation or Format Error"},
        500: {"model": ErrorResponse, "description": "Processing or AI Service Error"}
    }
)
async def transcribe_and_translate(
    audioFile: UploadFile = File(..., description="Audio file in .mp3, .wav, .m4a, or .webm format"),
    sourceLanguage: Optional[str] = Form("auto", description="Source language ('ar', 'ur', or 'auto')"),
    targetLanguage: str = Form("en", description="Target language code ('en', 'ar', 'ur', etc.)")
):
    """
    Main Doctor's Transcription & Translation workflow:
    1. Validates audio format & file size.
    2. Streams audio to safe ephemeral storage.
    3. Performs Speech-to-Text via ISpeechToTextService (with confidence scoring).
    4. Performs text Translation via ITranslationService.
    5. Generates AI-assisted clinical summary of transcription.
    6. Deletes temporary audio file immediately.
    7. Returns structured response with RTL/LTR language labels, confidence, and summary.
    """
    start_time = time.time()
    
    # 1. Parameter normalization
    src_lang = (sourceLanguage or "auto").strip().lower()
    tgt_lang = (targetLanguage or "en").strip().lower()
    
    if not audioFile or not audioFile.filename:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=ErrorResponse(
                success=False,
                errorCode="NO_FILE_PROVIDED",
                message="Please upload or record an audio file."
            ).model_dump()
        )

    try:
        # 2. Ephemeral Storage Context Manager (Ensures cleanup on any error)
        async with temporary_audio_file(audioFile) as temp_audio_path:
            stt_service = get_speech_to_text_service()
            translation_service = get_translation_service()
            
            # 3. Speech-to-Text transcription with Confidence Score
            try:
                transcription, detected_lang, confidence_score = await stt_service.transcribe(
                    temp_audio_path,
                    source_language=src_lang
                )
            except Exception as e:
                logger.error(f"STT execution error: {e}")
                return JSONResponse(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    content=ErrorResponse(
                        success=False,
                        errorCode="TRANSCRIPTION_FAILED",
                        message="Unable to transcribe the supplied audio. Please verify speech clarity."
                    ).model_dump()
                )

            if not transcription or not transcription.strip():
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content=ErrorResponse(
                        success=False,
                        errorCode="EMPTY_TRANSCRIPTION",
                        message="No recognizable speech was detected in the audio file."
                    ).model_dump()
                )

            # Determine final source language code
            effective_src = detected_lang if src_lang == "auto" else src_lang
            
            # 4. Text Translation
            try:
                translation = await translation_service.translate(
                    transcription,
                    source_language=effective_src,
                    target_language=tgt_lang
                )
            except Exception as e:
                logger.error(f"Translation execution error: {e}")
                translation = transcription

            # 5. AI-Assisted Clinical Summary Generation (Phase 2 Enhancement)
            clinical_summary = generate_clinical_summary(transcription, translation, effective_src)

            elapsed = round(time.time() - start_time, 2)
            detected_label = LANGUAGE_LABELS.get(effective_src, effective_src.upper())
            
            logger.info(f"Successfully processed audio in {elapsed}s: Src={effective_src} ({confidence_score}%), Tgt={tgt_lang}")
            
            return TranscribeTranslateResponse(
                success=True,
                sourceLanguage=effective_src,
                targetLanguage=tgt_lang,
                transcription=transcription,
                translation=translation,
                summary=clinical_summary,
                confidenceScore=confidence_score,
                durationSeconds=elapsed,
                detectedLanguageLabel=detected_label
            )

    except UnsupportedAudioFormatError as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=ErrorResponse(success=False, errorCode=e.error_code, message=e.message).model_dump()
        )
    except AudioSizeExceededError as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=ErrorResponse(success=False, errorCode=e.error_code, message=e.message).model_dump()
        )
    except AudioValidationError as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=ErrorResponse(success=False, errorCode=e.error_code, message=e.message).model_dump()
        )
    except Exception as e:
        logger.error(f"Unhandled error in audio workflow: {e}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                success=False,
                errorCode="INTERNAL_ERROR",
                message="An unexpected error occurred while processing the audio."
            ).model_dump()
        )
