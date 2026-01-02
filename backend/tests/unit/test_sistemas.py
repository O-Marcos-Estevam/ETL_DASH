"""
Testes unitarios para SistemaService
"""
import pytest
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.sistemas import SistemaService
from models.sistema import SistemaStatus


class TestSistemaServiceBasic:
    """Testes basicos do SistemaService"""

    @pytest.fixture
    def service(self, temp_state_path):
        """Fixture do service com arquivo temporario"""
        with patch.object(SistemaService, 'STATE_FILE', temp_state_path):
            return SistemaService()

    def test_get_all_returns_all_sistemas(self, service):
        """get_all retorna todos os sistemas"""
        sistemas = service.get_all()
        assert len(sistemas) == 8
        assert "amplis_reag" in sistemas
        assert "amplis_master" in sistemas
        assert "maps" in sistemas
        assert "fidc" in sistemas
        assert "jcot" in sistemas
        assert "britech" in sistemas
        assert "qore" in sistemas
        assert "trustee" in sistemas

    def test_get_by_id_existing(self, service):
        """get_by_id retorna sistema existente"""
        sistema = service.get_by_id("maps")
        assert sistema is not None
        assert sistema.id == "maps"
        assert sistema.nome == "MAPS"

    def test_get_by_id_nonexistent(self, service):
        """get_by_id retorna None para inexistente"""
        sistema = service.get_by_id("invalid_system")
        assert sistema is None

    def test_sistemas_have_metadata(self, service):
        """Sistemas tem metadata correto"""
        amplis = service.get_by_id("amplis_reag")
        assert amplis.nome == "AMPLIS (REAG)"
        assert amplis.descricao == "Importacao de dados do AMPLIS (REAG)"
        assert amplis.icone == "BarChart3"
        assert amplis.ordem == 1

    def test_default_status_is_idle(self, service):
        """Status padrao e IDLE"""
        for sistema in service.get_all().values():
            assert sistema.status == "IDLE"
            assert sistema.progresso == 0


class TestSistemaServiceToggle:
    """Testes para toggle de sistemas"""

    @pytest.fixture
    def service(self, temp_state_path):
        """Fixture do service"""
        with patch.object(SistemaService, 'STATE_FILE', temp_state_path):
            return SistemaService()

    def test_toggle_ativo_true(self, service):
        """Toggle ativa sistema"""
        sistema = service.toggle("fidc", True)
        assert sistema.ativo is True

    def test_toggle_ativo_false(self, service):
        """Toggle desativa sistema"""
        sistema = service.toggle("maps", False)
        assert sistema.ativo is False

    def test_toggle_persists(self, service, temp_state_path):
        """Toggle persiste no arquivo"""
        with patch.object(SistemaService, 'STATE_FILE', temp_state_path):
            service.toggle("britech", False)

            # Verificar arquivo
            with open(temp_state_path, "r") as f:
                state = json.load(f)
            assert state["britech"]["ativo"] is False

    def test_toggle_invalid_sistema(self, service):
        """Toggle de sistema invalido retorna None"""
        result = service.toggle("invalid", True)
        assert result is None


class TestSistemaServiceOpcoes:
    """Testes para opcoes de sistemas"""

    @pytest.fixture
    def service(self, temp_state_path):
        """Fixture do service"""
        with patch.object(SistemaService, 'STATE_FILE', temp_state_path):
            return SistemaService()

    def test_update_opcao(self, service):
        """Atualiza opcao do sistema"""
        sistema = service.update_opcao("amplis_reag", "csv", False)
        assert sistema.opcoes["csv"] is False

    def test_update_opcao_new_key(self, service):
        """Adiciona nova opcao"""
        sistema = service.update_opcao("fidc", "nova_opcao", True)
        assert sistema.opcoes["nova_opcao"] is True

    def test_update_opcao_persists(self, service, temp_state_path):
        """Opcao persiste no arquivo"""
        with patch.object(SistemaService, 'STATE_FILE', temp_state_path):
            service.update_opcao("qore", "lote_pdf", True)

            with open(temp_state_path, "r") as f:
                state = json.load(f)
            assert state["qore"]["opcoes"]["lote_pdf"] is True

    def test_update_opcao_invalid_sistema(self, service):
        """Opcao de sistema invalido retorna None"""
        result = service.update_opcao("invalid", "opt", True)
        assert result is None


class TestSistemaServiceStatus:
    """Testes para status de sistemas"""

    @pytest.fixture
    def service(self, temp_state_path):
        """Fixture do service"""
        with patch.object(SistemaService, 'STATE_FILE', temp_state_path):
            return SistemaService()

    def test_update_status_running(self, service):
        """Atualiza status para RUNNING"""
        sistema = service.update_status(
            "maps",
            SistemaStatus.RUNNING,
            progresso=25,
            mensagem="Baixando arquivos..."
        )
        assert sistema.status == "RUNNING"
        assert sistema.progresso == 25
        assert sistema.mensagem == "Baixando arquivos..."

    def test_update_status_success(self, service):
        """Atualiza status para SUCCESS"""
        sistema = service.update_status("fidc", SistemaStatus.SUCCESS, progresso=100)
        assert sistema.status == "SUCCESS"
        assert sistema.progresso == 100

    def test_update_status_error(self, service):
        """Atualiza status para ERROR"""
        sistema = service.update_status(
            "jcot",
            SistemaStatus.ERROR,
            mensagem="Falha na conexao"
        )
        assert sistema.status == "ERROR"
        assert sistema.mensagem == "Falha na conexao"

    def test_update_status_invalid(self, service):
        """Status de sistema invalido retorna None"""
        result = service.update_status("invalid", SistemaStatus.RUNNING)
        assert result is None

    def test_reset_all_status(self, service):
        """Reset all status volta todos para IDLE"""
        # Modificar alguns
        service.update_status("maps", SistemaStatus.RUNNING, progresso=50)
        service.update_status("fidc", SistemaStatus.SUCCESS, progresso=100)
        service.update_status("jcot", SistemaStatus.ERROR, mensagem="Erro")

        # Reset
        service.reset_all_status()

        # Verificar
        for sistema in service.get_all().values():
            assert sistema.status == "IDLE"
            assert sistema.progresso == 0
            assert sistema.mensagem is None


class TestSistemaServiceAtivos:
    """Testes para sistemas ativos"""

    @pytest.fixture
    def service(self, temp_state_path):
        """Fixture do service"""
        with patch.object(SistemaService, 'STATE_FILE', temp_state_path):
            svc = SistemaService()
            # Configurar alguns como inativos
            svc.toggle("jcot", False)
            svc.toggle("trustee", False)
            return svc

    def test_get_ativos(self, service):
        """get_ativos retorna apenas sistemas ativos"""
        ativos = service.get_ativos()
        assert "jcot" not in ativos
        assert "trustee" not in ativos
        assert "maps" in ativos
        assert "amplis_reag" in ativos

    def test_get_ativos_ids(self, service):
        """get_ativos_ids retorna lista de IDs"""
        ids = service.get_ativos_ids()
        assert isinstance(ids, list)
        assert "jcot" not in ids
        assert "maps" in ids


class TestSistemaServiceSerialization:
    """Testes para serializacao"""

    @pytest.fixture
    def service(self, temp_state_path):
        """Fixture do service"""
        with patch.object(SistemaService, 'STATE_FILE', temp_state_path):
            return SistemaService()

    def test_to_dict(self, service):
        """to_dict converte todos sistemas para dict"""
        data = service.to_dict()
        assert isinstance(data, dict)
        assert len(data) == 8

        # Verificar estrutura
        maps_data = data["maps"]
        assert maps_data["id"] == "maps"
        assert maps_data["nome"] == "MAPS"
        assert "opcoes" in maps_data
        assert "status" in maps_data


class TestSistemaServicePersistence:
    """Testes de persistencia"""

    def test_load_saved_state(self, state_file, sample_sistemas_state):
        """Carrega estado salvo do arquivo"""
        with patch.object(SistemaService, 'STATE_FILE', state_file):
            service = SistemaService()

            # Verificar estado carregado
            amplis = service.get_by_id("amplis_reag")
            assert amplis.ativo is True
            assert amplis.opcoes["csv"] is True
            assert amplis.opcoes["pdf"] is False

            master = service.get_by_id("amplis_master")
            assert master.ativo is False

    def test_new_file_uses_defaults(self, temp_dir):
        """Arquivo novo usa defaults"""
        fake_path = os.path.join(temp_dir, "new_state.json")
        with patch.object(SistemaService, 'STATE_FILE', fake_path):
            service = SistemaService()

            # Todos devem estar ativos por padrao
            for sistema in service.get_all().values():
                assert sistema.ativo is True
