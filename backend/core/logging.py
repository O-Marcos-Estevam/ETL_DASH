"""
Logging centralizado para o ETL Dashboard
"""
import logging
import sys
from typing import Optional


def setup_logging(
    level: str = "INFO",
    format_string: Optional[str] = None
) -> None:
    """
    Configura logging global da aplicacao.

    Args:
        level: Nivel de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_string: Formato customizado para logs
    """
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Converter string para nivel
    log_level = getattr(logging, level.upper(), logging.INFO)

    # Configurar root logger
    logging.basicConfig(
        level=log_level,
        format=format_string,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

    # Reduzir verbosidade de bibliotecas externas
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("websockets").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Retorna logger configurado para o modulo.

    Args:
        name: Nome do modulo (geralmente __name__)

    Returns:
        Logger configurado
    """
    return logging.getLogger(name)
