"""
Config Model - Configuracao ETL
"""
from pydantic import BaseModel
from typing import Dict, Optional, Any
from datetime import datetime


class Periodo(BaseModel):
    """Periodo de execucao"""
    dataInicial: Optional[str] = None
    dataFinal: Optional[str] = None
    usarD1Anbima: bool = True


class ConfiguracaoETL(BaseModel):
    """Configuracao principal do ETL"""
    versao: str = "2.0"
    ultimaModificacao: Optional[str] = None
    periodo: Periodo = Periodo()
    sistemas: Dict[str, Any] = {}

    class Config:
        extra = "allow"  # Permite campos extras como credenciais
