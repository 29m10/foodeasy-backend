"""
ElevenLabs text-to-speech service.
Converts text to speech using the ElevenLabs API:
POST https://api.elevenlabs.io/v1/text-to-speech/:voice_id
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any

import httpx
from dotenv import load_dotenv

load_dotenv()

# Project root (parent of app/)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
# Folder where generated voice MP3s are stored
VOICE_MP3S_DIR = Path(os.getenv("VOICE_MP3S_DIR", str(_PROJECT_ROOT / "voice_mp3s")))

ELEVENLABS_BASE_URL = "https://api.elevenlabs.io"
DEFAULT_OUTPUT_FORMAT = "mp3_44100_128"
DEFAULT_MODEL_ID = "eleven_v3"


def ensure_voice_mp3s_dir() -> Path:
    """Create VOICE_MP3S_DIR if it does not exist. Returns the path."""
    VOICE_MP3S_DIR.mkdir(parents=True, exist_ok=True)
    return VOICE_MP3S_DIR


def save_audio_to_voice_dir(audio_bytes: bytes, filename: str) -> Optional[Path]:
    """
    Save generated audio bytes to VOICE_MP3S_DIR.
    Creates the directory if needed. Returns the file path, or None on error.
    """
    try:
        ensure_voice_mp3s_dir()
        path = VOICE_MP3S_DIR / filename
        path.write_bytes(audio_bytes)
        return path
    except OSError as e:
        print(f"Failed to save voice MP3: {e}")
        return None


def _voice_settings_from_env() -> Dict[str, float]:
    """Build voice_settings from env, matching meal_messaging_service configuration."""
    stability = float(os.getenv("ELEVEN_LABS_VOICE_STABILITY", "0.5"))
    similarity_boost = float(os.getenv("ELEVEN_LABS_VOICE_SIMILARITY_BOOST", "0.75"))
    speed = float(os.getenv("ELEVEN_LABS_VOICE_SPEED", "1.0"))
    stability = max(0.0, min(1.0, stability))
    similarity_boost = max(0.0, min(1.0, similarity_boost))
    speed = max(0.25, min(4.0, speed))
    # Round stability to valid TTD values (0.0, 0.5, 1.0) for models that require it
    if stability < 0.25:
        stability = 0.0
    elif stability < 0.75:
        stability = 0.5
    else:
        stability = 1.0
    return {
        "stability": stability,
        "similarity_boost": similarity_boost,
        "speed": speed,
    }


class ElevenLabsTTSService:
    """
    Service for converting text to speech using the ElevenLabs API.
    """

    def __init__(self, api_key: Optional[str] = None, default_voice_id: Optional[str] = None):
        self._api_key = api_key or os.getenv("ELEVEN_LABS_API_KEY")
        self._default_voice_id = default_voice_id or os.getenv("ELEVEN_LABS_VOICE_ID")

    @property
    def is_configured(self) -> bool:
        """Return True if API key and at least default voice are configured."""
        return bool(self._api_key and self._default_voice_id)

    async def text_to_speech(
        self,
        text: str,
        voice_id: Optional[str] = None,
        model_id: Optional[str] = None,
        output_format: Optional[str] = None,
        voice_settings: Optional[Dict[str, float]] = None,
        timeout: float = 60.0,
    ) -> Optional[bytes]:
        """
        Convert text to speech using the ElevenLabs API.

        Args:
            text: The text to convert to speech.
            voice_id: Voice ID to use. Defaults to ELEVEN_LABS_VOICE_ID from env.
            model_id: Model ID (e.g. "eleven_multilingual_v2"). Defaults from env or constant.
            output_format: Audio format (e.g. "mp3_44100_128"). Defaults to mp3_44100_128.
            voice_settings: Optional dict with stability, similarity_boost, speed.
                When None, uses same env config as meal_messaging_service:
                ELEVEN_LABS_VOICE_STABILITY, ELEVEN_LABS_VOICE_SIMILARITY_BOOST, ELEVEN_LABS_VOICE_SPEED.
            timeout: Request timeout in seconds.

        Returns:
            Audio bytes on success, None on failure or if not configured.
        """
        vid = voice_id or self._default_voice_id
        if not self._api_key:
            return None
        if not vid:
            return None
        if not text or not text.strip():
            return None

        model_id = model_id or os.getenv("ELEVEN_LABS_MODEL_ID", DEFAULT_MODEL_ID)
        output_format = output_format or os.getenv("ELEVEN_LABS_OUTPUT_FORMAT", DEFAULT_OUTPUT_FORMAT)
        try:
            settings = voice_settings if voice_settings is not None else _voice_settings_from_env()
        except (ValueError, TypeError) as e:
            print(f"Invalid voice settings: {e}")
            return None

        url = f"{ELEVENLABS_BASE_URL}/v1/text-to-speech/{vid}"
        params = {"output_format": output_format}
        headers = {
            "xi-api-key": self._api_key,
            "Content-Type": "application/json",
        }
        payload: Dict[str, Any] = {
            "text": text.strip(),
            "model_id": model_id,
            "voice_settings": settings,
        }

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(url, params=params, headers=headers, json=payload)
                if response.status_code == 200:
                    return response.content
                # Log non-200 for debugging; do not raise
                ct = response.headers.get("content-type", "")
                if "application/json" in ct:
                    try:
                        err = response.json()
                        msg = err.get("detail", {}).get("message", err.get("detail", "Unknown error"))
                    except Exception:
                        msg = response.text
                else:
                    msg = response.text or f"HTTP {response.status_code}"
                print(f"ElevenLabs TTS error {response.status_code}: {msg}")
                return None
        except httpx.TimeoutException:
            print("ElevenLabs TTS timeout")
            return None
        except httpx.RequestError as e:
            print(f"ElevenLabs TTS request error: {e}")
            return None
        except Exception as e:
            print(f"ElevenLabs TTS error: {e}")
            return None

    def text_to_speech_sync(
        self,
        text: str,
        voice_id: Optional[str] = None,
        model_id: Optional[str] = None,
        output_format: Optional[str] = None,
        voice_settings: Optional[Dict[str, float]] = None,
        timeout: float = 60.0,
    ) -> Optional[bytes]:
        """
        Synchronous wrapper for text_to_speech. Use in non-async contexts.
        """
        import asyncio
        return asyncio.run(
            self.text_to_speech(
                text=text,
                voice_id=voice_id,
                model_id=model_id,
                output_format=output_format,
                voice_settings=voice_settings,
                timeout=timeout,
            )
        )
