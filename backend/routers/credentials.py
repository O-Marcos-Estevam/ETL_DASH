"""
Credentials Router - Endpoints para gerenciamento de credenciais
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import sys
import os

# Adicionar path para imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.credentials import get_config_service

router = APIRouter(prefix="/api", tags=["credentials"])


@router.get("/credentials")
async def get_credentials():
    """
    Retorna todas as credenciais.

    Nota: Senhas sao mascaradas por seguranca.
    Para ver senhas reais, use o arquivo credentials.json diretamente.

    Returns:
        Dict com todas as credenciais (senhas mascaradas)
    """
    service = get_config_service()
    # Retorna com senhas mascaradas para seguranca
    return service.get_credentials_masked()


@router.post("/credentials")
async def save_credentials(credentials: Dict[str, Any]):
    """
    Salva credenciais.

    Campos de senha com valor "********" serao ignorados
    (preserva valor existente).

    Args:
        credentials: Objeto com credenciais a salvar

    Returns:
        Status da operacao
    """
    service = get_config_service()
    success = service.save_credentials(credentials)

    if not success:
        raise HTTPException(
            status_code=500,
            detail="Erro ao salvar credenciais"
        )

    return {
        "status": "success",
        "message": "Credenciais salvas com sucesso"
    }


@router.get("/credentials/{system_id}")
async def get_system_credentials(system_id: str):
    """
    Retorna credenciais de um sistema especifico.

    Args:
        system_id: ID do sistema (ex: maps, amplis_reag)

    Returns:
        Credenciais do sistema (senhas mascaradas)

    Raises:
        404: Sistema nao encontrado
    """
    service = get_config_service()
    creds = service.get_system_credentials(system_id)

    if creds is None:
        raise HTTPException(
            status_code=404,
            detail=f"Credenciais para '{system_id}' nao encontradas"
        )

    # Mascarar senhas
    return service._mask_passwords(creds)


@router.get("/fundos")
async def get_fundos(system_id: str = None):
    """
    Retorna configuracao de fundos.

    Args:
        system_id: (Opcional) Filtrar por sistema

    Returns:
        Dict com fundos configurados
    """
    service = get_config_service()
    return service.get_fundos(system_id)
