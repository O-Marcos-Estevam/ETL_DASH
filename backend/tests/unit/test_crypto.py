"""
Testes unitarios para CryptoService
"""
import pytest
import os
import sys
import base64
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestCryptoServiceInit:
    """Testes para inicializacao do CryptoService"""

    def test_init_with_master_key(self):
        """Inicializa com master key fornecida"""
        from services.crypto import CryptoService

        key = base64.b64encode(b"test_key_32_bytes_long!!!!!!!!!!").decode()
        service = CryptoService(master_key=key)

        assert service._master_key == key

    def test_init_with_env_var(self):
        """Inicializa com variavel de ambiente"""
        from services.crypto import CryptoService

        key = base64.b64encode(b"env_key_32_bytes_long!!!!!!!!!!").decode()
        with patch.dict(os.environ, {"ETL_MASTER_KEY": key}):
            service = CryptoService()
            assert service._master_key == key

    def test_init_without_key_raises(self):
        """Erro quando master key nao fornecida"""
        from services.crypto import CryptoService

        with patch.dict(os.environ, {}, clear=True):
            # Remove ETL_MASTER_KEY if it exists
            os.environ.pop("ETL_MASTER_KEY", None)
            with pytest.raises(ValueError) as exc_info:
                CryptoService(master_key=None)
            assert "Master key required" in str(exc_info.value)

    def test_class_constants(self):
        """Constantes da classe estao corretas"""
        from services.crypto import CryptoService

        assert CryptoService.ALGORITHM == "AES-256-GCM"
        assert CryptoService.KDF == "PBKDF2-SHA256"
        assert CryptoService.ITERATIONS == 600_000
        assert CryptoService.KEY_LENGTH == 32
        assert CryptoService.NONCE_LENGTH == 12
        assert CryptoService.TAG_LENGTH == 16
        assert CryptoService.SALT_LENGTH == 32


class TestCryptoServiceDeriveKey:
    """Testes para derivacao de chave"""

    @pytest.fixture
    def crypto(self):
        """Fixture do CryptoService com chave de teste"""
        from services.crypto import CryptoService
        key = base64.b64encode(b"test_master_key_32_bytes!!!!!!!!").decode()
        return CryptoService(master_key=key)

    def test_derive_key_returns_bytes(self, crypto):
        """_derive_key retorna bytes"""
        salt = os.urandom(32)
        key = crypto._derive_key(salt)
        assert isinstance(key, bytes)
        assert len(key) == 32

    def test_derive_key_deterministic(self, crypto):
        """Mesma salt gera mesma chave"""
        salt = os.urandom(32)
        key1 = crypto._derive_key(salt)
        key2 = crypto._derive_key(salt)
        assert key1 == key2

    def test_derive_key_different_salt(self, crypto):
        """Salts diferentes geram chaves diferentes"""
        salt1 = os.urandom(32)
        salt2 = os.urandom(32)
        key1 = crypto._derive_key(salt1)
        key2 = crypto._derive_key(salt2)
        assert key1 != key2

    def test_derive_key_with_utf8_master_key(self):
        """Aceita master key em UTF-8 (nao base64)"""
        from services.crypto import CryptoService
        # Chave nao base64
        service = CryptoService(master_key="simple_utf8_key_not_base64")
        salt = os.urandom(32)
        key = service._derive_key(salt)
        assert len(key) == 32


class TestCryptoServiceEncryptDecrypt:
    """Testes para criptografia/descriptografia"""

    @pytest.fixture
    def crypto(self):
        """Fixture do CryptoService"""
        from services.crypto import CryptoService
        key = base64.b64encode(b"test_master_key_32_bytes!!!!!!!!").decode()
        return CryptoService(master_key=key)

    def test_encrypt_value_structure(self, crypto):
        """_encrypt_value retorna estrutura correta"""
        salt = os.urandom(32)
        key = crypto._derive_key(salt)

        result = crypto._encrypt_value("secret_password", key)

        assert result["_encrypted"] is True
        assert "nonce" in result
        assert "ciphertext" in result
        assert "tag" in result

    def test_decrypt_value_success(self, crypto):
        """_decrypt_value recupera valor original"""
        salt = os.urandom(32)
        key = crypto._derive_key(salt)

        original = "my_secret_password_123"
        encrypted = crypto._encrypt_value(original, key)
        decrypted = crypto._decrypt_value(encrypted, key)

        assert decrypted == original

    def test_decrypt_with_wrong_key_fails(self, crypto):
        """Falha ao descriptografar com chave errada"""
        from cryptography.exceptions import InvalidTag

        salt = os.urandom(32)
        key1 = crypto._derive_key(salt)
        key2 = crypto._derive_key(os.urandom(32))  # Different salt = different key

        encrypted = crypto._encrypt_value("secret", key1)

        with pytest.raises(InvalidTag):
            crypto._decrypt_value(encrypted, key2)

    def test_encrypt_different_nonce(self, crypto):
        """Cada criptografia usa nonce diferente"""
        salt = os.urandom(32)
        key = crypto._derive_key(salt)

        enc1 = crypto._encrypt_value("password", key)
        enc2 = crypto._encrypt_value("password", key)

        assert enc1["nonce"] != enc2["nonce"]
        assert enc1["ciphertext"] != enc2["ciphertext"]

    def test_encrypt_empty_string(self, crypto):
        """Criptografa string vazia"""
        salt = os.urandom(32)
        key = crypto._derive_key(salt)

        encrypted = crypto._encrypt_value("", key)
        decrypted = crypto._decrypt_value(encrypted, key)

        assert decrypted == ""

    def test_encrypt_unicode(self, crypto):
        """Criptografa caracteres Unicode"""
        salt = os.urandom(32)
        key = crypto._derive_key(salt)

        original = "senha_secreta_com_acentos_áéíóú_123"
        encrypted = crypto._encrypt_value(original, key)
        decrypted = crypto._decrypt_value(encrypted, key)

        assert decrypted == original


class TestCryptoServiceCredentials:
    """Testes para criptografia de credenciais completas"""

    @pytest.fixture
    def crypto(self):
        """Fixture do CryptoService"""
        from services.crypto import CryptoService
        key = base64.b64encode(b"test_master_key_32_bytes!!!!!!!!").decode()
        return CryptoService(master_key=key)

    def test_encrypt_credentials_structure(self, crypto):
        """encrypt_credentials retorna estrutura correta"""
        credentials = {
            "version": "1.0",
            "britech": {
                "url": "https://api.example.com",
                "username": "user",
                "password": "secret123"
            }
        }

        encrypted = crypto.encrypt_credentials(credentials)

        assert encrypted["version"] == "1.0"
        assert "encryption" in encrypted
        assert encrypted["encryption"]["algorithm"] == "AES-256-GCM"
        assert encrypted["encryption"]["kdf"] == "PBKDF2-SHA256"
        assert encrypted["encryption"]["iterations"] == 600_000
        assert "salt" in encrypted["encryption"]
        assert "created_at" in encrypted["encryption"]

    def test_encrypt_only_sensitive_fields(self, crypto):
        """Apenas campos sensiveis sao criptografados"""
        credentials = {
            "system": {
                "url": "https://api.example.com",
                "username": "admin",
                "password": "secret"
            }
        }

        encrypted = crypto.encrypt_credentials(credentials)

        # URL e username permanecem texto plano
        assert encrypted["system"]["url"] == "https://api.example.com"
        assert encrypted["system"]["username"] == "admin"
        # Senha e criptografada
        assert encrypted["system"]["password"]["_encrypted"] is True

    def test_decrypt_credentials_success(self, crypto):
        """decrypt_credentials recupera valores originais"""
        credentials = {
            "version": "2.0",
            "britech": {
                "url": "https://britech.com.br",
                "username": "admin",
                "password": "britech_password"
            },
            "amplis": {
                "username": "amplis_user",
                "password": "amplis_pass"
            }
        }

        encrypted = crypto.encrypt_credentials(credentials)
        decrypted = crypto.decrypt_credentials(encrypted)

        assert decrypted["version"] == "2.0"
        assert decrypted["britech"]["url"] == "https://britech.com.br"
        assert decrypted["britech"]["password"] == "britech_password"
        assert decrypted["amplis"]["password"] == "amplis_pass"

    def test_decrypt_missing_salt_raises(self, crypto):
        """Erro quando salt faltando"""
        encrypted = {"version": "1.0", "encryption": {}}

        with pytest.raises(ValueError) as exc_info:
            crypto.decrypt_credentials(encrypted)
        assert "Missing encryption salt" in str(exc_info.value)

    def test_encrypt_nested_structure(self, crypto):
        """Criptografa estrutura aninhada"""
        credentials = {
            "level1": {
                "level2": {
                    "level3": {
                        "password": "deep_secret"
                    }
                }
            }
        }

        encrypted = crypto.encrypt_credentials(credentials)
        decrypted = crypto.decrypt_credentials(encrypted)

        assert decrypted["level1"]["level2"]["level3"]["password"] == "deep_secret"

    def test_encrypt_list_with_passwords(self, crypto):
        """Criptografa lista com senhas"""
        credentials = {
            "systems": [
                {"name": "sys1", "password": "pass1"},
                {"name": "sys2", "password": "pass2"}
            ]
        }

        encrypted = crypto.encrypt_credentials(credentials)
        decrypted = crypto.decrypt_credentials(encrypted)

        assert decrypted["systems"][0]["name"] == "sys1"
        assert decrypted["systems"][0]["password"] == "pass1"
        assert decrypted["systems"][1]["password"] == "pass2"

    def test_encrypt_multiple_sensitive_fields(self, crypto):
        """Criptografa multiplos campos sensiveis"""
        credentials = {
            "system": {
                "password": "pass1",
                "senha": "pass2",
                "secret": "pass3",
                "token": "token123",
                "api_key": "key456"
            }
        }

        encrypted = crypto.encrypt_credentials(credentials)

        # Todos devem estar criptografados
        for field in ["password", "senha", "secret", "token", "api_key"]:
            assert encrypted["system"][field]["_encrypted"] is True

        decrypted = crypto.decrypt_credentials(encrypted)

        assert decrypted["system"]["password"] == "pass1"
        assert decrypted["system"]["senha"] == "pass2"
        assert decrypted["system"]["secret"] == "pass3"
        assert decrypted["system"]["token"] == "token123"
        assert decrypted["system"]["api_key"] == "key456"

    def test_depth_limit_protection(self, crypto):
        """Protecao contra recursao infinita"""
        # Criar estrutura muito aninhada
        deep = {"password": "secret"}
        for _ in range(15):
            deep = {"nested": deep}

        # Nao deve dar erro, mas para de processar apos profundidade 10
        encrypted = crypto.encrypt_credentials(deep)
        assert "nested" in encrypted

    def test_empty_password_not_encrypted(self, crypto):
        """Senha vazia nao e criptografada"""
        credentials = {
            "system": {
                "password": "",
                "other": "value"
            }
        }

        encrypted = crypto.encrypt_credentials(credentials)

        # Senha vazia permanece vazia (nao criptografa)
        assert encrypted["system"]["password"] == ""

    def test_non_string_password_not_encrypted(self, crypto):
        """Valores nao-string nao sao criptografados"""
        credentials = {
            "system": {
                "password": 12345,  # numero
                "secret": None  # None
            }
        }

        encrypted = crypto.encrypt_credentials(credentials)

        # Valores nao-string permanecem como estao
        assert encrypted["system"]["password"] == 12345
        assert encrypted["system"]["secret"] is None


class TestCryptoServiceIsEncrypted:
    """Testes para is_encrypted"""

    @pytest.fixture
    def crypto(self):
        """Fixture do CryptoService"""
        from services.crypto import CryptoService
        key = base64.b64encode(b"test_master_key_32_bytes!!!!!!!!").decode()
        return CryptoService(master_key=key)

    def test_is_encrypted_true(self, crypto):
        """Detecta dados criptografados"""
        credentials = {"system": {"password": "secret"}}
        encrypted = crypto.encrypt_credentials(credentials)

        assert crypto.is_encrypted(encrypted) is True

    def test_is_encrypted_false_plain(self, crypto):
        """Detecta dados nao criptografados"""
        credentials = {"system": {"password": "secret"}}

        assert crypto.is_encrypted(credentials) is False

    def test_is_encrypted_false_no_encryption_key(self, crypto):
        """False quando chave encryption faltando"""
        data = {"version": "1.0", "system": {}}

        assert crypto.is_encrypted(data) is False

    def test_is_encrypted_false_wrong_algorithm(self, crypto):
        """False quando algoritmo diferente"""
        data = {
            "encryption": {"algorithm": "AES-128-CBC"}
        }

        assert crypto.is_encrypted(data) is False


class TestCryptoServiceSingleton:
    """Testes para funcoes singleton"""

    def test_get_crypto_service_returns_instance(self):
        """get_crypto_service retorna instancia"""
        from services.crypto import get_crypto_service, reset_crypto_service, CryptoService

        reset_crypto_service()
        key = base64.b64encode(b"singleton_test_key!!!!!!!!!!!!!!").decode()

        with patch.dict(os.environ, {"ETL_MASTER_KEY": key}):
            service = get_crypto_service()
            assert isinstance(service, CryptoService)

    def test_get_crypto_service_singleton(self):
        """get_crypto_service retorna mesma instancia"""
        from services.crypto import get_crypto_service, reset_crypto_service

        reset_crypto_service()
        key = base64.b64encode(b"singleton_test_key!!!!!!!!!!!!!!").decode()

        with patch.dict(os.environ, {"ETL_MASTER_KEY": key}):
            service1 = get_crypto_service()
            service2 = get_crypto_service()
            assert service1 is service2

    def test_reset_crypto_service(self):
        """reset_crypto_service limpa singleton"""
        from services.crypto import get_crypto_service, reset_crypto_service

        key = base64.b64encode(b"singleton_test_key!!!!!!!!!!!!!!").decode()

        with patch.dict(os.environ, {"ETL_MASTER_KEY": key}):
            service1 = get_crypto_service()
            reset_crypto_service()
            service2 = get_crypto_service()
            assert service1 is not service2


class TestCryptoServiceIntegration:
    """Testes de integracao end-to-end"""

    def test_full_encrypt_decrypt_cycle(self):
        """Ciclo completo de criptografia/descriptografia"""
        from services.crypto import CryptoService

        key = base64.b64encode(b"integration_test_key!!!!!!!!!!!!").decode()
        crypto = CryptoService(master_key=key)

        original = {
            "version": "1.0",
            "britech": {
                "url": "https://api.britech.com.br",
                "username": "admin",
                "password": "super_secret_password_123!"
            },
            "amplis": {
                "username": "amplis_user",
                "senha": "amplis_senha_456"
            },
            "maps": {
                "api_key": "maps_api_key_789",
                "secret": "maps_secret_xyz"
            }
        }

        # Criptografar
        encrypted = crypto.encrypt_credentials(original)

        # Verificar que sensiveis estao criptografados
        assert encrypted["britech"]["password"]["_encrypted"] is True
        assert encrypted["amplis"]["senha"]["_encrypted"] is True
        assert encrypted["maps"]["api_key"]["_encrypted"] is True
        assert encrypted["maps"]["secret"]["_encrypted"] is True

        # Verificar que nao-sensiveis estao em texto plano
        assert encrypted["britech"]["url"] == original["britech"]["url"]
        assert encrypted["britech"]["username"] == original["britech"]["username"]

        # Descriptografar
        decrypted = crypto.decrypt_credentials(encrypted)

        # Verificar valores
        assert decrypted["britech"]["password"] == "super_secret_password_123!"
        assert decrypted["amplis"]["senha"] == "amplis_senha_456"
        assert decrypted["maps"]["api_key"] == "maps_api_key_789"
        assert decrypted["maps"]["secret"] == "maps_secret_xyz"

    def test_different_keys_cannot_decrypt(self):
        """Chaves diferentes nao conseguem descriptografar"""
        from services.crypto import CryptoService
        from cryptography.exceptions import InvalidTag

        key1 = base64.b64encode(b"first_master_key!!!!!!!!!!!!!!!!").decode()
        key2 = base64.b64encode(b"second_master_key!!!!!!!!!!!!!!!").decode()

        crypto1 = CryptoService(master_key=key1)
        crypto2 = CryptoService(master_key=key2)

        credentials = {"system": {"password": "secret"}}

        encrypted = crypto1.encrypt_credentials(credentials)

        with pytest.raises(InvalidTag):
            crypto2.decrypt_credentials(encrypted)
