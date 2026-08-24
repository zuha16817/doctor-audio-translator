import os
import uuid
import time
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import UploadFile

from backend.configuration.config import settings
from backend.services.audio.validator import AudioSizeExceededError, validate_audio_file

logger = logging.getLogger("doctor_translator.audio_cleaner")

CHUNK_SIZE = 1024 * 1024  # 1 MB chunk

@asynccontextmanager
async def temporary_audio_file(file: UploadFile) -> AsyncGenerator[str, None]:
    """
    Saves an uploaded audio file to a randomized temporary path,
    streams the content with real-time size limit enforcement,
    yields the temporary file path, and guarantees deletion upon exit (even on exception).
    """
    # 1. First validate headers/extension
    validate_audio_file(file)
    
    # 2. Extract clean extension
    _, ext = os.path.splitext(file.filename or "")
    if not ext:
        ext = ".wav"
    
    # 3. Create randomized temporary filename
    temp_filename = f"audio_{uuid.uuid4().hex}{ext.lower()}"
    temp_filepath = os.path.join(settings.TEMP_DIR, temp_filename)
    
    max_bytes = settings.MAX_AUDIO_SIZE_MB * 1024 * 1024
    total_bytes = 0
    
    try:
        # Stream file to disk while enforcing max size limit
        with open(temp_filepath, "wb") as buffer:
            while True:
                chunk = await file.read(CHUNK_SIZE)
                if not chunk:
                    break
                total_bytes += len(chunk)
                if total_bytes > max_bytes:
                    raise AudioSizeExceededError(
                        f"Audio file size exceeds the permitted limit of {settings.MAX_AUDIO_SIZE_MB}MB."
                    )
                buffer.write(chunk)
                
        if total_bytes == 0:
            raise AudioSizeExceededError("The uploaded audio file is empty (0 bytes).")
            
        logger.info(f"Temporarily saved audio file ({total_bytes} bytes) to {temp_filepath}")
        yield temp_filepath
        
    finally:
        # Guarantees deletion even if transcription or translation fails
        if os.path.exists(temp_filepath):
            try:
                os.remove(temp_filepath)
                logger.info(f"Cleaned up temporary audio file: {temp_filepath}")
            except Exception as e:
                logger.error(f"Failed to delete temporary audio file {temp_filepath}: {e}")

def cleanup_orphaned_temp_files(max_age_seconds: int = 3600):
    """
    Scans the temporary directory and deletes any orphaned audio files older than max_age_seconds.
    """
    if not os.path.exists(settings.TEMP_DIR):
        return
    now = time.time()
    for filename in os.listdir(settings.TEMP_DIR):
        if filename.startswith("audio_"):
            filepath = os.path.join(settings.TEMP_DIR, filename)
            try:
                if os.path.isfile(filepath):
                    file_age = now - os.path.getmtime(filepath)
                    if file_age > max_age_seconds:
                        os.remove(filepath)
                        logger.info(f"Cleaned up orphaned file: {filepath}")
            except Exception as e:
                logger.warning(f"Could not remove orphaned file {filepath}: {e}")
