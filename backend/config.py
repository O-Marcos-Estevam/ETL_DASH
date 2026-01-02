"""
Configuracoes centralizadas do ETL Dashboard V2 Backend
Suporta execucao como script Python ou executavel standalone
"""
import os
import sys
from pathlib import Path


def get_app_dir() -> Path:
    """
    Retorna diretorio base da aplicacao.
    Funciona tanto para desenvolvimento quanto para executavel PyInstaller.
    
    Em modo portable, a estrutura é:
    ETL_Dashboard/           <- ROOT (retornado)
    ├── runtime/
    │   └── backend/
    │       └── etl_backend.exe   <- sys.executable (2 níveis abaixo)
    """
    if getattr(sys, 'frozen', False):
        # Executando como .exe (PyInstaller)
        # O exe está em runtime/backend/, precisamos subir 2 níveis
        return Path(sys.executable).parent.parent.parent
    else:
        # Executando como script Python
        return Path(__file__).parent.parent  # DEV_ETL/


def is_portable() -> bool:
    """Retorna True se estiver rodando como executavel"""
    return getattr(sys, 'frozen', False)


class Settings:
    """Configuracoes do servidor e aplicacao"""

    # Diretorio base (funciona para dev e exe)
    APP_DIR = get_app_dir()
    
    # Paths - Desenvolvimento
    BACKEND_DIR = Path(__file__).parent if not is_portable() else APP_DIR / "runtime" / "backend"
    ROOT_DIR = APP_DIR
    PYTHON_DIR = APP_DIR / "python" if not is_portable() else APP_DIR / "modules"
    CONFIG_DIR = APP_DIR / "config"
    
    # Paths - Runtime (Chrome portatil)
    RUNTIME_DIR = APP_DIR / "runtime"
    CHROME_PATH = RUNTIME_DIR / "chromium" / "chrome.exe"
    CHROMEDRIVER_PATH = RUNTIME_DIR / "drivers" / "chromedriver.exe"
    
    # Paths - Frontend estatico
    WEB_DIR = APP_DIR / "web"

    # Server
    HOST = os.getenv("ETL_HOST", "0.0.0.0")
    PORT = int(os.getenv("ETL_PORT", "4001"))
    DEBUG = os.getenv("ETL_DEBUG", "false").lower() == "true"

    # CORS - Origens permitidas (separadas por virgula no env)
    # Em modo portatil, permitir localhost
    ALLOWED_ORIGINS = os.getenv(
        "ETL_CORS_ORIGINS",
        "http://localhost:4000,http://127.0.0.1:4000,http://localhost:4001,http://127.0.0.1:4001"
    ).split(",")

    # Execution
    DEFAULT_TIMEOUT = int(os.getenv("ETL_TIMEOUT", "3600"))  # 1 hora
    POLL_INTERVAL = float(os.getenv("ETL_POLL_INTERVAL", "2.0"))  # segundos

    # Database - usar pasta data/ no diretorio da app
    DATA_DIR = APP_DIR / "data"
    DB_PATH = DATA_DIR / "tasks.db"

    # Logging
    LOG_DIR = APP_DIR / "logs"
    LOG_LEVEL = os.getenv("ETL_LOG_LEVEL", "INFO")
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    @classmethod
    def ensure_dirs(cls):
        """Cria diretorios necessarios se nao existirem"""
        cls.DATA_DIR.mkdir(parents=True, exist_ok=True)
        cls.LOG_DIR.mkdir(parents=True, exist_ok=True)
        cls.CONFIG_DIR.mkdir(parents=True, exist_ok=True)


# Instancia singleton
settings = Settings()

# Criar diretorios ao importar
settings.ensure_dirs()
