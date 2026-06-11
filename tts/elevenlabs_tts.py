from elevenlabs.client import ElevenLabs
from elevenlabs import VoiceSettings
from config.settings import settings
from loguru import logger
import time

class TextToSpeechEngine:
    def __init__(self):
        self.client = ElevenLabs(api_key=settings.ELEVENLABS_API_KEY)
        self.voice_id = settings.VOICE_ID
        
    def stream_tts(self, text_iterator):
        """
        Takes an iterator of text chunks (e.g., from Gemini).
        Yields audio chunks in PCM 16000 format.
        """
        logger.debug("Starting ElevenLabs TTS stream...")
        start_time = time.time()
        ttfb = 0.0
        
        try:
            # Note: The elevenlabs client v1 supports text as an Iterator[str].
            # This triggers their WebSocket input streaming endpoint automatically
            # for ultra-low latency generation.
            audio_stream = self.client.text_to_speech.convert_realtime(
                text=text_iterator,
                voice_id=self.voice_id,
                # Using turbo model for lowest latency, fallback to multilingual if needed
                model_id="eleven_turbo_v2_5", 
                output_format="pcm_16000",
                voice_settings=VoiceSettings(stability=0.5, similarity_boost=0.8, style=0.0, use_speaker_boost=True)
            )
            
            for chunk in audio_stream:
                if ttfb == 0.0:
                    ttfb = time.time() - start_time
                    logger.info(f"TTS Audio TTFB: {ttfb:.2f}s")
                if chunk:
                    yield chunk
                    
            total_latency = time.time() - start_time
            logger.info(f"TTS Total Latency: {total_latency:.2f}s")
            
        except Exception as e:
            logger.error(f"ElevenLabs TTS Error: {e}")
            logger.warning("If the elevenlabs python package version doesn't support generator input, please implement a sentence-buffer approach.")
