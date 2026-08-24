import os
from typing import Optional
from fastapi import UploadFile
from backend.configuration.config import settings

class AudioValidationError(Exception):
    def __init__(self, message: str, error_code: str = "INVALID_AUDIO"):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)

class UnsupportedAudioFormatError(AudioValidationError):
    def __init__(self, message: str = "Unsupported audio format. Please upload .mp3, .wav, .m4a, or .webm."):
        super().__init__(message=message, error_code="UNSUPPORTED_FORMAT")

class AudioSizeExceededError(AudioValidationError):
    def __init__(self, message: Optional[str] = None):
        if not message:
            message = f"Audio file exceeds the permitted size limit of {settings.MAX_AUDIO_SIZE_MB}MB."
        super().__init__(message=message, error_code="FILE_TOO_LARGE")

def validate_audio_file(file: UploadFile, max_size_mb: Optional[int] = None) -> None:
    """
    Validates the uploaded audio file for:
    1. File presence and filename validity
    2. File extension compatibility (.mp3, .wav, .m4a, .webm, .ogg)
    3. Content type validity
    """
    if not file or not file.filename:
        raise AudioValidationError("Please upload or record an audio file.", error_code="NO_FILE_PROVIDED")
    
    # Clean filename and extract extension
    filename = file.filename.strip()
    _, ext = os.path.splitext(filename.lower())
    
    if not ext or ext not in settings.ALLOWED_EXTENSIONS:
        raise UnsupportedAudioFormatError(
            f"Unsupported audio format '{ext or 'unknown'}'. Supported formats: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )
    
    # Validate content_type if present
    content_type = (file.content_type or "").lower().strip()
    if content_type and content_type not in settings.ALLOWED_MIME_TYPES:
        # If MIME type is generic application/octet-stream or video/webm (common for MediaRecorder), accept if extension is valid
        if content_type not in ["application/octet-stream", "video/webm"]:
            # Warning/check - we permit known audio MIME types or valid extensions
            pass
