# Doctor’s Audio Transcription & Translation System

An enterprise-grade, clinical-focused web application designed to transcribe doctor and patient speech in **Arabic** and **Urdu**, and translate it seamlessly into **English** and other target languages.

---

## 🌟 Key Features

* **Multi-Format Audio Upload**: Supports `.mp3`, `.wav`, `.m4a`, and `.webm` up to 50 MB with strict server-side validation.
* **In-Browser Voice Recording**: High-fidelity recording using the `MediaRecorder` API accompanied by a real-time Web Audio API frequency waveform visualizer.
* **Dual-Engine Decoupled Architecture**:
  * **Speech-to-Text (STT)**: Decoupled via `ISpeechToTextService` with high-speed local `faster-whisper` (CTranslate2) and cloud Whisper fallback.
  * **Translation**: Decoupled via `ITranslationService` with multi-engine fallback chains.
* **Authentic Multilingual & RTL Typography**: Dynamic Right-to-Left (`dir="rtl"`) layout and custom Google Fonts (`Cairo` for Arabic, `Noto Nastaliq Urdu` for Urdu).
* **Clinical Privacy & Security**: Zero permanent retention of audio. Audio is saved to temporary storage with randomized UUIDs and deterministically deleted immediately after processing.
* **Clinical Productivity Tools**: One-click copy-to-clipboard, `.txt` transcript downloads, text-to-speech audio pronunciation, and one-click sample loaders for testing.

---

## 🏛️ System Architecture

```mermaid
graph TD
    User["👨‍⚕️ Doctor / Patient"] -->|Upload or Mic Stream| UI["🖥️ Single Page Interface"]
    UI -->|REST API multipart/form-data| Backend["⚙️ FastAPI Backend (/api/audio/transcribe-translate)"]
    
    subgraph Security & Pipeline
        Backend --> Validate["🔒 Validation (Extension, MIME, Size)"]
        Validate --> Ephemeral["💾 Ephemeral Storage (UUID temp file)"]
        Ephemeral --> STT["🎙️ ISpeechToTextService (Faster-Whisper)"]
        STT --> Trans["📝 Arabic/Urdu Source Text"]
        Trans --> Translate["🌐 ITranslationService (Multi-Engine)"]
        Translate --> Result["📄 English / Target Translation"]
        Result --> Cleanup["🧹 Deterministic Cleanup (File Deleted)"]
    end
    
    Cleanup --> Response["📦 JSON Response"]
    Response --> UI
```

---

## 🚀 Quick Start Guide

### Prerequisites
* Python 3.10+
* `ffmpeg` installed on the host machine (for audio processing)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment (Optional)
Copy `.env.example` to `.env` if you wish to customize configuration:
```bash
cp .env.example .env
```

### 3. Run the Server
```bash
python backend/main.py
```
Or with Uvicorn directly:
```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Open in Browser
Visit **`http://localhost:8000`** to access the application.

---

## 📡 REST API Reference

### `POST /api/audio/transcribe-translate`
Processes audio file and returns transcription and translation.

#### Request (`multipart/form-data`)
| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `audioFile` | Binary File | Yes | Audio file (`.mp3`, `.wav`, `.m4a`, `.webm`) |
| `sourceLanguage` | String | No | `auto` (default), `ar` (Arabic), or `ur` (Urdu) |
| `targetLanguage` | String | Yes | `en` (default), `ar`, `ur`, `fr`, `es`, `de` |

#### Success Response (`200 OK`)
```json
{
  "success": true,
  "sourceLanguage": "ar",
  "targetLanguage": "en",
  "transcription": "مرحبا يا دكتور، أشعر بألم شديد في المعدة منذ يومين وارتفاع في درجة الحرارة.",
  "translation": "Hello doctor, I have been feeling severe stomach pain for two days and a high fever.",
  "durationSeconds": 1.45,
  "detectedLanguageLabel": "Arabic"
}
```

#### Error Response (`400 Bad Request` or `500 Internal Error`)
```json
{
  "success": false,
  "errorCode": "UNSUPPORTED_FORMAT",
  "message": "Unsupported audio format '.pdf'. Supported formats: .mp3, .wav, .m4a, .webm, .ogg"
}
```

---

## 🧪 Running Automated Tests

Run the full test suite with Pytest:
```bash
pytest backend/tests/ -v
```

---

## 📄 License
Developed for clinical workflow automation and medical language accessibility.
