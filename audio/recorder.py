import pyaudio

import numpy as np
import wave
import io
# pyrefly: ignore [missing-import]
from loguru import logger
from config.settings import settings

class AudioRecorder:
    def __init__(self, sample_rate=16000, chunk_duration_ms=30):
        self.sample_rate = sample_rate
        self.chunk_duration_ms = chunk_duration_ms
        self.chunk_size = int(self.sample_rate * self.chunk_duration_ms / 1000)
        self.energy_threshold = 500  # RMS threshold for speech
        self.pa = pyaudio.PyAudio()
        
    def record_utterance(self, silence_duration_ms=1500) -> bytes:
        """
        Records an utterance. Stops after `silence_duration_ms` of continuous silence.
        Returns the recorded audio as WAV bytes.
        """
        stream = self.pa.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self.sample_rate,
            input=True,
            input_device_index=settings.MIC_DEVICE_INDEX if settings.MIC_DEVICE_INDEX > 0 else None,
            frames_per_buffer=self.chunk_size
        )
        
        logger.info("Microphone active. Listening for speech...")
        
        frames = []
        silence_chunks = 0
        speech_started = False
        max_silence_chunks = int(silence_duration_ms / self.chunk_duration_ms)
        
        try:
            while True:
                data = stream.read(self.chunk_size, exception_on_overflow=False)
                # Calculate RMS energy using numpy
                audio_data = np.frombuffer(data, dtype=np.int16).astype(np.float32)
                rms_energy = np.sqrt(np.mean(np.square(audio_data)))
                is_speech = rms_energy > self.energy_threshold
                
                if is_speech:
                    if not speech_started:
                        logger.debug("Speech detected.")
                    speech_started = True
                    silence_chunks = 0
                    frames.append(data)
                else:
                    if speech_started:
                        silence_chunks += 1
                        frames.append(data)
                        if silence_chunks > max_silence_chunks:
                            logger.debug("Silence detected, stopping recording.")
                            break
                    else:
                        # Keep a small buffer before speech starts
                        frames.append(data)
                        if len(frames) > 10:
                            frames.pop(0)
        finally:
            stream.stop_stream()
            stream.close()
            
        if not speech_started:
            return None
            
        # Convert frames to WAV bytes
        wav_io = io.BytesIO()
        with wave.open(wav_io, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(self.pa.get_sample_size(pyaudio.paInt16))
            wf.setframerate(self.sample_rate)
            wf.writeframes(b''.join(frames))
            
        return wav_io.getvalue()

    def cleanup(self):
        self.pa.terminate()
