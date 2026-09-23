"""Live Worker Telemetry WebSocket & Broadcast Subsystem."""
import json
import time
from typing import Set, Dict, Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter(tags=["Telemetry"])


class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)

    async def broadcast(self, message: Dict[str, Any]):
        dead_connections = set()
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                dead_connections.add(connection)
        for dead in dead_connections:
            self.active_connections.discard(dead)


manager = ConnectionManager()


@router.websocket("/ws/telemetry")
async def websocket_telemetry_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        await websocket.send_json({
            "type": "CONNECTION_ESTABLISHED",
            "message": "Connected to Gieni OS Live Telemetry Stream.",
            "timestamp": time.time(),
            "data": {"status": "ACTIVE"},
        })
        while True:
            raw_text = await websocket.receive_text()
            try:
                data = json.loads(raw_text)
                if data.get("type") == "SUBSCRIBE":
                    await websocket.send_json({
                        "type": "SUBSCRIBED",
                        "message": f"Subscribed to {data.get('channel', 'TELEMETRY')} stream.",
                        "timestamp": time.time(),
                    })
            except Exception:
                pass
    except (WebSocketDisconnect, Exception):
        manager.disconnect(websocket)
