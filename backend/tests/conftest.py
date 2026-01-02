"""
Pytest Fixtures - Configuracoes compartilhadas para testes
"""
import pytest
import tempfile
import os
import sys
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

# Adicionar backend ao path
backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))


# ============================================================
# Fixtures de Arquivos Temporarios
# ============================================================

@pytest.fixture
def temp_dir():
    """Diretorio temporario para testes"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def temp_db_path(temp_dir):
    """Caminho para banco de dados temporario"""
    return os.path.join(temp_dir, "test_tasks.db")


@pytest.fixture
def temp_credentials_path(temp_dir):
    """Caminho para arquivo de credenciais temporario"""
    return os.path.join(temp_dir, "credentials.json")


@pytest.fixture
def temp_state_path(temp_dir):
    """Caminho para arquivo de estado temporario"""
    return os.path.join(temp_dir, "sistemas_state.json")


# ============================================================
# Fixtures de Dados de Teste
# ============================================================

@pytest.fixture
def sample_credentials():
    """Credenciais de exemplo para testes"""
    return {
        "version": "2.0",
        "amplis": {
            "reag": {"url": "https://amplis.test", "username": "user_reag", "password": "pass123"},
            "master": {"url": "https://amplis.test", "username": "user_master", "password": "pass456"}
        },
        "maps": {"url": "https://maps.test", "username": "maps_user", "password": "maps_pass"},
        "fidc": {"url": "https://fidc.test", "username": "fidc_user", "password": "fidc_pass"},
        "jcot": {"url": "https://jcot.test", "username": "jcot_user", "password": "jcot_pass"},
        "britech": {"url": "https://britech.test", "username": "britech_user", "password": "britech_pass"},
        "qore": {"url": "https://qore.test", "username": "qore_user", "password": "qore_pass"},
        "paths": {
            "csv": "C:\\test\\csv",
            "pdf": "C:\\test\\pdf",
            "maps": "C:\\test\\maps",
            "fidc": "C:\\test\\fidc",
            "jcot": "C:\\test\\jcot",
            "britech": "C:\\test\\britech",
            "qore_excel": "C:\\test\\qore_excel",
            "qore_pdf": "C:\\test\\qore_pdf",
            "bd_xlsx": "C:\\test\\bd_xlsx",
            "trustee": "C:\\test\\trustee",
            "selenium_temp": "C:\\test\\selenium"
        },
        "fundos": {"selecionados": ["FUNDO1", "FUNDO2"]}
    }


@pytest.fixture
def sample_sistemas_state():
    """Estado de sistemas de exemplo"""
    return {
        "amplis_reag": {"ativo": True, "opcoes": {"csv": True, "pdf": False}},
        "amplis_master": {"ativo": False, "opcoes": {"csv": True, "pdf": True}},
        "maps": {"ativo": True, "opcoes": {"excel": True, "pdf": True, "ativo": True, "passivo": False}},
        "fidc": {"ativo": True, "opcoes": {}},
        "jcot": {"ativo": False, "opcoes": {}},
        "britech": {"ativo": True, "opcoes": {}},
        "qore": {"ativo": True, "opcoes": {"excel": True, "pdf": True, "lote_pdf": False}},
        "trustee": {"ativo": False, "opcoes": {}}
    }


@pytest.fixture
def sample_job_params():
    """Parametros de job de exemplo"""
    return {
        "sistemas": ["amplis_reag", "maps", "fidc"],
        "data_inicial": "2024-01-01",
        "data_final": "2024-01-31",
        "dry_run": False,
        "limpar": False,
        "opcoes": {
            "amplis_reag": {"csv": True, "pdf": False},
            "maps": {"excel": True, "pdf": True, "ativo": True, "passivo": False}
        }
    }


# ============================================================
# Fixtures de Arquivos
# ============================================================

@pytest.fixture
def credentials_file(temp_credentials_path, sample_credentials):
    """Cria arquivo de credenciais temporario"""
    os.makedirs(os.path.dirname(temp_credentials_path), exist_ok=True)
    with open(temp_credentials_path, "w", encoding="utf-8") as f:
        json.dump(sample_credentials, f)
    return temp_credentials_path


@pytest.fixture
def state_file(temp_state_path, sample_sistemas_state):
    """Cria arquivo de estado temporario"""
    os.makedirs(os.path.dirname(temp_state_path), exist_ok=True)
    with open(temp_state_path, "w", encoding="utf-8") as f:
        json.dump(sample_sistemas_state, f)
    return temp_state_path


# ============================================================
# Fixtures de Mocks
# ============================================================

@pytest.fixture
def mock_subprocess():
    """Mock para asyncio.subprocess"""
    with patch("asyncio.create_subprocess_exec") as mock:
        process = MagicMock()
        process.returncode = 0
        process.stdout = MagicMock()
        process.stderr = MagicMock()
        process.wait = MagicMock(return_value=None)
        mock.return_value = process
        yield mock


# ============================================================
# Fixtures para API (httpx)
# ============================================================

@pytest.fixture
def test_client():
    """Cliente de teste para API FastAPI"""
    from httpx import AsyncClient, ASGITransport
    from app import app

    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


# ============================================================
# Fixtures de Database
# ============================================================

@pytest.fixture
def test_db(temp_db_path):
    """Inicializa banco de dados de teste"""
    from core import database

    # Substituir caminho do banco
    original_path = database.DB_PATH
    database.DB_PATH = Path(temp_db_path)

    # Inicializar
    database.init_db()

    yield database

    # Restaurar
    database.DB_PATH = original_path
