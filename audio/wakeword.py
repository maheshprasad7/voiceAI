import speech_recognition as sr
from loguru import logger
from config.settings import settings

class WakeWordDetector:
    def __init__(self, wake_word=None):
        self.wake_word = (wake_word or settings.WAKE_WORD).lower()
        self.recognizer = sr.Recognizer()
        self.mic = sr.Microphone(device_index=settings.MIC_DEVICE_INDEX if settings.MIC_DEVICE_INDEX > 0 else None)
        
        logger.info("Calibrating wake word microphone for ambient noise...")
        with self.mic as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
        logger.info("Wake word calibration complete.")
            
    def listen_for_wake_word(self, callback):
        """
        Listens in the background for the wake word.
        Calls the callback function when detected.
        Returns a stop function to halt background listening.
        """
        logger.info(f"Background listening for wake word: '{self.wake_word}'")
        
        def callback_wrapper(recognizer, audio):
            try:
                # Using sphinx for offline, low-latency wake word detection if installed
                # Otherwise, fallback to recognize_google (requires internet but usually fast enough)
                try:
                    text = recognizer.recognize_google(audio).lower()
                except:
                    # If google fails or offline, maybe whisper or sphinx
                    # For production, consider using openwakeword or pvporcupine here.
                    logger.debug("WakeWord: STT failed for this chunk.")
                    return
                    
                logger.debug(f"Heard: {text}")
                
                # Check if wake word is present
                # Note: For multiple words, simple string inclusion is robust
                if self.wake_word in text or text.replace(" ", "") == self.wake_word.replace(" ", ""):
                    logger.success(f"Wake word '{self.wake_word}' detected!")
                    callback()
            except Exception as e:
                logger.error(f"Wake word error: {e}")
                
        stop_listening = self.recognizer.listen_in_background(self.mic, callback_wrapper)
        return stop_listening
