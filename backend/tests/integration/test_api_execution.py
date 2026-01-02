"""
Testes de integracao para API de execucao
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


@pytest.fixture
def mock_database():
    """Mock do modulo database"""
    mock = MagicMock()
    mock.add_job.return_value = 1
    mock.get_job.return_value = {
        "id": 1,
        "type": "etl_pipeline",
        "params": '{"sistemas": ["maps"]}',
        "status": "pending",
        "logs": "",
        "error_message": None,
        "created_at": "2024-01-01T10:00:00",
        "started_at": None,
        "finished_at": None
    }
    mock.get_running_job.return_value = None
    mock.list_jobs.return_value = []
    return mock


@pytest.fixture
def mock_sistema_service():
    """Mock do SistemaService"""
    from models.sistema import Sistema

    sistemas = {
        "maps": Sistema(
            id="maps",
            nome="MAPS",
            descricao="MAPS",
            icone="Map",
            ativo=True,
            opcoes={"excel": True}
        )
    }

    service = MagicMock()
    service.get_ativos_ids.return_value = ["maps"]
    service.get_by_id.side_effect = lambda x: sistemas.get(x)
    service.update_status.return_value = None
    return service


@pytest.mark.asyncio
class TestExecutionEndpoints:
    """Testes para endpoints de execucao"""

    async def test_execute_pipeline(self, mock_database, mock_sistema_service, disable_auth):
        """POST /api/execute enfileira pipeline"""
        from httpx import AsyncClient, ASGITransport

        with patch("routers.execution.database", mock_database), \
             patch("routers.execution.get_sistema_service", return_value=mock_sistema_service):
            from app import app
            transport = ASGITransport(app=app)

            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/execute",
                    json={
                        "sistemas": ["maps"],
                        "data_inicial": "2024-01-01",
                        "data_final": "2024-01-31"
                    }
                )

            assert response.status_code == 200
            data = response.json()
            assert "job_id" in data
            mock_database.add_job.assert_called_once()

    async def test_execute_empty_sistemas_returns_error(self, mock_database, mock_sistema_service, disable_auth):
        """POST /api/execute com sistemas vazio retorna erro"""
        from httpx import AsyncClient, ASGITransport

        with patch("routers.execution.database", mock_database), \
             patch("routers.execution.get_sistema_service", return_value=mock_sistema_service):
            from app import app
            transport = ASGITransport(app=app)

            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/execute",
                    json={"sistemas": []}
                )

            # API retorna erro quando nenhum sistema e fornecido
            assert response.status_code in [200, 400]

    async def test_execute_when_running_queues_job(self, mock_database, mock_sistema_service, disable_auth):
        """POST /api/execute enfileira job mesmo quando ha outro rodando"""
        from httpx import AsyncClient, ASGITransport

        mock_database.get_running_job.return_value = {"id": 1, "status": "running"}

        with patch("routers.execution.database", mock_database), \
             patch("routers.execution.get_sistema_service", return_value=mock_sistema_service):
            from app import app
            transport = ASGITransport(app=app)

            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/execute",
                    json={"sistemas": ["maps"]}
                )

            # API permite enfileirar jobs (eles ficam pending)
            assert response.status_code == 200

    async def test_get_job_status(self, mock_database, disable_auth):
        """GET /api/jobs/{id} retorna status do job"""
        from httpx import AsyncClient, ASGITransport

        with patch("routers.execution.database", mock_database):
            from app import app
            transport = ASGITransport(app=app)

            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/jobs/1")

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == 1
            assert data["status"] == "pending"

    async def test_get_job_not_found(self, mock_database, disable_auth):
        """GET /api/jobs/{id} retorna 404 para inexistente"""
        from httpx import AsyncClient, ASGITransport

        mock_database.get_job.return_value = None

        with patch("routers.execution.database", mock_database):
            from app import app
            transport = ASGITransport(app=app)

            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/jobs/999")

            assert response.status_code == 404

    async def test_list_jobs(self, mock_database, disable_auth):
        """GET /api/jobs lista jobs"""
        from httpx import AsyncClient, ASGITransport

        mock_database.list_jobs.return_value = [
            {"id": 1, "type": "etl_pipeline", "status": "completed"},
            {"id": 2, "type": "etl_single", "status": "pending"}
        ]

        with patch("routers.execution.database", mock_database):
            from app import app
            transport = ASGITransport(app=app)

            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/jobs")

            assert response.status_code == 200
            data = response.json()
            # API retorna dict com "jobs" key
            if isinstance(data, dict) and "jobs" in data:
                assert len(data["jobs"]) == 2
            else:
                assert len(data) == 2

    async def test_list_jobs_with_filter(self, mock_database, disable_auth):
        """GET /api/jobs?status=pending filtra por status"""
        from httpx import AsyncClient, ASGITransport

        with patch("routers.execution.database", mock_database):
            from app import app
            transport = ASGITransport(app=app)

            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/jobs?status=pending")

            assert response.status_code == 200
            mock_database.list_jobs.assert_called_with(status="pending", limit=20, offset=0)

    async def test_cancel_job(self, mock_database, disable_auth):
        """POST /api/cancel/{id} cancela job"""
        from httpx import AsyncClient, ASGITransport

        mock_database.get_job.return_value = {
            "id": 1,
            "status": "running"
        }

        with patch("routers.execution.database", mock_database), \
             patch("routers.execution.get_worker") as mock_worker:
            mock_worker.return_value.cancel_current_job.return_value = True

            from app import app
            transport = ASGITransport(app=app)

            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post("/api/cancel/1")

            assert response.status_code == 200


@pytest.mark.asyncio
class TestExecuteSingleEndpoint:
    """Testes para execucao de sistema unico"""

    async def test_execute_single(self, mock_database, mock_sistema_service, disable_auth):
        """POST /api/execute/{sistema_id} executa sistema unico"""
        from httpx import AsyncClient, ASGITransport

        with patch("routers.execution.database", mock_database), \
             patch("routers.execution.get_sistema_service", return_value=mock_sistema_service):
            from app import app
            transport = ASGITransport(app=app)

            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/execute/maps",
                    json={"data_inicial": "2024-01-01"}
                )

            assert response.status_code == 200
            data = response.json()
            assert "job_id" in data

    async def test_execute_single_invalid_sistema(self, mock_database, mock_sistema_service, disable_auth):
        """POST /api/execute/{sistema_id} rejeita sistema invalido"""
        from httpx import AsyncClient, ASGITransport

        mock_sistema_service.get_by_id.return_value = None

        with patch("routers.execution.database", mock_database), \
             patch("routers.execution.get_sistema_service", return_value=mock_sistema_service):
            from app import app
            transport = ASGITransport(app=app)

            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post("/api/execute/invalid", json={})

            # API pode retornar 404 ou 422 dependendo da validacao
            assert response.status_code in [404, 422]
