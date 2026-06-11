import uvicorn
import threading
from loguru import logger
import sys

# Configure logging
logger.remove()
logger.add(sys.stdout, colorize=True, format="<green>{time}</green> <level>{message}</level>")
logger.add("logs/avahaan.log", rotation="10 MB")

from config.settings import settings
from ui.dashboard import app as fastapi_app, ui_event_queue
from conversation.conversation_manager import ConversationManager

def run_fastapi():
    """Runs the FastAPI server for the dashboard."""
    logger.info(f"Starting dashboard at http://{settings.HOST}:{settings.PORT}")
    uvicorn.run(fastapi_app, host=settings.HOST, port=settings.PORT, log_level="error")

def main():
    # Start the Dashboard UI in a separate thread
    ui_thread = threading.Thread(target=run_fastapi, daemon=True)
    ui_thread.start()
    
    # Initialize and start the conversation manager
    manager = ConversationManager(ui_queue=ui_event_queue)
    manager.start()
    
    # Keep the main thread alive
    try:
        ui_thread.join()
    except KeyboardInterrupt:
        logger.info("Shutting down AVAHAAN Voice Agent...")

if __name__ == "__main__":
    main()
