"""
Testes unitarios para models Pydantic
"""
import pytest
from pydantic import ValidationError

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from models.job import Job, JobParams, JobStatus
from models.sistema import Sistema, SistemaOpcoes, SistemaStatus


class TestJobStatus:
    """Testes para enum JobStatus"""

    def test_status_values(self):
        """Verifica valores do enum"""
        assert JobStatus.PENDING == "pending"
        assert JobStatus.RUNNING == "running"
        assert JobStatus.COMPLETED == "completed"
        assert JobStatus.ERROR == "error"
        assert JobStatus.CANCELLED == "cancelled"

    def test_status_from_string(self):
        """Verifica conversao de string para enum"""
        assert JobStatus("pending") == JobStatus.PENDING
        assert JobStatus("running") == JobStatus.RUNNING


class TestJobParams:
    """Testes para modelo JobParams"""

    def test_default_values(self):
        """Verifica valores padrao"""
        params = JobParams()
        assert params.sistemas == []
        assert params.dry_run is False
        assert params.limpar is False
        assert params.data_inicial is None
        assert params.data_final is None
        assert params.opcoes == {}

    def test_with_values(self):
        """Verifica criacao com valores"""
        params = JobParams(
            sistemas=["amplis_reag", "maps"],
            dry_run=True,
            data_inicial="2024-01-01",
            data_final="2024-01-31",
            opcoes={"amplis_reag": {"csv": True}}
        )
        assert params.sistemas == ["amplis_reag", "maps"]
        assert params.dry_run is True
        assert params.data_inicial == "2024-01-01"
        assert params.opcoes["amplis_reag"]["csv"] is True

    def test_serialization(self):
        """Verifica serializacao para dict"""
        params = JobParams(sistemas=["fidc"])
        data = params.model_dump()
        assert isinstance(data, dict)
        assert data["sistemas"] == ["fidc"]


class TestJob:
    """Testes para modelo Job"""

    def test_minimal_job(self):
        """Verifica job com campos minimos"""
        job = Job(id=1, type="etl_pipeline")
        assert job.id == 1
        assert job.type == "etl_pipeline"
        assert job.status == JobStatus.PENDING
        assert job.logs == ""
        assert job.error_message is None

    def test_complete_job(self):
        """Verifica job com todos os campos"""
        params = JobParams(sistemas=["maps"])
        job = Job(
            id=42,
            type="etl_single",
            params=params,
            status=JobStatus.RUNNING,
            logs="[INFO] Starting...\n",
            created_at="2024-01-01T10:00:00",
            started_at="2024-01-01T10:01:00"
        )
        assert job.id == 42
        assert job.params.sistemas == ["maps"]
        assert job.status == "running"  # use_enum_values=True
        assert "Starting" in job.logs

    def test_job_status_enum_serialization(self):
        """Verifica que status e serializado como string"""
        job = Job(id=1, type="test", status=JobStatus.COMPLETED)
        data = job.model_dump()
        assert data["status"] == "completed"


class TestSistemaStatus:
    """Testes para enum SistemaStatus"""

    def test_status_values(self):
        """Verifica valores do enum"""
        assert SistemaStatus.IDLE == "IDLE"
        assert SistemaStatus.RUNNING == "RUNNING"
        assert SistemaStatus.SUCCESS == "SUCCESS"
        assert SistemaStatus.ERROR == "ERROR"
        assert SistemaStatus.CANCELLED == "CANCELLED"


class TestSistemaOpcoes:
    """Testes para modelo SistemaOpcoes"""

    def test_all_optional(self):
        """Verifica que todos os campos sao opcionais"""
        opcoes = SistemaOpcoes()
        assert opcoes.csv is None
        assert opcoes.pdf is None
        assert opcoes.excel is None

    def test_with_values(self):
        """Verifica criacao com valores"""
        opcoes = SistemaOpcoes(csv=True, pdf=False, excel=True)
        assert opcoes.csv is True
        assert opcoes.pdf is False
        assert opcoes.excel is True

    def test_extra_fields_allowed(self):
        """Verifica que campos extras sao permitidos"""
        # Config.extra = "allow"
        opcoes = SistemaOpcoes(csv=True, custom_option=True)
        assert opcoes.csv is True
        # Extra fields acessiveis via model_extra ou diretamente
        assert hasattr(opcoes, "custom_option") or "custom_option" in opcoes.model_extra


class TestSistema:
    """Testes para modelo Sistema"""

    def test_minimal_sistema(self):
        """Verifica sistema com campos minimos"""
        sistema = Sistema(
            id="test_sys",
            nome="Test System",
            descricao="A test system",
            icone="TestIcon"
        )
        assert sistema.id == "test_sys"
        assert sistema.nome == "Test System"
        assert sistema.ativo is True  # default
        assert sistema.ordem == 0  # default
        assert sistema.status == "IDLE"  # use_enum_values
        assert sistema.progresso == 0

    def test_complete_sistema(self):
        """Verifica sistema com todos os campos"""
        sistema = Sistema(
            id="amplis_reag",
            nome="AMPLIS (REAG)",
            descricao="Importacao de dados do AMPLIS (REAG)",
            icone="BarChart3",
            ativo=False,
            ordem=1,
            opcoes={"csv": True, "pdf": False},
            status=SistemaStatus.RUNNING,
            progresso=50,
            mensagem="Processando..."
        )
        assert sistema.id == "amplis_reag"
        assert sistema.ativo is False
        assert sistema.opcoes["csv"] is True
        assert sistema.opcoes["pdf"] is False
        assert sistema.status == "RUNNING"
        assert sistema.progresso == 50
        assert sistema.mensagem == "Processando..."

    def test_sistema_serialization(self):
        """Verifica serializacao para dict"""
        sistema = Sistema(
            id="test",
            nome="Test",
            descricao="Desc",
            icone="Icon",
            status=SistemaStatus.SUCCESS
        )
        data = sistema.model_dump()
        assert isinstance(data, dict)
        assert data["id"] == "test"
        assert data["status"] == "SUCCESS"

    def test_sistema_with_invalid_status(self):
        """Verifica erro com status invalido"""
        with pytest.raises(ValidationError):
            Sistema(
                id="test",
                nome="Test",
                descricao="Desc",
                icone="Icon",
                status="INVALID_STATUS"
            )
