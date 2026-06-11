import google.generativeai as genai
import time
from loguru import logger
from config.settings import settings
from config.prompts import SYSTEM_PROMPT
from memory.conversation_memory import ConversationMemory

class GeminiAgent:
    def __init__(self, memory: ConversationMemory):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.memory = memory
        self.model_name = settings.MODEL_NAME
        
        # Initializing the model here, but we'll recreate it when system_instruction needs to update
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            system_instruction=self._get_dynamic_system_prompt()
        )
        
    def _get_dynamic_system_prompt(self):
        context = self.memory.get_context_string()
        if context:
            return f"{SYSTEM_PROMPT}\n\nAdditional Context:\n{context}"
        return SYSTEM_PROMPT
        
    def update_system_prompt(self):
        """Recreates the model instance with the updated memory context."""
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            system_instruction=self._get_dynamic_system_prompt()
        )
        
    def generate_response_stream(self, user_text: str):
        """
        Generates a streaming response from Gemini.
        Yields text chunks.
        """
        start_time = time.time()
        ttfb = 0.0
        
        self.memory.add_message("user", user_text)
        
        # Optional: very simple regex or logic here to extract facts before asking LLM,
        # For example, catching "My favourite cricketer is Dhoni" and saving it.
        if "favourite" in user_text.lower() or "favorite" in user_text.lower():
            # A more robust system would use a parallel LLM call to extract facts.
            # We'll just add the user's raw statement to facts for this version.
            self.memory.add_fact(user_text)
        
        try:
            self.update_system_prompt()
            
            gemini_history = []
            for msg in self.memory.get_history_for_llm():
                role = "user" if msg["role"] == "user" else "model"
                gemini_history.append({"role": role, "parts": [msg["content"]]})
                
            if len(gemini_history) > 0:
                history_for_chat = gemini_history[:-1]
                prompt = gemini_history[-1]["parts"][0]
            else:
                history_for_chat = []
                prompt = user_text
                
            chat = self.model.start_chat(history=history_for_chat)
            
            logger.debug(f"Sending to Gemini ({self.model_name})...")
            response = chat.send_message(prompt, stream=True)
            
            full_response = ""
            for chunk in response:
                if chunk.text:
                    if ttfb == 0.0:
                        ttfb = time.time() - start_time
                        logger.info(f"Gemini TTFB: {ttfb:.2f}s")
                    full_response += chunk.text
                    # Yielding text chunk
                    yield chunk.text
                    
            total_latency = time.time() - start_time
            logger.info(f"Gemini Total Latency: {total_latency:.2f}s")
            
            self.memory.add_message("model", full_response)
            
        except Exception as e:
            logger.error(f"Gemini Generation Error: {e}")
            yield "I encountered an error processing your request."
