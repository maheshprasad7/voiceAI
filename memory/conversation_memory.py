from loguru import logger
from typing import List, Dict

class ConversationMemory:
    def __init__(self):
        # We can set default user name or update it dynamically later
        self.user_name: str = "User" 
        self.conversation_history: List[Dict[str, str]] = []
        self.preferences: Dict[str, str] = {}
        self.important_facts: List[str] = []
        
    def add_message(self, role: str, content: str):
        """Adds a message to the history and maintains the buffer size."""
        self.conversation_history.append({"role": role, "content": content})
        # Keep last 20 messages to prevent context bloat
        if len(self.conversation_history) > 20:
            self.conversation_history.pop(0)
            
    def get_history_for_llm(self):
        """Returns the conversation history."""
        return self.conversation_history
        
    def add_fact(self, fact: str):
        """Adds an important fact to the long-term memory buffer."""
        self.important_facts.append(fact)
        logger.info(f"Memory: Saved new fact - {fact}")
        
    def update_preference(self, key: str, value: str):
        """Updates a user preference."""
        self.preferences[key] = value
        logger.info(f"Memory: Updated preference - {key}: {value}")
        
    def get_context_string(self) -> str:
        """Returns a string containing facts and preferences to prepend to the system prompt."""
        context = []
        if self.user_name != "User":
            context.append(f"The user's name is {self.user_name}.")
            
        if self.preferences:
            prefs = ", ".join([f"{k}: {v}" for k, v in self.preferences.items()])
            context.append(f"User preferences: {prefs}")
            
        if self.important_facts:
            facts = "\n".join([f"- {f}" for f in self.important_facts])
            context.append(f"Important facts remembered:\n{facts}")
            
        return "\n\n".join(context)
