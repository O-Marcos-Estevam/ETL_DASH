from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import List
import logging

import services.state as state_service
from services.background_worker import get_worker
from config import settings

# Configurar logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format=settings.LOG_FORMAT
)
logger = logging.getLogger(__name__)


# Lifecycle manager para startup/shutdown
@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Gerencia startup e shutdown do app"""
    # Startup
    import database
    database.init_db()
    logger.info("Database inicializado")

    # Iniciar worker
    worker = get_worker()
    await worker.start()
    logger.info("BackgroundWorker iniciado")

    yield

    # Shutdown
    await worker.stop()
    logger.info("BackgroundWorker parado")


app = FastAPI(title="ETL Dashboard V2 Backend", lifespan=lifespan)

# CORS Setup - Usa origens configuradas (padrao: localhost:4000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
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
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast_log(self, log_entry: dict):
        """Envia log para todos os clientes conectados"""
        message = {
            "type": "log",
            "payload": log_entry
        }
        await self._broadcast(message)

    async def broadcast_status(self, sistema_id: str, status: str, progresso: int = 0, mensagem: str = None):
        """Envia status update de um sistema para todos os clientes"""
        message = {
            "type": "status",
            "payload": {
                "sistema_id": sistema_id,
                "status": status,
                "progresso": progresso,
                "mensagem": mensagem
            }
        }
        await self._broadcast(message)

    async def broadcast_job_complete(self, job_id: int, status: str, duracao: int = 0):
        """Envia notificacao de job completo"""
        message = {
            "type": "job_complete",
            "payload": {
                "job_id": job_id,
                "status": status,
                "duracao_segundos": duracao
            }
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

    @property
    def connection_count(self) -> int:
        """Retorna numero de conexoes ativas"""
        return len(self.active_connections)

manager = ConnectionManager()
# Register manager in shared state so other routers can use it
state_service.ws_manager = manager

# -------------------------------------------------------------------------
# Routers
# -------------------------------------------------------------------------
from routers.config import router as config_router
from routers.execution import router as execution_router
from routers.sistemas import router as sistemas_router
from routers.credentials import router as credentials_router

app.include_router(config_router)
app.include_router(execution_router)
app.include_router(sistemas_router)
app.include_router(credentials_router)


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
    uvicorn.run(
        "app:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG  # Apenas em desenvolvimento
    )
