from loguru import logger
import re

class CommandRouter:
    """Routes direct commands to bypass the LLM and trigger robot actions directly."""
    
    def __init__(self):
        self.commands = {
            "turn left": "robot.move_head(-45, 0)",
            "turn right": "robot.move_head(45, 0)",
            "stop": "system.stop",
            "wave": "robot.wave_hand()",
            "move forward": "ros.publish('/cmd_vel', 'forward')"
        }
        
    def process_command(self, text: str) -> bool:
        """
        Returns True if a direct command was detected and processed.
        Returns False if the text should be passed to Gemini.
        """
        clean_text = text.lower().strip()
        # Remove punctuation
        clean_text = re.sub(r'[^\w\s]', '', clean_text)
        
        for cmd, action in self.commands.items():
            if clean_text == cmd or clean_text.startswith(cmd):
                logger.info(f"Command Router: Executed direct command -> {action}")
                return True
                
        return False
