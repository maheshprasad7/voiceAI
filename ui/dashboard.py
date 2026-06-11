import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from loguru import logger
import json
import queue

app = FastAPI(title="AVAHAAN Voice Core")

# Shared queue for UI events
ui_event_queue = queue.Queue()
connected_clients = set()
latest_state = "IDLE"


# Mount static files
app.mount("/static", StaticFiles(directory="ui/static"), name="static")

@app.get("/")
async def get_dashboard():
    with open("ui/static/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())
        
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.add(websocket)
    await websocket.send_text(json.dumps({"type": "state", "data": latest_state}))
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        connected_clients.remove(websocket)

async def broadcast_events():
    """Background task to broadcast events from the queue to all websockets."""
    logger.info("UI Broadcast task started.")
    while True:
        try:
            if not ui_event_queue.empty():
                event = ui_event_queue.get_nowait()
                global latest_state
                if event.get("type") == "state":
                    latest_state = event.get("data")
                    
                if connected_clients:
                    msg = json.dumps(event)
                    disconnected = set()
                    for client in connected_clients:
                        try:
                            await client.send_text(msg)
                        except:
                            disconnected.add(client)
                    for c in disconnected:
                        connected_clients.remove(c)
            await asyncio.sleep(0.05)
        except Exception as e:
            logger.error(f"UI Broadcast Error: {e}")
            await asyncio.sleep(1)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(broadcast_events())
