import pytest
from backend.services.translation.factory import get_translation_service
from backend.services.speech.factory import get_speech_to_text_service

@pytest.mark.asyncio
async def test_translation_service_arabic_to_english():
    service = get_translation_service()
    arabic_text = "مرحبا يا دكتور، أشعر بألم في المعدة."
    translated = await service.translate(arabic_text, source_language="ar", target_language="en")
    assert isinstance(translated, str)
    assert len(translated) > 0
    assert any(w in translated.lower() for w in ["hello", "doctor", "stomach", "pain"])

@pytest.mark.asyncio
async def test_translation_service_urdu_to_english():
    service = get_translation_service()
    urdu_text = "مجھے شدید بخار ہے۔"
    translated = await service.translate(urdu_text, source_language="ur", target_language="en")
    assert isinstance(translated, str)
    assert len(translated) > 0
    assert any(w in translated.lower() for w in ["fever", "severe", "high"])

@pytest.mark.asyncio
async def test_translation_same_language():
    service = get_translation_service()
    text = "Hello doctor"
    translated = await service.translate(text, source_language="en", target_language="en")
    assert translated == text
