"""
Testes de integracao para API de sistemas
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


@pytest.fixture
def mock_sistema_service():
    """Mock do SistemaService"""
    from models.sistema import Sistema, SistemaStatus

    # Criar sistemas mock
    sistemas = {
        "amplis_reag": Sistema(
            id="amplis_reag",
            nome="AMPLIS (REAG)",
            descricao="Importacao AMPLIS REAG",
            icone="BarChart3",
            ordem=1,
            ativo=True,
            opcoes={"csv": True, "pdf": True}
        ),
        "maps": Sistema(
            id="maps",
            nome="MAPS",
            descricao="Upload MAPS",
            icone="Map",
            ordem=3,
            ativo=True,
            opcoes={"excel": True, "pdf": True}
        ),
        "fidc": Sistema(
            id="fidc",
            nome="FIDC",
            descricao="Gestao FIDC",
            icone="FileSpreadsheet",
            ordem=4,
            ativo=False,
            opcoes={}
        )
    }

    service = MagicMock()
    service.get_all.return_value = sistemas
    service.get_by_id.side_effect = lambda x: sistemas.get(x)
    service.get_ativos.return_value = {k: v for k, v in sistemas.items() if v.ativo}
    service.to_dict.return_value = {k: v.model_dump() for k, v in sistemas.items()}

    def toggle(sistema_id, ativo):
        if sistema_id in sistemas:
            sistemas[sistema_id].ativo = ativo
            return sistemas[sistema_id]
        return None

    def update_opcao(sistema_id, opcao, valor):
        if sistema_id in sistemas:
            sistemas[sistema_id].opcoes[opcao] = valor
            return sistemas[sistema_id]
        return None

    service.toggle.side_effect = toggle
    service.update_opcao.side_effect = update_opcao

    return service


@pytest.mark.asyncio
class TestSistemasEndpoints:
    """Testes para endpoints de sistemas"""

    async def test_get_sistemas(self, mock_sistema_service):
        """GET /api/sistemas retorna todos os sistemas"""
        from httpx import AsyncClient, ASGITransport

        with patch("routers.sistemas.get_sistema_service", return_value=mock_sistema_service):
            from app import app
            transport = ASGITransport(app=app)

            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/sistemas")

            assert response.status_code == 200
            data = response.json()
            assert "amplis_reag" in data
            assert "maps" in data
            assert data["amplis_reag"]["nome"] == "AMPLIS (REAG)"

    async def test_get_sistemas_ativos(self, mock_sistema_service):
        """GET /api/sistemas/ativos retorna apenas sistemas ativos"""
        from httpx import AsyncClient, ASGITransport

        with patch("routers.sistemas.get_sistema_service", return_value=mock_sistema_service):
            from app import app
            transport = ASGITransport(app=app)

            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/sistemas/ativos")

            assert response.status_code == 200
            data = response.json()
            assert "amplis_reag" in data
            assert "maps" in data
            assert "fidc" not in data  # inativo

    async def test_get_sistema_by_id(self, mock_sistema_service):
        """GET /api/sistemas/{id} retorna sistema especifico"""
        from httpx import AsyncClient, ASGITransport

        with patch("routers.sistemas.get_sistema_service", return_value=mock_sistema_service):
            from app import app
            transport = ASGITransport(app=app)

            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/sistemas/maps")

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == "maps"
            assert data["nome"] == "MAPS"

    async def test_get_sistema_not_found(self, mock_sistema_service):
        """GET /api/sistemas/{id} retorna 404 para inexistente"""
        from httpx import AsyncClient, ASGITransport

        with patch("routers.sistemas.get_sistema_service", return_value=mock_sistema_service):
            from app import app
            transport = ASGITransport(app=app)

            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/sistemas/invalid")

            assert response.status_code == 404

    async def test_toggle_sistema(self, mock_sistema_service):
        """PATCH /api/sistemas/{id}/toggle alterna estado"""
        from httpx import AsyncClient, ASGITransport

        with patch("routers.sistemas.get_sistema_service", return_value=mock_sistema_service):
            from app import app
            transport = ASGITransport(app=app)

            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.patch(
                    "/api/sistemas/fidc/toggle?ativo=true"
                )

            assert response.status_code == 200
            mock_sistema_service.toggle.assert_called_with("fidc", True)

    async def test_toggle_sistema_not_found(self, mock_sistema_service):
        """PATCH /api/sistemas/{id}/toggle retorna 404 para inexistente"""
        from httpx import AsyncClient, ASGITransport

        with patch("routers.sistemas.get_sistema_service", return_value=mock_sistema_service):
            from app import app
            transport = ASGITransport(app=app)

            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.patch(
                    "/api/sistemas/invalid/toggle?ativo=true"
                )

            assert response.status_code == 404

    async def test_update_opcao(self, mock_sistema_service):
        """PATCH /api/sistemas/{id}/opcao atualiza opcao"""
        from httpx import AsyncClient, ASGITransport

        with patch("routers.sistemas.get_sistema_service", return_value=mock_sistema_service):
            from app import app
            transport = ASGITransport(app=app)

            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.patch(
                    "/api/sistemas/amplis_reag/opcao?opcao=pdf&valor=false"
                )

            assert response.status_code == 200
            mock_sistema_service.update_opcao.assert_called_with("amplis_reag", "pdf", False)
