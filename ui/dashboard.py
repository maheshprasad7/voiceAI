import asyncio
import os
import time
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from starlette.responses import FileResponse
from loguru import logger
import json
import queue

from livekit.api import AccessToken, VideoGrants

app = FastAPI(title="AVAHAAN Voice Core")

# Shared queue for UI events
ui_event_queue = queue.Queue()
connected_clients = set()
latest_state = "IDLE"

@app.get("/")
async def get_dashboard():
    with open("ui/static/index.html", "r", encoding="utf-8") as f:
        content = f.read()
    return HTMLResponse(
        content,
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        }
    )

@app.get("/static/{filepath:path}")
async def serve_static(filepath: str):
    """Serve static files with no-cache headers."""
    file_path = os.path.join("ui", "static", filepath)
    if not os.path.exists(file_path):
        return JSONResponse({"error": "not found"}, status_code=404)
    
    # Determine content type
    content_type = "application/octet-stream"
    if filepath.endswith(".js"):
        content_type = "application/javascript"
    elif filepath.endswith(".css"):
        content_type = "text/css"
    elif filepath.endswith(".html"):
        content_type = "text/html"
    
    return FileResponse(
        file_path,
        media_type=content_type,
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        }
    )

@app.get("/token")
async def get_token():
    """Generate a LiveKit access token with a unique room per session."""
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")
    livekit_url = os.getenv("LIVEKIT_URL", "")

    if not api_key or not api_secret:
        return JSONResponse({"error": "LIVEKIT_API_KEY or LIVEKIT_API_SECRET not set"}, status_code=500)

    # Unique room name per session to avoid stale room conflicts on refresh
    room_name = f"avahaan-{int(time.time())}"
    identity = f"user-{int(time.time())}"

    token = (
        AccessToken(api_key, api_secret)
        .with_identity(identity)
        .with_name("User")
        .with_grants(VideoGrants(
            room_join=True,
            room=room_name,
        ))
    )

    return JSONResponse({
        "token": token.to_jwt(),
        "url": livekit_url,
        "room": room_name,
    })

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
