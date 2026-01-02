"""
Testes unitarios para ConfigService (credentials)
"""
import pytest
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.credentials import ConfigService


class TestMaskPasswords:
    """Testes para _mask_passwords"""

    @pytest.fixture
    def service(self):
        """Fixture do service com mock do arquivo"""
        with patch.object(ConfigService, '_load_credentials'):
            service = ConfigService()
            service._credentials = {}
            return service

    def test_mask_password_field(self, service):
        """Mascara campo password"""
        data = {"username": "user", "password": "secret123"}
        result = service._mask_passwords(data)
        assert result["username"] == "user"
        assert result["password"] == "********"

    def test_mask_senha_field(self, service):
        """Mascara campo senha"""
        data = {"usuario": "admin", "senha": "minhasenha"}
        result = service._mask_passwords(data)
        assert result["senha"] == "********"

    def test_mask_secret_field(self, service):
        """Mascara campo secret"""
        data = {"api_key": "key", "secret": "top_secret"}
        result = service._mask_passwords(data)
        assert result["secret"] == "********"

    def test_mask_token_field(self, service):
        """Mascara campo token"""
        data = {"user_id": 1, "token": "jwt_token_here"}
        result = service._mask_passwords(data)
        assert result["token"] == "********"

    def test_mask_empty_password(self, service):
        """Password vazio vira string vazia"""
        data = {"password": ""}
        result = service._mask_passwords(data)
        assert result["password"] == ""

    def test_mask_nested_dict(self, service):
        """Mascara em dicts aninhados"""
        data = {
            "amplis": {
                "reag": {"username": "user", "password": "pass1"},
                "master": {"username": "admin", "password": "pass2"}
            }
        }
        result = service._mask_passwords(data)
        assert result["amplis"]["reag"]["username"] == "user"
        assert result["amplis"]["reag"]["password"] == "********"
        assert result["amplis"]["master"]["password"] == "********"

    def test_mask_list_of_dicts(self, service):
        """Mascara em lista de dicts"""
        data = {
            "users": [
                {"name": "Alice", "password": "alice123"},
                {"name": "Bob", "password": "bob456"}
            ]
        }
        result = service._mask_passwords(data)
        assert result["users"][0]["name"] == "Alice"
        assert result["users"][0]["password"] == "********"
        assert result["users"][1]["password"] == "********"

    def test_mask_depth_limit(self, service):
        """Respeita limite de profundidade"""
        # Criar estrutura muito aninhada
        deep = {"level": 0}
        current = deep
        for i in range(15):
            current["nested"] = {"level": i + 1, "password": "secret"}
            current = current["nested"]

        result = service._mask_passwords(deep)
        # Deve funcionar sem erro (limite de 10 niveis)
        assert isinstance(result, dict)

    def test_mask_preserves_non_sensitive(self, service):
        """Preserva campos nao sensiveis"""
        data = {
            "url": "https://api.test.com",
            "port": 8080,
            "enabled": True,
            "tags": ["prod", "api"],
            "password": "secret"
        }
        result = service._mask_passwords(data)
        assert result["url"] == "https://api.test.com"
        assert result["port"] == 8080
        assert result["enabled"] is True
        assert result["tags"] == ["prod", "api"]
        assert result["password"] == "********"


class TestMergeCredentials:
    """Testes para _merge_credentials"""

    @pytest.fixture
    def service(self):
        """Fixture do service"""
        with patch.object(ConfigService, '_load_credentials'):
            service = ConfigService()
            service._credentials = {}
            return service

    def test_merge_preserves_masked_password(self, service):
        """Merge preserva senha quando vem mascarada"""
        existing = {"username": "user", "password": "real_password"}
        new = {"username": "new_user", "password": "********"}
        result = service._merge_credentials(existing, new)
        assert result["username"] == "new_user"
        assert result["password"] == "real_password"  # Preservada

    def test_merge_updates_real_password(self, service):
        """Merge atualiza senha real"""
        existing = {"username": "user", "password": "old_password"}
        new = {"username": "user", "password": "new_password"}
        result = service._merge_credentials(existing, new)
        assert result["password"] == "new_password"

    def test_merge_nested_dicts(self, service):
        """Merge recursivo em dicts aninhados"""
        existing = {
            "amplis": {
                "reag": {"username": "user1", "password": "pass1"},
                "master": {"username": "user2", "password": "pass2"}
            }
        }
        new = {
            "amplis": {
                "reag": {"username": "new_user", "password": "********"},
                "master": {"username": "user2", "password": "new_pass"}
            }
        }
        result = service._merge_credentials(existing, new)
        assert result["amplis"]["reag"]["username"] == "new_user"
        assert result["amplis"]["reag"]["password"] == "pass1"  # Preservada
        assert result["amplis"]["master"]["password"] == "new_pass"  # Atualizada

    def test_merge_adds_new_keys(self, service):
        """Merge adiciona novas chaves"""
        existing = {"username": "user"}
        new = {"username": "user", "email": "user@test.com"}
        result = service._merge_credentials(existing, new)
        assert result["email"] == "user@test.com"

    def test_merge_empty_password_preserved(self, service):
        """Merge preserva quando novo password e vazio"""
        existing = {"password": "real_pass"}
        new = {"password": ""}
        result = service._merge_credentials(existing, new)
        # Vazio nao e "********", entao mantem como esta
        assert result["password"] == ""


class TestGetSystemCredentials:
    """Testes para get_system_credentials"""

    @pytest.fixture
    def service(self, sample_credentials):
        """Fixture do service com credenciais"""
        with patch.object(ConfigService, '_load_credentials'):
            service = ConfigService()
            service._credentials = sample_credentials
            return service

    def test_get_simple_system(self, service):
        """Busca sistema simples"""
        creds = service.get_system_credentials("maps")
        assert creds["url"] == "https://maps.test"
        assert creds["username"] == "maps_user"

    def test_get_compound_system(self, service):
        """Busca sistema composto (amplis_reag)"""
        creds = service.get_system_credentials("amplis_reag")
        assert creds["url"] == "https://amplis.test"
        assert creds["username"] == "user_reag"

    def test_get_another_compound_system(self, service):
        """Busca outro sistema composto (amplis_master)"""
        creds = service.get_system_credentials("amplis_master")
        assert creds["username"] == "user_master"

    def test_get_nonexistent_system(self, service):
        """Retorna None para sistema inexistente"""
        creds = service.get_system_credentials("invalid_system")
        assert creds is None

    def test_get_paths(self, service):
        """Busca paths"""
        paths = service.get_paths()
        assert paths["csv"] == "C:\\test\\csv"
        assert paths["pdf"] == "C:\\test\\pdf"


class TestConfigServiceWithFile:
    """Testes de integracao com arquivo"""

    def test_load_from_file(self, credentials_file, sample_credentials):
        """Carrega credenciais de arquivo"""
        with patch.object(ConfigService, 'CREDENTIALS_PATH', credentials_file):
            service = ConfigService()
            creds = service.get_credentials()
            assert creds["version"] == "2.0"
            assert creds["amplis"]["reag"]["username"] == "user_reag"

    def test_save_to_file(self, temp_credentials_path, sample_credentials):
        """Salva credenciais em arquivo"""
        with patch.object(ConfigService, 'CREDENTIALS_PATH', temp_credentials_path):
            # Criar diretorio
            os.makedirs(os.path.dirname(temp_credentials_path), exist_ok=True)

            service = ConfigService()
            service._credentials = {}
            service.save_credentials(sample_credentials)

            # Verificar arquivo
            with open(temp_credentials_path, "r") as f:
                saved = json.load(f)
            assert saved["version"] == "2.0"

    def test_default_credentials_when_file_missing(self, temp_dir):
        """Usa credenciais padrao quando arquivo nao existe"""
        fake_path = os.path.join(temp_dir, "nonexistent", "creds.json")
        with patch.object(ConfigService, 'CREDENTIALS_PATH', fake_path):
            service = ConfigService()
            creds = service.get_credentials()
            assert creds["version"] == "2.0"
            assert "amplis" in creds
            assert "paths" in creds

    def test_get_credentials_masked(self, credentials_file):
        """get_credentials_masked retorna senhas mascaradas"""
        with patch.object(ConfigService, 'CREDENTIALS_PATH', credentials_file):
            service = ConfigService()
            masked = service.get_credentials_masked()
            assert masked["amplis"]["reag"]["password"] == "********"
            assert masked["maps"]["password"] == "********"

    def test_reload_credentials(self, credentials_file, sample_credentials):
        """reload() recarrega do arquivo"""
        with patch.object(ConfigService, 'CREDENTIALS_PATH', credentials_file):
            service = ConfigService()

            # Modificar em memoria
            service._credentials["version"] = "modified"

            # Recarregar
            service.reload()

            # Deve voltar ao original
            assert service._credentials["version"] == "2.0"
