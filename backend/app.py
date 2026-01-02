from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import List
import logging

import services.state as state_service
from services.worker import get_worker
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
    from core import database
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
# Servir Frontend Estatico (modo producao/portatil)
# -------------------------------------------------------------------------
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Montar arquivos estaticos se pasta web/ existir
if settings.WEB_DIR.exists() and (settings.WEB_DIR / "index.html").exists():
    # Servir assets
    if (settings.WEB_DIR / "assets").exists():
        app.mount("/assets", StaticFiles(directory=settings.WEB_DIR / "assets"), name="assets")
    
    logger.info(f"Frontend estatico disponivel em: {settings.WEB_DIR}")

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
            except Exception as e:
                logger.warning(f"Erro ao enviar mensagem via WebSocket: {e}")
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

# Rota catch-all para servir index.html (SPA routing)
# Deve vir depois de todas as outras rotas
@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    """Serve index.html para rotas do SPA (React Router)"""
    # Ignorar rotas de API e WebSocket
    if full_path.startswith("api/") or full_path.startswith("ws"):
        return {"detail": "Not found"}
    
    # Servir index.html se existir
    index_path = settings.WEB_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    
    # Em desenvolvimento, redirecionar para frontend separado
    return {"message": "Frontend nao encontrado. Execute 'npm run build' ou use http://localhost:4000"}

def check_port_available(host: str, port: int) -> bool:
    """Verifica se a porta esta disponivel tentando fazer bind"""
    import socket
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind((host, port))
                return True  # Porta esta livre
            except OSError:
                return False  # Porta ja esta em uso
    except Exception as e:
        logger.warning(f"Erro ao verificar porta: {e}")
        return True  # Em caso de erro, tenta iniciar mesmo assim

if __name__ == "__main__":
    import uvicorn
    import sys
    
    # Verificar se porta esta disponivel
    if not check_port_available(settings.HOST, settings.PORT):
        logger.error(f"Porta {settings.PORT} ja esta em uso!")
        logger.info("Tentando usar porta alternativa 4002...")
        settings.PORT = 4002
        
        # Verificar porta 4002
        if not check_port_available(settings.HOST, settings.PORT):
            logger.error(f"Porta {settings.PORT} tambem esta em uso!")
            logger.error("Por favor, encerre processos Python ou configure outra porta via ETL_PORT")
            sys.exit(1)
    
    logger.info(f"Iniciando servidor em {settings.HOST}:{settings.PORT}")
    
    # Em modo PyInstaller (frozen), passar objeto app diretamente
    # Em modo desenvolvimento, usar string para permitir reload
    if getattr(sys, 'frozen', False):
        # Modo executavel - passar objeto app diretamente
        uvicorn.run(
            app,
            host=settings.HOST,
            port=settings.PORT,
            log_level="info"
        )
    else:
        # Modo desenvolvimento - usar string para hot reload
        uvicorn.run(
            "app:app",
            host=settings.HOST,
            port=settings.PORT,
            reload=settings.DEBUG
        )
