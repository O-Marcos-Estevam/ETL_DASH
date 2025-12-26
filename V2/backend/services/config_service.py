"""
Config Service - Gerencia configuracoes e credenciais
"""
import json
import os
from typing import Dict, Any, Optional
from datetime import datetime


class ConfigService:
    """Servico para gerenciar configuracoes ETL"""

    # Caminho do arquivo de credenciais
    CREDENTIALS_PATH = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "config", "credentials.json")
    )

    def __init__(self):
        self._credentials: Dict[str, Any] = {}
        self._load_credentials()

    def _load_credentials(self):
        """Carrega credenciais do arquivo"""
        if os.path.exists(self.CREDENTIALS_PATH):
            try:
                with open(self.CREDENTIALS_PATH, "r", encoding="utf-8") as f:
                    self._credentials = json.load(f)
            except Exception as e:
                print(f"Erro ao carregar credentials.json: {e}")
                self._credentials = {}
        else:
            self._credentials = self._get_default_credentials()

    def _get_default_credentials(self) -> Dict[str, Any]:
        """Retorna estrutura padrao de credenciais"""
        return {
            "version": "2.0",
            "amplis": {
                "reag": {"url": "", "username": "", "password": ""},
                "master": {"url": "", "username": "", "password": ""}
            },
            "maps": {"url": "", "username": "", "password": "", "fundos": [], "usar_todos": True, "fundos_selecionados": []},
            "fidc": {"url": "", "username": "", "password": "", "fundos": [], "usar_todos": True, "fundos_selecionados": []},
            "jcot": {"url": "", "username": "", "password": ""},
            "britech": {"url": "", "username": "", "password": ""},
            "qore": {"url": "", "username": "", "password": "", "fundos": [], "usar_todos": True, "fundos_selecionados": []},
            "paths": {
                "csv": "",
                "pdf": "",
                "maps": "",
                "fidc": "",
                "jcot": "",
                "britech": "",
                "qore_excel": "",
                "qore_pdf": "",
                "bd_xlsx": "",
                "trustee": "",
                "selenium_temp": ""
            },
            "fundos": {"selecionados": []}
        }

    def _save_credentials(self):
        """Salva credenciais no arquivo"""
        # Criar diretorio se nao existir
        os.makedirs(os.path.dirname(self.CREDENTIALS_PATH), exist_ok=True)

        with open(self.CREDENTIALS_PATH, "w", encoding="utf-8") as f:
            json.dump(self._credentials, f, indent=4, ensure_ascii=False)

    def get_credentials(self) -> Dict[str, Any]:
        """Retorna todas as credenciais"""
        return self._credentials.copy()

    def get_credentials_masked(self) -> Dict[str, Any]:
        """Retorna credenciais com senhas mascaradas"""
        return self._mask_passwords(self._credentials.copy())

    def _mask_passwords(self, obj: Any, depth: int = 0) -> Any:
        """Mascara campos de senha recursivamente"""
        if depth > 10:  # Prevenir recursao infinita
            return obj

        if isinstance(obj, dict):
            masked = {}
            for key, value in obj.items():
                if key.lower() in ["password", "senha", "secret", "token"]:
                    masked[key] = "********" if value else ""
                else:
                    masked[key] = self._mask_passwords(value, depth + 1)
            return masked
        elif isinstance(obj, list):
            return [self._mask_passwords(item, depth + 1) for item in obj]
        else:
            return obj

    def save_credentials(self, credentials: Dict[str, Any]) -> bool:
        """Salva credenciais (merge com existentes para preservar senhas nao alteradas)"""
        try:
            # Fazer merge para preservar senhas que vieram mascaradas
            merged = self._merge_credentials(self._credentials, credentials)
            self._credentials = merged
            self._save_credentials()
            return True
        except Exception as e:
            print(f"Erro ao salvar credenciais: {e}")
            return False

    def _merge_credentials(self, existing: Dict, new: Dict, depth: int = 0) -> Dict:
        """Merge credenciais preservando senhas mascaradas"""
        if depth > 10:
            return new

        result = existing.copy()

        for key, value in new.items():
            if key.lower() in ["password", "senha", "secret", "token"]:
                # So atualiza se nao for mascara
                if value and value != "********":
                    result[key] = value
            elif isinstance(value, dict) and key in result and isinstance(result[key], dict):
                result[key] = self._merge_credentials(result[key], value, depth + 1)
            else:
                result[key] = value

        return result

    def get_paths(self) -> Dict[str, str]:
        """Retorna configuracao de paths"""
        return self._credentials.get("paths", {})

    def get_system_credentials(self, system_id: str) -> Optional[Dict[str, Any]]:
        """Retorna credenciais de um sistema especifico"""
        # Mapear IDs compostos (amplis_reag -> amplis.reag)
        if "_" in system_id:
            parts = system_id.split("_", 1)
            parent = self._credentials.get(parts[0], {})
            if isinstance(parent, dict):
                return parent.get(parts[1])

        return self._credentials.get(system_id)

    def get_fundos(self, system_id: str = None) -> Dict[str, Any]:
        """Retorna configuracao de fundos"""
        fundos = self._credentials.get("fundos", {})
        if system_id:
            return fundos.get(system_id, {})
        return fundos

    def reload(self):
        """Recarrega credenciais do arquivo"""
        self._load_credentials()


# Instancia singleton
_instance: Optional[ConfigService] = None

def get_config_service() -> ConfigService:
    """Retorna instancia singleton do ConfigService"""
    global _instance
    if _instance is None:
        _instance = ConfigService()
    return _instance
