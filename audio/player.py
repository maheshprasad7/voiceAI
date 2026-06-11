import pyaudio
from loguru import logger
from config.settings import settings

class AudioPlayer:
    def __init__(self):
        self.pa = pyaudio.PyAudio()
        self.stream = None
        self._stop_playing = False
        
    def play_stream(self, audio_chunk_generator, sample_rate=16000):
        """
        Plays an audio stream chunk by chunk. 
        Supports instant interruption via self.stop().
        """
        self._stop_playing = False
        
        try:
            self.stream = self.pa.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=sample_rate,
                output=True,
                output_device_index=settings.SPEAKER_DEVICE_INDEX if settings.SPEAKER_DEVICE_INDEX > 0 else None
            )
            
            logger.info("Started audio playback.")
            for chunk in audio_chunk_generator:
                if self._stop_playing:
                    logger.info("Playback interrupted instantly.")
                    break
                if chunk:
                    self.stream.write(chunk)
                    
        except Exception as e:
            logger.error(f"Error during audio playback: {e}")
        finally:
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
                self.stream = None
                logger.debug("Audio stream closed.")
            
    def stop(self):
        """Instantly stops the audio playback."""
        self._stop_playing = True

    def cleanup(self):
        self.pa.terminate()
