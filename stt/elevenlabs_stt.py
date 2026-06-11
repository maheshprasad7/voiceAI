import requests
import time
from loguru import logger
from config.settings import settings
from stt.whisper_fallback import WhisperFallbackSTT

class SpeechToTextEngine:
    def __init__(self):
        self.api_key = settings.ELEVENLABS_API_KEY
        # Using ElevenLabs REST STT endpoint. 
        self.url = "https://api.elevenlabs.io/v1/speech-to-text" 
        self.fallback = WhisperFallbackSTT(model_size="base")
        
    def transcribe(self, audio_bytes: bytes) -> tuple[str, float]:
        """
        Transcribes audio. Returns tuple of (transcription_text, latency_seconds).
        Now uses Google STT natively for near-zero latency.
        """
        start_time = time.time()
        
        if not audio_bytes:
            return "", 0.0
            
        try:
            logger.debug("Transcribing via native Google STT...")
            text = self.fallback.transcribe(audio_bytes)
            latency = time.time() - start_time
            if text:
                logger.info(f"Google STT successful. Latency: {latency:.2f}s")
            return text, latency
            
        except Exception as e:
            logger.error(f"Google STT failed: {e}")
            return "", time.time() - start_time
