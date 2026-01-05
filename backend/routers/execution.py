"""
Execution Router - Endpoints para execucao de pipelines ETL

Execute and cancel require admin, list/get jobs available for viewers.
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel
from typing import List, Dict, Optional
import logging
import sys
import os

# Adicionar path para imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import database
from services.sistemas import get_sistema_service
from services.worker import get_worker
from models.sistema import SistemaStatus
from models.api import (
    ExecuteResponse,
    JobListResponse,
    CancelResponse,
    ErrorResponse
)
from auth.dependencies import require_admin, require_viewer
from auth.models import UserInDB

logger = logging.getLogger("uvicorn.error")

router = APIRouter(tags=["execution"])


class ExecuteRequest(BaseModel):
    """Request para executar pipeline"""
    sistemas: List[str]
    dry_run: bool = False
    limpar: bool = False
    data_inicial: Optional[str] = None
    data_final: Optional[str] = None
    opcoes: Dict[str, Dict[str, bool]] = {}


class ExecuteSingleRequest(BaseModel):
    """Request para executar sistema individual"""
    dry_run: bool = False
    limpar: bool = False
    data_inicial: Optional[str] = None
    data_final: Optional[str] = None
    opcoes: Dict[str, bool] = {}


# ==================== EXECUCAO ====================

@router.post(
    "/api/execute",
    response_model=ExecuteResponse,
    summary="Executar Pipeline ETL",
    responses={
        400: {"model": ErrorResponse, "description": "Nenhum sistema selecionado"},
        500: {"model": ErrorResponse, "description": "Erro interno"}
    }
)
async def execute_pipeline(
    request: ExecuteRequest,
    current_user: UserInDB = Depends(require_admin)
):
    """
    Enfileira execucao de um pipeline ETL completo (ADMIN ONLY).

    - **sistemas**: Lista de IDs dos sistemas a executar
    - **data_inicial**: Data inicial (YYYY-MM-DD)
    - **data_final**: Data final (YYYY-MM-DD)
    - **dry_run**: Se True, simula execução
    """
    try:
        # Validar que pelo menos um sistema foi selecionado
        if not request.sistemas:
            raise HTTPException(
                status_code=400,
                detail="Nenhum sistema selecionado para execucao"
            )

        # In pool mode, check if there's an available slot
        # In single mode, check if there's any running job
        from config import settings

        if settings.MAX_CONCURRENT_JOBS == 1:
            running_job = database.get_running_job()
            if running_job:
                return {
                    "status": "error",
                    "message": f"Ja existe um job em execucao (ID: {running_job['id']})",
                    "job_id": running_job["id"]
                }
        else:
            # Pool mode - check if all slots are busy
            running_count = database.get_running_jobs_count()
            if running_count >= settings.MAX_CONCURRENT_JOBS:
                return {
                    "status": "queued",
                    "message": f"Todos os {settings.MAX_CONCURRENT_JOBS} slots estao ocupados. Job sera enfileirado.",
                    "job_id": -1  # Will be set after creation
                }

        # Criar job no banco
        job_id = database.add_job("etl_pipeline", request.model_dump())

        logger.info(f"Pipeline enfileirado: job_id={job_id}, sistemas={request.sistemas}")

        # Atualizar status dos sistemas para RUNNING
        service = get_sistema_service()
        for sistema_id in request.sistemas:
            service.update_status(sistema_id, SistemaStatus.RUNNING, 0, "Aguardando execucao...")

        return {
            "status": "started",
            "message": "Pipeline ETL enfileirado com sucesso",
            "job_id": job_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao enfileirar pipeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/execute/{sistema_id}")
async def execute_single_system(
    sistema_id: str,
    request: ExecuteSingleRequest,
    current_user: UserInDB = Depends(require_admin)
):
    """
    Enfileira execucao de um sistema ETL individual (ADMIN ONLY).

    Args:
        sistema_id: ID do sistema a executar
        request: Parametros de execucao

    Returns:
        Status e job_id do job enfileirado
    """
    try:
        # Verificar se sistema existe
        service = get_sistema_service()
        sistema = service.get_by_id(sistema_id)

        if not sistema:
            raise HTTPException(
                status_code=404,
                detail=f"Sistema '{sistema_id}' nao encontrado"
            )

        # Check for running jobs (same logic as execute_pipeline)
        from config import settings

        if settings.MAX_CONCURRENT_JOBS == 1:
            running_job = database.get_running_job()
            if running_job:
                return {
                    "status": "error",
                    "message": f"Ja existe um job em execucao (ID: {running_job['id']})",
                    "job_id": running_job["id"]
                }

        # Criar parametros do job
        params = {
            "sistemas": [sistema_id],
            "dry_run": request.dry_run,
            "limpar": request.limpar,
            "data_inicial": request.data_inicial,
            "data_final": request.data_final,
            "opcoes": {sistema_id: request.opcoes}
        }

        # Criar job no banco
        job_id = database.add_job("etl_single", params)

        logger.info(f"Sistema enfileirado: job_id={job_id}, sistema={sistema_id}")

        # Atualizar status do sistema
        service.update_status(sistema_id, SistemaStatus.RUNNING, 0, "Aguardando execucao...")

        return {
            "status": "started",
            "message": f"Sistema '{sistema_id}' enfileirado para execucao",
            "job_id": job_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao enfileirar sistema: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/cancel/{job_id}")
async def cancel_execution(
    job_id: int,
    current_user: UserInDB = Depends(require_admin)
):
    """
    Cancela uma execucao em andamento (ADMIN ONLY).

    Args:
        job_id: ID do job a cancelar

    Returns:
        Status da operacao
    """
    try:
        # Buscar job
        job = database.get_job(job_id)

        if not job:
            raise HTTPException(
                status_code=404,
                detail=f"Job {job_id} nao encontrado"
            )

        # Verificar se pode ser cancelado
        if job["status"] not in ["pending", "running"]:
            return {
                "status": "error",
                "message": f"Job {job_id} nao pode ser cancelado (status: {job['status']})"
            }

        # Cancelar processo em execucao via worker
        worker = get_worker()
        cancelled = worker.cancel_job(job_id)

        if not cancelled:
            # Job might not be running yet (still pending)
            if job["status"] == "pending":
                database.update_job_status(job_id, "cancelled", "Cancelado antes de iniciar")
            else:
                # Job not found in worker - update status anyway
                database.update_job_status(job_id, "cancelled", "Cancelado pelo usuario")
        else:
            # Worker handled the cancellation
            database.update_job_status(job_id, "cancelled", "Cancelado pelo usuario")

        # Atualizar status dos sistemas
        service = get_sistema_service()
        service.reset_all_status()

        logger.info(f"Job {job_id} cancelado pelo usuario")

        return {
            "status": "success",
            "message": f"Job {job_id} cancelado com sucesso"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao cancelar job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== JOBS ====================

@router.get(
    "/api/jobs",
    response_model=JobListResponse,
    summary="Listar Jobs",
    description="Lista todos os jobs de execução com suporte a filtros e paginação."
)
async def list_jobs(
    status: Optional[str] = Query(None, description="Filtrar por status (pending, running, completed, error, cancelled)"),
    limit: int = Query(20, ge=1, le=100, description="Limite de resultados"),
    offset: int = Query(0, ge=0, description="Offset para paginacao"),
    current_user: UserInDB = Depends(require_viewer)
):
    """
    Lista jobs de execucao (ADMIN e VIEWER).

    Suporta filtros por status e paginação.
    """
    jobs = database.list_jobs(status=status, limit=limit, offset=offset)
    return {
        "jobs": jobs,
        "total": len(jobs),
        "limit": limit,
        "offset": offset
    }


@router.get("/api/jobs/{job_id}")
async def get_job_status(
    job_id: int,
    current_user: UserInDB = Depends(require_viewer)
):
    """
    Retorna status de um job especifico (ADMIN e VIEWER).

    Args:
        job_id: ID do job

    Returns:
        Detalhes do job

    Raises:
        404: Job nao encontrado
    """
    job = database.get_job(job_id)

    if not job:
        raise HTTPException(
            status_code=404,
            detail=f"Job {job_id} nao encontrado"
        )

    return job


# ==================== POOL/WORKER STATUS ====================

@router.get("/api/pool/status")
async def get_pool_status(current_user: UserInDB = Depends(require_viewer)):
    """
    Returns status of the worker/pool (ADMIN and VIEWER).

    In single mode: returns current job info
    In pool mode: returns all slot statuses
    """
    worker = get_worker()
    return worker.get_status()


@router.get("/api/pool/metrics")
async def get_pool_metrics(current_user: UserInDB = Depends(require_viewer)):
    """
    Returns execution metrics (ADMIN and VIEWER).

    Includes:
    - Worker mode (single/pool)
    - Slots info (if pool mode)
    - Queue depth
    - Completed jobs in last 24h
    """
    from config import settings

    worker = get_worker()
    worker_status = worker.get_status()

    metrics = {
        "mode": worker_status.get("mode", "single"),
        "max_concurrent_jobs": settings.MAX_CONCURRENT_JOBS,
        "jobs_pending": database.get_pending_jobs_count(),
        "jobs_running": database.get_running_jobs_count(),
        "jobs_completed_24h": database.get_completed_jobs_count(hours=24),
    }

    # Add pool-specific metrics if in pool mode
    if worker_status.get("mode") == "pool":
        metrics["slots_active"] = worker_status.get("active_count", 0)
        metrics["slots_idle"] = worker_status.get("idle_count", 0)
        metrics["slots"] = worker_status.get("slots", [])

    return metrics
