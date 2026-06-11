import speech_recognition as sr
import io
from loguru import logger

class WhisperFallbackSTT:
    def __init__(self, model_size="base"):
        logger.info("Initializing Google STT fallback (replacing Whisper due to missing ffmpeg)...")
        self.recognizer = sr.Recognizer()
        logger.info("Google STT fallback initialized.")
        
    def transcribe(self, audio_bytes: bytes) -> str:
        """Transcribes audio using Google STT."""
        if not audio_bytes:
            return ""
            
        try:
            logger.debug("Transcribing with Google STT fallback...")
            with io.BytesIO(audio_bytes) as source:
                with sr.AudioFile(source) as audio_file:
                    audio_data = self.recognizer.record(audio_file)
                    text = self.recognizer.recognize_google(audio_data)
                    logger.debug(f"Google Fallback Result: {text}")
                    return text
        except sr.UnknownValueError:
            logger.warning("Google STT could not understand audio.")
            return ""
        except sr.RequestError as e:
            logger.error(f"Could not request results from Google STT service; {e}")
            return ""
        except Exception as e:
            logger.error(f"Fallback STT failed: {e}")
            return ""
