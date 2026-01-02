"""
Config Router - Endpoints para configuracao ETL

GET config available for viewers, POST requires admin.
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
import json
import os
import sys
from datetime import datetime

# Garantir que o diretorio backend esta no path
_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from services.sistemas import get_sistema_service
from services.credentials import get_config_service
from auth.dependencies import require_admin, require_viewer
from auth.models import UserInDB

router = APIRouter(tags=["config"])

# Caminho do credentials.json
CONFIG_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "config", "credentials.json")
)


@router.get("/api/config")
async def get_config(current_user: UserInDB = Depends(require_viewer)):
    """
    Retorna configuracao completa do ETL (ADMIN e VIEWER).

    Combina:
    - Metadata dos sistemas (do SistemaService)
    - Credenciais (do ConfigService) - senhas mascaradas para viewer
    - Periodo padrao

    Returns:
        Objeto hibrido com sistemas + credenciais para compatibilidade com frontend
    """
    try:
        # Obter servicos
        sistema_service = get_sistema_service()
        config_service = get_config_service()

        # Obter credenciais raw (para Settings form)
        creds = config_service.get_credentials()

        # Construir response hibrida
        response = creds.copy()

        # Adicionar sistemas do SistemaService
        response["sistemas"] = sistema_service.to_dict()

        # Adicionar periodo padrao
        response["periodo"] = {
            "dataInicial": None,
            "dataFinal": None,
            "usarD1Anbima": True
        }

        # Adicionar metadata
        response["versao"] = creds.get("version", "2.0")
        response["ultimaModificacao"] = datetime.now().isoformat()

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao carregar config: {str(e)}")


@router.post("/api/config")
async def update_config(
    config: Dict[str, Any],
    current_user: UserInDB = Depends(require_admin)
):
    """
    Atualiza configuracao (ADMIN ONLY).

    Salva credenciais no credentials.json (excluindo campos de metadata).
    Atualiza estado dos sistemas no SistemaService.

    Args:
        config: Objeto de configuracao

    Returns:
        Status da operacao
    """
    try:
        config_service = get_config_service()
        sistema_service = get_sistema_service()

        # Separar dados
        sistemas_data = config.pop("sistemas", None)
        config.pop("periodo", None)
        config.pop("ultimaModificacao", None)
        config.pop("versao", None)

        # Salvar credenciais
        config["version"] = config.get("version", "2.0")
        success = config_service.save_credentials(config)

        if not success:
            raise HTTPException(status_code=500, detail="Erro ao salvar credenciais")

        # Atualizar estado dos sistemas se fornecido
        if sistemas_data:
            for sys_id, sys_data in sistemas_data.items():
                if isinstance(sys_data, dict):
                    # Atualizar ativo/opcoes
                    if "ativo" in sys_data:
                        sistema_service.toggle(sys_id, sys_data["ativo"])
                    if "opcoes" in sys_data:
                        for opcao, valor in sys_data["opcoes"].items():
                            sistema_service.update_opcao(sys_id, opcao, valor)

        return {"status": "success", "message": "Configuracao salva com sucesso"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao salvar config: {str(e)}")


@router.get("/api/config/paths")
async def get_paths(current_user: UserInDB = Depends(require_viewer)):
    """
    Retorna configuracao de paths (ADMIN e VIEWER).

    Returns:
        Dict com paths configurados
    """
    config_service = get_config_service()
    return config_service.get_paths()
