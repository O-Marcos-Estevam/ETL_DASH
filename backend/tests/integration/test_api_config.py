"""
Testes de integracao para API de config
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


@pytest.fixture
def mock_config_service(sample_credentials):
    """Mock do ConfigService"""
    service = MagicMock()
    service.get_credentials.return_value = sample_credentials
    service.get_paths.return_value = sample_credentials["paths"]
    service.save_credentials.return_value = True
    return service


@pytest.fixture
def mock_sistema_service():
    """Mock do SistemaService"""
    from models.sistema import Sistema

    service = MagicMock()
    service.to_dict.return_value = {
        "maps": {
            "id": "maps",
            "nome": "MAPS",
            "descricao": "Sistema MAPS",
            "icone": "Map",
            "ativo": True,
            "opcoes": {"excel": True, "pdf": True}
        }
    }
    service.toggle.return_value = None
    service.update_opcao.return_value = None
    return service


@pytest.mark.asyncio
class TestConfigEndpoints:
    """Testes para endpoints de config"""

    async def test_get_config(self, disable_auth, mock_config_service, mock_sistema_service):
        """GET /api/config retorna config combinada"""
        from httpx import AsyncClient, ASGITransport
        from app import app

        with patch("routers.config.get_config_service", return_value=mock_config_service), \
             patch("routers.config.get_sistema_service", return_value=mock_sistema_service):
            transport = ASGITransport(app=app)

            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/config")

            assert response.status_code == 200
            data = response.json()
            assert "sistemas" in data
            assert "paths" in data

    async def test_get_config_includes_periodo(self, disable_auth, mock_config_service, mock_sistema_service):
        """GET /api/config inclui periodo padrao"""
        from httpx import AsyncClient, ASGITransport
        from app import app

        with patch("routers.config.get_config_service", return_value=mock_config_service), \
             patch("routers.config.get_sistema_service", return_value=mock_sistema_service):
            transport = ASGITransport(app=app)

            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/config")

            data = response.json()
            assert "periodo" in data
            assert data["periodo"]["usarD1Anbima"] is True

    async def test_update_config(self, disable_auth, mock_config_service, mock_sistema_service):
        """POST /api/config salva configuracao"""
        from httpx import AsyncClient, ASGITransport
        from app import app

        with patch("routers.config.get_config_service", return_value=mock_config_service), \
             patch("routers.config.get_sistema_service", return_value=mock_sistema_service):
            transport = ASGITransport(app=app)

            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/config",
                    json={
                        "amplis": {"reag": {"username": "new_user"}},
                        "sistemas": {"maps": {"ativo": True}}
                    }
                )

            assert response.status_code == 200
            mock_config_service.save_credentials.assert_called_once()

    async def test_update_config_failure(self, disable_auth, mock_config_service, mock_sistema_service):
        """POST /api/config retorna erro em falha"""
        from httpx import AsyncClient, ASGITransport
        from app import app

        mock_config_service.save_credentials.return_value = False

        with patch("routers.config.get_config_service", return_value=mock_config_service), \
             patch("routers.config.get_sistema_service", return_value=mock_sistema_service):
            transport = ASGITransport(app=app)

            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/config",
                    json={"test": "data"}
                )

            assert response.status_code == 500

    async def test_update_config_updates_sistemas(self, disable_auth, mock_config_service, mock_sistema_service):
        """POST /api/config atualiza estado dos sistemas"""
        from httpx import AsyncClient, ASGITransport
        from app import app

        with patch("routers.config.get_config_service", return_value=mock_config_service), \
             patch("routers.config.get_sistema_service", return_value=mock_sistema_service):
            transport = ASGITransport(app=app)

            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/config",
                    json={
                        "sistemas": {
                            "maps": {"ativo": False, "opcoes": {"excel": False}}
                        }
                    }
                )

            assert response.status_code == 200
            mock_sistema_service.toggle.assert_called_with("maps", False)
            mock_sistema_service.update_opcao.assert_called_with("maps", "excel", False)


@pytest.mark.asyncio
class TestPathsEndpoint:
    """Testes para endpoint de paths"""

    async def test_get_paths(self, disable_auth, mock_config_service):
        """GET /api/config/paths retorna paths"""
        from httpx import AsyncClient, ASGITransport
        from app import app

        with patch("routers.config.get_config_service", return_value=mock_config_service):
            transport = ASGITransport(app=app)

            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/config/paths")

            assert response.status_code == 200
            data = response.json()
            assert "csv" in data
            assert "pdf" in data
