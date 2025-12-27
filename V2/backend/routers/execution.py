"""
Execution Router - Endpoints para execucao de pipelines ETL
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Dict, Optional
import logging
import sys
import os

# Adicionar path para imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database
from services.sistema_service import get_sistema_service
from services.background_worker import get_worker
from models.sistema import SistemaStatus

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

@router.post("/api/execute")
async def execute_pipeline(request: ExecuteRequest):
    """
    Enfileira execucao de um pipeline ETL completo.

    Args:
        request: Parametros de execucao (sistemas, datas, opcoes)

    Returns:
        Status e job_id do job enfileirado
    """
    try:
        # Validar que pelo menos um sistema foi selecionado
        if not request.sistemas:
            raise HTTPException(
                status_code=400,
                detail="Nenhum sistema selecionado para execucao"
            )

        # Verificar se ja existe job em execucao
        running_job = database.get_running_job()
        if running_job:
            return {
                "status": "error",
                "message": f"Ja existe um job em execucao (ID: {running_job['id']})",
                "job_id": running_job["id"]
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
async def execute_single_system(sistema_id: str, request: ExecuteSingleRequest):
    """
    Enfileira execucao de um sistema ETL individual.

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

        # Verificar se ja existe job em execucao
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
async def cancel_execution(job_id: int):
    """
    Cancela uma execucao em andamento.

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
        worker.cancel_current_job()

        # Atualizar status no banco
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

@router.get("/api/jobs")
async def list_jobs(
    status: Optional[str] = Query(None, description="Filtrar por status"),
    limit: int = Query(20, description="Limite de resultados"),
    offset: int = Query(0, description="Offset para paginacao")
):
    """
    Lista jobs de execucao.

    Args:
        status: Filtrar por status (pending, running, completed, error, cancelled)
        limit: Numero maximo de resultados
        offset: Offset para paginacao

    Returns:
        Lista de jobs
    """
    jobs = database.list_jobs(status=status, limit=limit, offset=offset)
    return {
        "jobs": jobs,
        "total": len(jobs),
        "limit": limit,
        "offset": offset
    }


@router.get("/api/jobs/{job_id}")
async def get_job_status(job_id: int):
    """
    Retorna status de um job especifico.

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
