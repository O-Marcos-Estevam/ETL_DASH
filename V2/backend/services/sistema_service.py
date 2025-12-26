"""
Sistema Service - Gerencia estado dos sistemas ETL
"""
import json
import os
import sys
from typing import Dict, Optional, List

# Garantir que o diretorio backend esta no path
_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from models.sistema import Sistema, SistemaStatus, SISTEMAS_METADATA


class SistemaService:
    """Servico para gerenciar sistemas ETL"""

    # Caminho para persistir estado dos sistemas
    STATE_FILE = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "config", "sistemas_state.json")
    )

    def __init__(self):
        self._sistemas: Dict[str, Sistema] = {}
        self._load_state()

    def _load_state(self):
        """Carrega estado dos sistemas do arquivo ou inicializa com defaults"""
        saved_state = {}

        # Tentar carregar estado salvo
        if os.path.exists(self.STATE_FILE):
            try:
                with open(self.STATE_FILE, "r", encoding="utf-8") as f:
                    saved_state = json.load(f)
            except Exception:
                saved_state = {}

        # Inicializar sistemas com metadata + estado salvo
        for sys_id, meta in SISTEMAS_METADATA.items():
            saved = saved_state.get(sys_id, {})

            self._sistemas[sys_id] = Sistema(
                id=sys_id,
                nome=meta["nome"],
                descricao=meta["descricao"],
                icone=meta["icone"],
                ordem=meta["ordem"],
                opcoes=saved.get("opcoes", meta.get("opcoes", {})),
                ativo=saved.get("ativo", True),
                status=SistemaStatus.IDLE,
                progresso=0,
                mensagem=None
            )

    def _save_state(self):
        """Persiste estado dos sistemas"""
        state = {}
        for sys_id, sistema in self._sistemas.items():
            state[sys_id] = {
                "ativo": sistema.ativo,
                "opcoes": sistema.opcoes
            }

        # Criar diretorio se nao existir
        os.makedirs(os.path.dirname(self.STATE_FILE), exist_ok=True)

        with open(self.STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)

    def get_all(self) -> Dict[str, Sistema]:
        """Retorna todos os sistemas"""
        return self._sistemas

    def get_by_id(self, sistema_id: str) -> Optional[Sistema]:
        """Retorna sistema por ID"""
        return self._sistemas.get(sistema_id)

    def get_ativos(self) -> Dict[str, Sistema]:
        """Retorna apenas sistemas ativos"""
        return {
            sys_id: sistema
            for sys_id, sistema in self._sistemas.items()
            if sistema.ativo
        }

    def get_ativos_ids(self) -> List[str]:
        """Retorna lista de IDs de sistemas ativos"""
        return [sys_id for sys_id, sistema in self._sistemas.items() if sistema.ativo]

    def toggle(self, sistema_id: str, ativo: bool) -> Optional[Sistema]:
        """Ativa ou desativa um sistema"""
        sistema = self._sistemas.get(sistema_id)
        if sistema:
            sistema.ativo = ativo
            self._save_state()
        return sistema

    def update_opcao(self, sistema_id: str, opcao: str, valor: bool) -> Optional[Sistema]:
        """Atualiza uma opcao do sistema"""
        sistema = self._sistemas.get(sistema_id)
        if sistema:
            sistema.opcoes[opcao] = valor
            self._save_state()
        return sistema

    def update_status(self, sistema_id: str, status: SistemaStatus,
                      progresso: int = 0, mensagem: str = None) -> Optional[Sistema]:
        """Atualiza status de execucao do sistema"""
        sistema = self._sistemas.get(sistema_id)
        if sistema:
            sistema.status = status
            sistema.progresso = progresso
            sistema.mensagem = mensagem
        return sistema

    def reset_all_status(self):
        """Reseta status de todos os sistemas para IDLE"""
        for sistema in self._sistemas.values():
            sistema.status = SistemaStatus.IDLE
            sistema.progresso = 0
            sistema.mensagem = None

    def to_dict(self) -> Dict[str, dict]:
        """Converte todos os sistemas para dict"""
        return {
            sys_id: sistema.model_dump()
            for sys_id, sistema in self._sistemas.items()
        }


# Instancia singleton
_instance: Optional[SistemaService] = None

def get_sistema_service() -> SistemaService:
    """Retorna instancia singleton do SistemaService"""
    global _instance
    if _instance is None:
        _instance = SistemaService()
    return _instance
