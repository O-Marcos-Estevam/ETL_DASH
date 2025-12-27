"""
Sistema Model - Representa um sistema ETL
"""
from pydantic import BaseModel
from typing import Dict, Optional
from enum import Enum


class SistemaStatus(str, Enum):
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"
    CANCELLED = "CANCELLED"


class SistemaOpcoes(BaseModel):
    """Opcoes configuracveis por sistema"""
    csv: Optional[bool] = None
    pdf: Optional[bool] = None
    excel: Optional[bool] = None
    ativo: Optional[bool] = None
    passivo: Optional[bool] = None
    lote_pdf: Optional[bool] = None
    lote_excel: Optional[bool] = None

    class Config:
        extra = "allow"  # Permite opcoes extras


class Sistema(BaseModel):
    """Modelo de Sistema ETL"""
    id: str
    nome: str
    descricao: str
    icone: str
    ativo: bool = True
    ordem: int = 0
    opcoes: Dict[str, bool] = {}
    status: SistemaStatus = SistemaStatus.IDLE
    progresso: int = 0
    mensagem: Optional[str] = None

    class Config:
        use_enum_values = True


# Metadata estatico dos sistemas disponiveis
SISTEMAS_METADATA: Dict[str, dict] = {
    "amplis_reag": {
        "nome": "AMPLIS (REAG)",
        "descricao": "Importacao de dados do AMPLIS (REAG)",
        "icone": "BarChart3",
        "ordem": 1,
        "opcoes": {"csv": True, "pdf": True}
    },
    "amplis_master": {
        "nome": "AMPLIS (Master)",
        "descricao": "Importacao de dados do AMPLIS (Master)",
        "icone": "BarChart3",
        "ordem": 2,
        "opcoes": {"csv": True, "pdf": True}
    },
    "maps": {
        "nome": "MAPS",
        "descricao": "Upload e Processamento MAPS",
        "icone": "Map",
        "ordem": 3,
        "opcoes": {"excel": True, "pdf": True, "ativo": True, "passivo": True}
    },
    "fidc": {
        "nome": "FIDC",
        "descricao": "Gestao de Direitos Creditorios",
        "icone": "FileSpreadsheet",
        "ordem": 4,
        "opcoes": {}
    },
    "jcot": {
        "nome": "JCOT",
        "descricao": "Integracao JCOT",
        "icone": "Database",
        "ordem": 5,
        "opcoes": {}
    },
    "britech": {
        "nome": "BRITECH",
        "descricao": "Integracao BRITECH",
        "icone": "Server",
        "ordem": 6,
        "opcoes": {}
    },
    "qore": {
        "nome": "QORE",
        "descricao": "Processamento XML QORE",
        "icone": "FileCode",
        "ordem": 7,
        "opcoes": {"excel": True, "pdf": True, "lote_pdf": False, "lote_excel": False}
    },
    "trustee": {
        "nome": "TRUSTEE",
        "descricao": "Automacao TRUSTEE",
        "icone": "Shield",
        "ordem": 8,
        "opcoes": {}
    }
}
