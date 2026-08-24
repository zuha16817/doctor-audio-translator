import os
import pytest
from httpx import AsyncClient, ASGITransport
from backend.main import app

@pytest.mark.asyncio
async def test_health_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "stt_provider" in data

@pytest.mark.asyncio
async def test_languages_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/languages")
        assert response.status_code == 200
        data = response.json()
        assert "sourceLanguages" in data
        assert "targetLanguages" in data
        assert any(l["code"] == "ar" for l in data["sourceLanguages"])
        assert any(l["code"] == "ur" for l in data["sourceLanguages"])

@pytest.mark.asyncio
async def test_transcribe_translate_invalid_file_extension():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        files = {"audioFile": ("malicious.exe", b"MZ...", "application/x-msdownload")}
        data = {"sourceLanguage": "ar", "targetLanguage": "en"}
        response = await client.post("/api/audio/transcribe-translate", files=files, data=data)
        assert response.status_code == 400
        result = response.json()
        assert result["success"] is False
        assert result["errorCode"] == "UNSUPPORTED_FORMAT"
        assert "Unsupported audio format" in result["message"]

@pytest.mark.asyncio
async def test_transcribe_translate_with_sample_arabic():
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sample_path = os.path.join(root_dir, "frontend", "samples", "arabic_medical_sample.wav")
    assert os.path.exists(sample_path), f"Sample file not found at {sample_path}"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        with open(sample_path, "rb") as f:
            files = {"audioFile": ("arabic_medical_sample.wav", f, "audio/wav")}
            data = {"sourceLanguage": "ar", "targetLanguage": "en"}
            response = await client.post("/api/audio/transcribe-translate", files=files, data=data)
            
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert result["sourceLanguage"] == "ar"
        assert result["targetLanguage"] == "en"
        assert len(result["transcription"]) > 0
        assert len(result["translation"]) > 0
        assert result["detectedLanguageLabel"] == "Arabic"
        assert result["confidenceScore"] is not None and result["confidenceScore"] > 0
        assert result["summary"] is not None and len(result["summary"]) > 0

@pytest.mark.asyncio
async def test_transcribe_translate_with_sample_urdu():
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sample_path = os.path.join(root_dir, "frontend", "samples", "urdu_medical_sample.wav")
    assert os.path.exists(sample_path), f"Sample file not found at {sample_path}"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        with open(sample_path, "rb") as f:
            files = {"audioFile": ("urdu_medical_sample.wav", f, "audio/wav")}
            data = {"sourceLanguage": "ur", "targetLanguage": "en"}
            response = await client.post("/api/audio/transcribe-translate", files=files, data=data)
            
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert result["sourceLanguage"] == "ur"
        assert result["targetLanguage"] == "en"
        assert len(result["transcription"]) > 0
        assert len(result["translation"]) > 0
        assert result["detectedLanguageLabel"] == "Urdu"
        assert result["confidenceScore"] is not None and result["confidenceScore"] > 0
        assert result["summary"] is not None and len(result["summary"]) > 0
