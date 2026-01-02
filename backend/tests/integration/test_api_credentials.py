"""
Testes de integracao para API de credenciais
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
    service.get_credentials_masked.return_value = {
        "version": "2.0",
        "amplis": {
            "reag": {"url": "https://amplis.test", "username": "user_reag", "password": "********"},
            "master": {"url": "https://amplis.test", "username": "user_master", "password": "********"}
        },
        "maps": {"url": "https://maps.test", "username": "maps_user", "password": "********"},
        "paths": sample_credentials["paths"]
    }
    service.get_system_credentials_masked.side_effect = lambda x: {
        "url": f"https://{x}.test",
        "username": f"{x}_user",
        "password": "********"
    }
    service.save_credentials.return_value = True
    service.get_paths.return_value = sample_credentials["paths"]
    service.get_fundos.return_value = sample_credentials.get("fundos", {})
    return service


@pytest.mark.asyncio
class TestCredentialsEndpoints:
    """Testes para endpoints de credenciais"""

    async def test_get_credentials(self, mock_config_service, disable_auth):
        """GET /api/credentials retorna credenciais mascaradas"""
        from httpx import AsyncClient, ASGITransport

        with patch("routers.credentials.get_config_service", return_value=mock_config_service):
            from app import app
            transport = ASGITransport(app=app)

            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/credentials")

            assert response.status_code == 200
            data = response.json()
            assert data["amplis"]["reag"]["password"] == "********"
            assert data["amplis"]["reag"]["username"] == "user_reag"

    async def test_save_credentials(self, mock_config_service, disable_auth):
        """POST /api/credentials salva credenciais"""
        from httpx import AsyncClient, ASGITransport

        with patch("routers.credentials.get_config_service", return_value=mock_config_service):
            from app import app
            transport = ASGITransport(app=app)

            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/credentials",
                    json={
                        "amplis": {
                            "reag": {"username": "new_user", "password": "new_pass"}
                        }
                    }
                )

            assert response.status_code == 200
            mock_config_service.save_credentials.assert_called_once()

    async def test_save_credentials_failure(self, mock_config_service, disable_auth):
        """POST /api/credentials retorna erro em falha"""
        from httpx import AsyncClient, ASGITransport

        mock_config_service.save_credentials.return_value = False

        with patch("routers.credentials.get_config_service", return_value=mock_config_service):
            from app import app
            transport = ASGITransport(app=app)

            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/credentials",
                    json={"test": "data"}
                )

            assert response.status_code == 500

    async def test_get_system_credentials(self, mock_config_service, disable_auth):
        """GET /api/credentials/{system_id} retorna credenciais do sistema"""
        from httpx import AsyncClient, ASGITransport

        with patch("routers.credentials.get_config_service", return_value=mock_config_service):
            from app import app
            transport = ASGITransport(app=app)

            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/credentials/maps")

            assert response.status_code == 200
            data = response.json()
            assert data["password"] == "********"

    async def test_get_system_credentials_not_found(self, mock_config_service, disable_auth):
        """GET /api/credentials/{system_id} retorna 404 ou 200 vazio para inexistente"""
        from httpx import AsyncClient, ASGITransport

        mock_config_service.get_system_credentials_masked.return_value = None

        with patch("routers.credentials.get_config_service", return_value=mock_config_service):
            from app import app
            transport = ASGITransport(app=app)

            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/credentials/invalid")

            # API pode retornar 404 ou 200 com valor None/vazio
            assert response.status_code in [200, 404]

    async def test_get_fundos(self, mock_config_service, disable_auth):
        """GET /api/fundos retorna configuracao de fundos"""
        from httpx import AsyncClient, ASGITransport

        with patch("routers.credentials.get_config_service", return_value=mock_config_service):
            from app import app
            transport = ASGITransport(app=app)

            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/fundos")

            assert response.status_code == 200


@pytest.mark.asyncio
class TestHealthEndpoint:
    """Testes para endpoint de health"""

    async def test_health_check(self):
        """GET /api/health retorna status ok"""
        from httpx import AsyncClient, ASGITransport
        from app import app

        transport = ASGITransport(app=app)

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
