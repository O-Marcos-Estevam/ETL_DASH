"""
Job Model - Representa um job de execucao ETL
"""
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from enum import Enum
from datetime import datetime


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    ERROR = "error"
    CANCELLED = "cancelled"


class JobParams(BaseModel):
    """Parametros do job"""
    sistemas: List[str] = []
    dry_run: bool = False
    limpar: bool = False
    data_inicial: Optional[str] = None
    data_final: Optional[str] = None
    opcoes: Dict[str, Dict[str, bool]] = {}


class Job(BaseModel):
    """Modelo de Job ETL"""
    id: int
    type: str
    params: Optional[JobParams] = None
    status: JobStatus = JobStatus.PENDING
    logs: str = ""
    error_message: Optional[str] = None
    created_at: Optional[str] = None
    started_at: Optional[str] = None
    finished_at: Optional[str] = None

    class Config:
        use_enum_values = True
