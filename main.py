import uvicorn
import threading
from loguru import logger
import sys
import os
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logger.remove()
logger.add(sys.stdout, colorize=True, format="<green>{time}</green> <level>{message}</level>")
logger.add("logs/avahaan.log", rotation="10 MB")

from ui.dashboard import app as fastapi_app
from livekit import agents
from agent import entrypoint

def run_fastapi():
    """Runs the FastAPI server for the dashboard."""
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    logger.info(f"Starting dashboard at http://{host}:{port}")
    uvicorn.run(fastapi_app, host=host, port=port, log_level="error")

def main():
    # Start the Dashboard UI in a separate thread
    ui_thread = threading.Thread(target=run_fastapi, daemon=True)
    ui_thread.start()
    
    # Start the LiveKit agent
    logger.info("Starting LiveKit Agent...")
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))

if __name__ == "__main__":
    main()
