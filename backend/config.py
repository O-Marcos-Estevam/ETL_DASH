"""
Configuracoes centralizadas do ETL Dashboard V2 Backend
"""
import os
from pathlib import Path


class Settings:
    """Configuracoes do servidor e aplicacao"""

    # Paths
    BACKEND_DIR = Path(__file__).parent
    ROOT_DIR = BACKEND_DIR.parent  # DEV_ETL/
    PYTHON_DIR = ROOT_DIR / "python"
    CONFIG_DIR = ROOT_DIR / "config"

    # Server
    HOST = os.getenv("ETL_HOST", "0.0.0.0")
    PORT = int(os.getenv("ETL_PORT", "4001"))
    DEBUG = os.getenv("ETL_DEBUG", "false").lower() == "true"

    # CORS - Origens permitidas (separadas por virgula no env)
    ALLOWED_ORIGINS = os.getenv(
        "ETL_CORS_ORIGINS",
        "http://localhost:4000,http://127.0.0.1:4000"
    ).split(",")

    # Execution
    DEFAULT_TIMEOUT = int(os.getenv("ETL_TIMEOUT", "3600"))  # 1 hora
    POLL_INTERVAL = float(os.getenv("ETL_POLL_INTERVAL", "2.0"))  # segundos

    # Database
    DATA_DIR = BACKEND_DIR / "data"
    DB_PATH = DATA_DIR / "tasks.db"

    # Logging
    LOG_DIR = BACKEND_DIR / "logs"
    LOG_LEVEL = os.getenv("ETL_LOG_LEVEL", "INFO")
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


# Instancia singleton
settings = Settings()
