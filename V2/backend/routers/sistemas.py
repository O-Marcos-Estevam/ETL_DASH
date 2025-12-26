"""
Sistemas Router - Endpoints para gerenciamento de sistemas ETL
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Dict
import sys
import os

# Adicionar path para imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.sistema_service import get_sistema_service
from models.sistema import Sistema

router = APIRouter(prefix="/api/sistemas", tags=["sistemas"])


@router.get("", response_model=Dict[str, dict])
async def get_sistemas():
    """
    Retorna todos os sistemas disponiveis.

    Returns:
        Dict com todos os sistemas indexados por ID
    """
    service = get_sistema_service()
    return service.to_dict()


@router.get("/ativos", response_model=Dict[str, dict])
async def get_sistemas_ativos():
    """
    Retorna apenas os sistemas ativos.

    Returns:
        Dict com sistemas ativos indexados por ID
    """
    service = get_sistema_service()
    ativos = service.get_ativos()
    return {sys_id: sistema.model_dump() for sys_id, sistema in ativos.items()}


@router.get("/{sistema_id}")
async def get_sistema(sistema_id: str):
    """
    Retorna um sistema especifico pelo ID.

    Args:
        sistema_id: ID do sistema

    Returns:
        Sistema encontrado

    Raises:
        404: Sistema nao encontrado
    """
    service = get_sistema_service()
    sistema = service.get_by_id(sistema_id)

    if not sistema:
        raise HTTPException(
            status_code=404,
            detail=f"Sistema '{sistema_id}' nao encontrado"
        )

    return sistema.model_dump()


@router.patch("/{sistema_id}/toggle")
async def toggle_sistema(
    sistema_id: str,
    ativo: bool = Query(..., description="Novo estado do sistema")
):
    """
    Ativa ou desativa um sistema.

    Args:
        sistema_id: ID do sistema
        ativo: True para ativar, False para desativar

    Returns:
        Sistema atualizado

    Raises:
        404: Sistema nao encontrado
    """
    service = get_sistema_service()
    sistema = service.toggle(sistema_id, ativo)

    if not sistema:
        raise HTTPException(
            status_code=404,
            detail=f"Sistema '{sistema_id}' nao encontrado"
        )

    return {
        "status": "success",
        "message": f"Sistema {'ativado' if ativo else 'desativado'}",
        "sistema": sistema.model_dump()
    }


@router.patch("/{sistema_id}/opcao")
async def update_opcao(
    sistema_id: str,
    opcao: str = Query(..., description="Nome da opcao"),
    valor: bool = Query(..., description="Novo valor da opcao")
):
    """
    Atualiza uma opcao de um sistema.

    Args:
        sistema_id: ID do sistema
        opcao: Nome da opcao (csv, pdf, excel, etc)
        valor: Novo valor (True/False)

    Returns:
        Sistema atualizado

    Raises:
        404: Sistema nao encontrado
    """
    service = get_sistema_service()
    sistema = service.update_opcao(sistema_id, opcao, valor)

    if not sistema:
        raise HTTPException(
            status_code=404,
            detail=f"Sistema '{sistema_id}' nao encontrado"
        )

    return {
        "status": "success",
        "message": f"Opcao '{opcao}' atualizada para {valor}",
        "sistema": sistema.model_dump()
    }
