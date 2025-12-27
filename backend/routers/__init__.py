# Routers package
from .config import router as config_router
from .execution import router as execution_router
from .sistemas import router as sistemas_router
from .credentials import router as credentials_router

__all__ = [
    "config_router",
    "execution_router",
    "sistemas_router",
    "credentials_router"
]
