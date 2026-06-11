import threading
import time
from loguru import logger

from audio.wakeword import WakeWordDetector
from audio.recorder import AudioRecorder
from audio.player import AudioPlayer
from stt.elevenlabs_stt import SpeechToTextEngine
from llm.gemini_agent import GeminiAgent
from memory.conversation_memory import ConversationMemory
from tts.elevenlabs_tts import TextToSpeechEngine
from conversation.command_router import CommandRouter

class ConversationManager:
    def __init__(self, ui_queue=None):
        self.state = "IDLE"
        self.ui_queue = ui_queue
        
        self.memory = ConversationMemory()
        self.agent = GeminiAgent(self.memory)
        self.recorder = AudioRecorder()
        self.player = AudioPlayer()
        self.stt = SpeechToTextEngine()
        self.tts = TextToSpeechEngine()
        self.router = CommandRouter()
        
        # Wake word detector
        self.wake_detector = WakeWordDetector()
        
        # Interruption detector
        self.stop_detector = WakeWordDetector(wake_word="stop")
        self._stop_listening_fn = None
        self._interrupted = False
        
    def _set_state(self, new_state: str):
        self.state = new_state
        logger.info(f"State Transition: -> {self.state}")
        if self.ui_queue:
            self.ui_queue.put({"type": "state", "data": self.state})
            
    def _emit_ui(self, metric_type: str, data: any):
        if self.ui_queue:
            self.ui_queue.put({"type": metric_type, "data": data})

    def start(self):
        """Starts the main conversation loop."""
        self._set_state("IDLE")
        logger.info("Starting AVAHAAN Voice Agent orchestration...")
        # Start background listening
        self.wake_detector.listen_for_wake_word(self.on_wake_word)
        
    def on_wake_word(self):
        if self.state in ["IDLE", "INTERRUPTED"]:
            # Run turn in a new thread
            threading.Thread(target=self.run_turn, daemon=True).start()
            
    def _stop_callback(self):
        if self.state == "SPEAKING":
            logger.warning("Interruption detected! 'Stop' spoken.")
            self._interrupted = True
            self.player.stop()

    def run_turn(self):
        while True:
            turn_start_time = time.time()
            try:
                self._set_state("LISTENING")
                audio_bytes = self.recorder.record_utterance()
                
                if not audio_bytes:
                    logger.info("No speech detected. Ending conversation loop.")
                    self._set_state("IDLE")
                    break
                    
                self._set_state("TRANSCRIBING")
                text, stt_latency = self.stt.transcribe(audio_bytes)
                self._emit_ui("latency_stt", stt_latency)
                self._emit_ui("transcript", text)
                
                if not text:
                    logger.info("Transcription failed or empty. Ending conversation loop.")
                    self._set_state("IDLE")
                    break
                    
                if self.router.process_command(text):
                    logger.info("Command executed. Ending conversation loop.")
                    self._set_state("IDLE")
                    break
                    
                self._set_state("THINKING")
                
                # The agent.generate_response_stream measures Gemini latency internally, 
                # we will just stream it out
                text_generator = self.agent.generate_response_stream(text)
                
                self._set_state("SPEAKING")
                
                # Start listening for interruption
                self._interrupted = False
                self._stop_listening_fn = self.stop_detector.listen_for_wake_word(self._stop_callback)
                
                audio_stream = self.tts.stream_tts(text_generator)
                
                # Wait for TTS to stream and play
                self.player.play_stream(audio_stream)
                
                if self._stop_listening_fn:
                    self._stop_listening_fn(wait_for_stop=False)
                    
                total_latency = time.time() - turn_start_time
                self._emit_ui("latency_total", total_latency)
                    
                if self._interrupted:
                    self._set_state("INTERRUPTED")
                    # If interrupted by "Stop", don't end the conversation, just loop back to listening!
                    continue
                else:
                    # After speaking normally, loop back to LISTENING
                    continue

            except Exception as e:
                logger.error(f"Error in conversation turn: {e}")
                self._set_state("ERROR")
                time.sleep(2)
                self._set_state("IDLE")
                break

