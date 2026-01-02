"""
Modelos de API para documentação OpenAPI
Esses modelos são usados para validação de request/response e geração de docs Swagger/ReDoc
"""
from pydantic import BaseModel, Field, RootModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ============================================
# Enums
# ============================================

class JobStatus(str, Enum):
    """Status possíveis de um job"""
    pending = "pending"
    running = "running"
    completed = "completed"
    error = "error"
    cancelled = "cancelled"


class SistemaStatus(str, Enum):
    """Status possíveis de um sistema"""
    idle = "idle"
    running = "running"
    success = "success"
    error = "error"


# ============================================
# Request Models
# ============================================

class ExecuteRequest(BaseModel):
    """Request para execução de pipeline ETL"""
    sistemas: List[str] = Field(
        ...,
        description="Lista de IDs dos sistemas a executar",
        example=["maps", "amplis_reag"]
    )
    data_inicial: Optional[str] = Field(
        None,
        description="Data inicial no formato YYYY-MM-DD ou DD/MM/YYYY",
        example="2024-01-01"
    )
    data_final: Optional[str] = Field(
        None,
        description="Data final no formato YYYY-MM-DD ou DD/MM/YYYY",
        example="2024-01-31"
    )
    limpar: bool = Field(
        False,
        description="Se True, limpa dados antes de importar"
    )
    dry_run: bool = Field(
        False,
        description="Se True, simula execução sem fazer alterações"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "sistemas": ["maps", "amplis_reag"],
                "data_inicial": "2024-01-01",
                "data_final": "2024-01-31",
                "limpar": False,
                "dry_run": False
            }
        }
    }


class ExecuteSingleRequest(BaseModel):
    """Request para execução de sistema único"""
    data_inicial: Optional[str] = Field(
        None,
        description="Data inicial",
        example="2024-01-01"
    )
    data_final: Optional[str] = Field(
        None,
        description="Data final",
        example="2024-01-31"
    )
    opcoes: Optional[Dict[str, Any]] = Field(
        None,
        description="Opções específicas do sistema"
    )


class CredentialsUpdateRequest(BaseModel):
    """Request para atualização de credenciais"""
    amplis: Optional[Dict[str, Any]] = Field(None, description="Credenciais AMPLIS")
    maps: Optional[Dict[str, Any]] = Field(None, description="Credenciais MAPS")
    fidc: Optional[Dict[str, Any]] = Field(None, description="Credenciais FIDC")
    qore: Optional[Dict[str, Any]] = Field(None, description="Credenciais QORE")
    britech: Optional[Dict[str, Any]] = Field(None, description="Credenciais BRITECH")
    paths: Optional[Dict[str, str]] = Field(None, description="Paths configurados")

    model_config = {
        "extra": "allow"  # Permite campos adicionais
    }


# ============================================
# Response Models
# ============================================

class HealthResponse(BaseModel):
    """Resposta do endpoint de health check"""
    status: str = Field(..., example="ok")
    version: str = Field(..., example="2.1.0")
    timestamp: Optional[str] = Field(None, example="2024-01-15T10:30:00Z")


class ExecuteResponse(BaseModel):
    """Resposta da execução de pipeline"""
    status: str = Field(..., example="queued")
    message: str = Field(..., example="Pipeline enfileirado com sucesso")
    job_id: int = Field(..., description="ID do job criado", example=1)

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "queued",
                "message": "Pipeline enfileirado com sucesso",
                "job_id": 1
            }
        }
    }


class JobResponse(BaseModel):
    """Detalhes de um job"""
    id: int = Field(..., example=1)
    type: str = Field(..., example="etl_pipeline")
    params: Optional[str] = Field(None, description="Parâmetros JSON do job")
    status: JobStatus = Field(..., example="running")
    logs: Optional[str] = Field(None, description="Logs de execução")
    error_message: Optional[str] = Field(None, description="Mensagem de erro se houver")
    created_at: Optional[str] = Field(None, example="2024-01-15T10:00:00")
    started_at: Optional[str] = Field(None, example="2024-01-15T10:00:05")
    finished_at: Optional[str] = Field(None, example="2024-01-15T10:05:00")


class JobListResponse(BaseModel):
    """Lista de jobs"""
    jobs: List[JobResponse] = Field(..., description="Lista de jobs")
    total: Optional[int] = Field(None, description="Total de jobs")
    page: Optional[int] = Field(None, description="Página atual")
    limit: Optional[int] = Field(None, description="Limite por página")


class SistemaOpcoes(BaseModel):
    """Opções de um sistema"""
    csv: Optional[bool] = Field(None, description="Exportar CSV")
    pdf: Optional[bool] = Field(None, description="Exportar PDF")
    excel: Optional[bool] = Field(None, description="Exportar Excel")

    model_config = {
        "extra": "allow"
    }


class SistemaResponse(BaseModel):
    """Detalhes de um sistema ETL"""
    id: str = Field(..., example="maps")
    nome: str = Field(..., example="MAPS")
    descricao: Optional[str] = Field(None, example="Upload de dados MAPS")
    icone: Optional[str] = Field(None, example="Map")
    ordem: Optional[int] = Field(None, example=1)
    ativo: bool = Field(..., example=True)
    status: Optional[SistemaStatus] = Field(None, example="idle")
    opcoes: Optional[SistemaOpcoes] = Field(None)
    mensagem: Optional[str] = Field(None, description="Mensagem de status atual")


class SistemasListResponse(RootModel[Dict[str, SistemaResponse]]):
    """Lista de sistemas"""

    model_config = {
        "json_schema_extra": {
            "example": {
                "maps": {
                    "id": "maps",
                    "nome": "MAPS",
                    "ativo": True,
                    "status": "idle"
                }
            }
        }
    }


class ToggleResponse(BaseModel):
    """Resposta de toggle de sistema"""
    status: str = Field(..., example="success")
    message: str = Field(..., example="Sistema ativado")
    sistema: SistemaResponse


class OpcaoUpdateResponse(BaseModel):
    """Resposta de atualização de opção"""
    status: str = Field(..., example="success")
    message: str = Field(..., example="Opção 'pdf' atualizada para True")
    sistema: SistemaResponse


class CredentialsResponse(BaseModel):
    """Credenciais mascaradas"""
    version: Optional[str] = Field(None, example="2.0")
    amplis: Optional[Dict[str, Any]] = Field(None)
    maps: Optional[Dict[str, Any]] = Field(None)
    fidc: Optional[Dict[str, Any]] = Field(None)
    qore: Optional[Dict[str, Any]] = Field(None)
    britech: Optional[Dict[str, Any]] = Field(None)
    paths: Optional[Dict[str, str]] = Field(None)

    model_config = {
        "extra": "allow"
    }


class SaveCredentialsResponse(BaseModel):
    """Resposta de salvamento de credenciais"""
    status: str = Field(..., example="success")
    message: str = Field(..., example="Credenciais salvas com sucesso")


class CancelResponse(BaseModel):
    """Resposta de cancelamento de job"""
    status: str = Field(..., example="success")
    message: str = Field(..., example="Job cancelado com sucesso")
    job_id: int = Field(..., example=1)


# ============================================
# Error Models
# ============================================

class ErrorResponse(BaseModel):
    """Resposta de erro padrão"""
    detail: str = Field(..., example="Recurso não encontrado")

    model_config = {
        "json_schema_extra": {
            "example": {
                "detail": "Sistema 'invalid' não encontrado"
            }
        }
    }


class ValidationErrorResponse(BaseModel):
    """Resposta de erro de validação"""
    detail: List[Dict[str, Any]] = Field(
        ...,
        example=[{"loc": ["body", "sistemas"], "msg": "field required", "type": "value_error.missing"}]
    )


class RateLimitResponse(BaseModel):
    """Resposta de rate limit excedido"""
    detail: str = Field(..., example="Rate limit excedido. Tente novamente em 60 segundos.")
    retry_after: Optional[int] = Field(None, example=60)
