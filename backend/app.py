from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import List, Optional
import logging

import services.state as state_service
from services.worker import get_worker
from config import settings

# Import security middleware
from middleware.security_headers import SecurityHeadersMiddleware
from middleware.rate_limiter import RateLimitMiddleware

# Import auth router and dependencies
from auth.router import router as auth_router
from auth.dependencies import get_ws_user
from auth.database import init_auth_tables

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

    # Initialize auth tables
    init_auth_tables()
    logger.info("Auth tables inicializadas")

    # Check for ETL_MASTER_KEY (required for encrypted credentials)
    import os
    if not os.getenv("ETL_MASTER_KEY"):
        logger.warning(
            "⚠️  ETL_MASTER_KEY not set! Encrypted credentials will NOT work. "
            "Set the environment variable or credentials will use defaults."
        )

    # Initialize WebSocket manager (supports Redis for distributed mode)
    from services.distributed_ws import create_ws_manager
    ws_manager = create_ws_manager()
    await ws_manager.initialize()
    state_service.ws_manager = ws_manager
    logger.info(f"WebSocket manager initialized: distributed={ws_manager.is_distributed}")

    # Iniciar worker
    worker = get_worker()
    await worker.start()
    logger.info(f"BackgroundWorker iniciado: mode={worker.get_status().get('mode', 'single')}")

    yield

    # Shutdown
    await worker.stop()
    logger.info("BackgroundWorker parado")

    # Shutdown WebSocket manager
    await ws_manager.shutdown()
    logger.info("WebSocket manager shutdown complete")


# OpenAPI Tags para organizar documentação
openapi_tags = [
    {
        "name": "auth",
        "description": "Autenticação e gerenciamento de usuários"
    },
    {
        "name": "execution",
        "description": "Execução e monitoramento de pipelines ETL"
    },
    {
        "name": "sistemas",
        "description": "Gerenciamento de sistemas ETL disponíveis"
    },
    {
        "name": "credentials",
        "description": "Configuração de credenciais e paths"
    },
    {
        "name": "config",
        "description": "Configurações gerais do sistema"
    },
]

app = FastAPI(
    title="ETL Dashboard API",
    description="""
## API para gerenciamento de pipelines ETL

Esta API permite:
- **Executar** pipelines ETL para múltiplos sistemas
- **Monitorar** status de execução em tempo real via WebSocket
- **Configurar** credenciais e paths de sistemas
- **Gerenciar** usuários e permissões

### Autenticação
A maioria dos endpoints requer autenticação JWT.
Use `/api/auth/login` para obter um token de acesso.

### WebSocket
Conecte em `/ws?token=<jwt>` para receber atualizações em tempo real.
    """,
    version="2.1.0",
    openapi_tags=openapi_tags,
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    license_info={
        "name": "Proprietary",
    },
)

# Security Middleware (order matters - first added = outermost)
# Add security headers to all responses
app.add_middleware(SecurityHeadersMiddleware)

# Rate limiting
app.add_middleware(RateLimitMiddleware, default_limit=100, window_seconds=60)

# CORS Setup - More restrictive configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
    expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"],
    max_age=600,  # Cache preflight for 10 minutes
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
# WebSocket Manager
# -------------------------------------------------------------------------
# The WebSocket manager is now created in lifespan() using DistributedConnectionManager
# which supports both local-only and Redis-distributed modes.
# Access via state_service.ws_manager after app startup.

# -------------------------------------------------------------------------
# Routers
# -------------------------------------------------------------------------
from routers.config import router as config_router
from routers.execution import router as execution_router
from routers.sistemas import router as sistemas_router
from routers.credentials import router as credentials_router

# Include auth router first
app.include_router(auth_router)

# Include other routers
app.include_router(config_router)
app.include_router(execution_router)
app.include_router(sistemas_router)
app.include_router(credentials_router)


from models.api import HealthResponse

@app.get(
    "/api/health",
    response_model=HealthResponse,
    tags=["config"],
    summary="Health Check",
    description="Verifica se a API está funcionando corretamente."
)
async def health_check():
    """Retorna status de saúde da API"""
    return HealthResponse(status="ok", version="2.2.0")


@app.get(
    "/api/ws/stats",
    tags=["config"],
    summary="WebSocket Stats",
    description="Returns WebSocket manager statistics including Redis status."
)
async def websocket_stats():
    """Returns WebSocket manager statistics"""
    manager = state_service.ws_manager
    if manager:
        return manager.get_stats()
    return {"error": "WebSocket manager not initialized"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: Optional[str] = Query(None)):
    """
    WebSocket endpoint for real-time logs and status updates.

    Supports optional authentication via query parameter: ws://host/ws?token=<jwt>
    If AUTH_REQUIRED environment variable is set, authentication is mandatory.
    """
    import os

    # Check if authentication is required
    auth_required = os.getenv("AUTH_REQUIRED", "false").lower() == "true"

    if auth_required and token:
        try:
            # Validate token
            from auth.security import decode_token
            from auth.database import get_user_by_username

            payload = decode_token(token)
            if not payload or payload.type != "access":
                await websocket.close(code=4001, reason="Invalid token")
                return

            user = get_user_by_username(payload.sub)
            if not user or not user.is_active:
                await websocket.close(code=4003, reason="User not found or disabled")
                return

            logger.info(f"WebSocket authenticated: {user.username}")
        except Exception as e:
            logger.warning(f"WebSocket auth error: {e}")
            await websocket.close(code=4001, reason="Authentication failed")
            return
    elif auth_required and not token:
        await websocket.close(code=4001, reason="Token required")
        return

    # Get WebSocket manager from shared state
    manager = state_service.ws_manager
    if not manager:
        await websocket.close(code=4000, reason="Service unavailable")
        return

    # Connect and handle messages
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
