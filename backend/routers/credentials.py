"""
Credentials Router - Endpoints para gerenciamento de credenciais

Protected endpoints requiring admin authentication.
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
import sys
import os

# Adicionar path para imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.credentials import get_config_service
from auth.dependencies import require_admin
from auth.models import UserInDB

router = APIRouter(prefix="/api", tags=["credentials"])


@router.get("/credentials")
async def get_credentials(current_user: UserInDB = Depends(require_admin)):
    """
    Retorna todas as credenciais (ADMIN ONLY).

    Nota: Senhas sao mascaradas por seguranca.

    Returns:
        Dict com todas as credenciais (senhas mascaradas)
    """
    service = get_config_service()
    # Retorna com senhas mascaradas para seguranca
    return service.get_credentials_masked()


@router.post("/credentials")
async def save_credentials(
    credentials: Dict[str, Any],
    current_user: UserInDB = Depends(require_admin)
):
    """
    Salva credenciais (ADMIN ONLY).

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
async def get_system_credentials(
    system_id: str,
    current_user: UserInDB = Depends(require_admin)
):
    """
    Retorna credenciais de um sistema especifico (ADMIN ONLY).

    Args:
        system_id: ID do sistema (ex: maps, amplis_reag)

    Returns:
        Credenciais do sistema (senhas mascaradas)

    Raises:
        404: Sistema nao encontrado
    """
    service = get_config_service()
    creds = service.get_system_credentials_masked(system_id)

    if creds is None:
        raise HTTPException(
            status_code=404,
            detail=f"Credenciais para '{system_id}' nao encontradas"
        )

    return creds


@router.get("/fundos")
async def get_fundos(
    system_id: str = None,
    current_user: UserInDB = Depends(require_admin)
):
    """
    Retorna configuracao de fundos (ADMIN ONLY).

    Args:
        system_id: (Opcional) Filtrar por sistema

    Returns:
        Dict com fundos configurados
    """
    service = get_config_service()
    return service.get_fundos(system_id)
