import io
import pytest
from fastapi import UploadFile
from backend.services.audio.validator import (
    validate_audio_file,
    AudioValidationError,
    UnsupportedAudioFormatError,
    AudioSizeExceededError
)

def test_validate_valid_wav_file():
    file = UploadFile(filename="test.wav", file=io.BytesIO(b"RIFF....WAVE"), headers={"content-type": "audio/wav"})
    # Should not raise
    validate_audio_file(file)

def test_validate_valid_mp3_file():
    file = UploadFile(filename="doctor_speech.mp3", file=io.BytesIO(b"ID3...."), headers={"content-type": "audio/mpeg"})
    validate_audio_file(file)

def test_validate_invalid_extension():
    file = UploadFile(filename="document.pdf", file=io.BytesIO(b"%PDF-1.4"), headers={"content-type": "application/pdf"})
    with pytest.raises(UnsupportedAudioFormatError) as exc_info:
        validate_audio_file(file)
    assert "Unsupported audio format" in str(exc_info.value)
    assert exc_info.value.error_code == "UNSUPPORTED_FORMAT"

def test_validate_empty_filename():
    file = UploadFile(filename="", file=io.BytesIO(b""))
    with pytest.raises(AudioValidationError) as exc_info:
        validate_audio_file(file)
    assert exc_info.value.error_code == "NO_FILE_PROVIDED"
