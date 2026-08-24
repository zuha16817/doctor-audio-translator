from typing import Optional
from pydantic import BaseModel, Field

class TranscribeTranslateResponse(BaseModel):
    success: bool = True
    sourceLanguage: str = Field(..., description="Detected or specified source language code (e.g. 'ar', 'ur')")
    targetLanguage: str = Field(..., description="Target language code (e.g. 'en', 'ar', 'ur')")
    transcription: str = Field(..., description="Transcribed text in source language")
    translation: str = Field(..., description="Translated text in target language")
    summary: Optional[str] = Field(None, description="AI-generated clinical summary of the transcription")
    confidenceScore: Optional[float] = Field(None, description="Speech recognition confidence score (0-100%)")
    durationSeconds: Optional[float] = Field(None, description="Processing duration in seconds")
    detectedLanguageLabel: Optional[str] = Field(None, description="Human readable label like 'Arabic' or 'Urdu'")

class ErrorResponse(BaseModel):
    success: bool = False
    errorCode: str = Field(..., description="Standardized error code (e.g. 'TRANSCRIPTION_FAILED', 'INVALID_FILE_FORMAT')")
    message: str = Field(..., description="User-friendly error message")

class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "1.0.0"
    stt_provider: str
    translation_provider: str
    max_file_size_mb: int
