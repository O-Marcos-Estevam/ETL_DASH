from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import services.state as state_service

app = FastAPI(title="ETL Dashboard V2 Backend")

# CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------------------------------
# WebSocket Manager (Moved to class for clarity)
# -------------------------------------------------------------------------
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast_log(self, log_entry: dict):
        message = {
            "type": "log",
            "payload": log_entry
        }
        await self._broadcast(message)
    
    async def _broadcast(self, message: dict):
        disconnect_list = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                disconnect_list.append(connection)
        
        for conn in disconnect_list:
            self.disconnect(conn)

manager = ConnectionManager()
# Register manager in shared state so other routers can use it
state_service.ws_manager = manager

# -------------------------------------------------------------------------
# Routers
# -------------------------------------------------------------------------
from routers.config import router as config_router
from routers.execution import router as execution_router

app.include_router(config_router)
app.include_router(execution_router)

import database

@app.on_event("startup")
async def startup_event():
    database.init_db()

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "version": "2.1.0"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=4001, reload=True)
