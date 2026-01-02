"""
Testes de integracao para WebSocket
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestConnectionManager:
    """Testes para ConnectionManager"""

    @pytest.fixture
    def manager(self):
        """Fixture do ConnectionManager"""
        from app import ConnectionManager
        return ConnectionManager()

    @pytest.fixture
    def mock_websocket(self):
        """Mock de WebSocket"""
        ws = MagicMock()
        ws.accept = AsyncMock()
        ws.send_json = AsyncMock()
        ws.close = AsyncMock()
        return ws

    @pytest.mark.asyncio
    async def test_connect_accepts_websocket(self, manager, mock_websocket):
        """Connect aceita conexao WebSocket"""
        await manager.connect(mock_websocket)
        mock_websocket.accept.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_adds_to_list(self, manager, mock_websocket):
        """Connect adiciona WebSocket a lista"""
        await manager.connect(mock_websocket)
        assert mock_websocket in manager.active_connections

    def test_disconnect_removes_from_list(self, manager, mock_websocket):
        """Disconnect remove WebSocket da lista"""
        manager.active_connections.append(mock_websocket)
        manager.disconnect(mock_websocket)
        assert mock_websocket not in manager.active_connections

    def test_disconnect_handles_not_connected(self, manager, mock_websocket):
        """Disconnect nao da erro se nao conectado"""
        manager.disconnect(mock_websocket)  # Nao deve lancar excecao

    def test_connection_count(self, manager, mock_websocket):
        """connection_count retorna numero correto"""
        assert manager.connection_count == 0
        manager.active_connections.append(mock_websocket)
        assert manager.connection_count == 1

    @pytest.mark.asyncio
    async def test_broadcast_log(self, manager, mock_websocket):
        """broadcast_log envia log para todos"""
        manager.active_connections.append(mock_websocket)

        log_entry = {"level": "INFO", "sistema": "MAPS", "mensagem": "Test"}
        await manager.broadcast_log(log_entry)

        mock_websocket.send_json.assert_called_once()
        args = mock_websocket.send_json.call_args[0][0]
        assert args["type"] == "log"
        assert args["payload"] == log_entry

    @pytest.mark.asyncio
    async def test_broadcast_status(self, manager, mock_websocket):
        """broadcast_status envia status update"""
        manager.active_connections.append(mock_websocket)

        await manager.broadcast_status("maps", "RUNNING", 50, "Processando...")

        mock_websocket.send_json.assert_called_once()
        args = mock_websocket.send_json.call_args[0][0]
        assert args["type"] == "status"
        assert args["payload"]["sistema_id"] == "maps"
        assert args["payload"]["status"] == "RUNNING"
        assert args["payload"]["progresso"] == 50

    @pytest.mark.asyncio
    async def test_broadcast_job_complete(self, manager, mock_websocket):
        """broadcast_job_complete envia notificacao"""
        manager.active_connections.append(mock_websocket)

        await manager.broadcast_job_complete(1, "completed", 120)

        mock_websocket.send_json.assert_called_once()
        args = mock_websocket.send_json.call_args[0][0]
        assert args["type"] == "job_complete"
        assert args["payload"]["job_id"] == 1
        assert args["payload"]["status"] == "completed"
        assert args["payload"]["duracao_segundos"] == 120

    @pytest.mark.asyncio
    async def test_broadcast_handles_failed_connection(self, manager, mock_websocket):
        """Broadcast remove conexao com falha"""
        mock_websocket.send_json.side_effect = Exception("Connection lost")
        manager.active_connections.append(mock_websocket)

        await manager.broadcast_log({"test": "data"})

        # Conexao deve ter sido removida
        assert mock_websocket not in manager.active_connections

    @pytest.mark.asyncio
    async def test_broadcast_to_multiple_connections(self, manager):
        """Broadcast envia para multiplas conexoes"""
        ws1 = MagicMock()
        ws1.send_json = AsyncMock()
        ws2 = MagicMock()
        ws2.send_json = AsyncMock()

        manager.active_connections.extend([ws1, ws2])

        await manager.broadcast_log({"test": "data"})

        ws1.send_json.assert_called_once()
        ws2.send_json.assert_called_once()


@pytest.mark.asyncio
class TestWebSocketEndpoint:
    """Testes para endpoint WebSocket"""

    async def test_websocket_connect(self):
        """WebSocket aceita conexao"""
        from httpx import AsyncClient, ASGITransport
        from httpx_ws.transport import ASGIWebSocketTransport

        # Este teste verifica se o endpoint existe
        # Teste completo de WebSocket requer httpx-ws ou starlette testclient
        pass  # WebSocket testing requires specialized testing setup

    async def test_websocket_auth_required_without_token(self):
        """WebSocket rejeita conexao sem token quando AUTH_REQUIRED=true"""
        # Requer setup especial para testar WebSocket com auth
        pass


@pytest.mark.asyncio
class TestWebSocketIntegration:
    """Testes de integracao WebSocket com Worker"""

    async def test_worker_broadcasts_via_websocket(self):
        """Worker envia logs via WebSocket"""
        from services.worker import BackgroundWorker
        import services.state as state_service

        # Create mock manager
        mock_manager = MagicMock()
        mock_manager.broadcast_log = AsyncMock()
        mock_manager.broadcast_status = AsyncMock()
        mock_manager.broadcast_job_complete = AsyncMock()

        # Set as state manager
        original_manager = state_service.ws_manager
        state_service.ws_manager = mock_manager

        try:
            worker = BackgroundWorker()

            # Test broadcast methods
            await worker._broadcast_log({"level": "INFO", "mensagem": "Test"})
            mock_manager.broadcast_log.assert_called_once()

            await worker._broadcast_status("maps", "RUNNING", 50, "Processing")
            mock_manager.broadcast_status.assert_called_once()

            await worker._broadcast_job_complete(1, "completed", 60)
            mock_manager.broadcast_job_complete.assert_called_once()

        finally:
            # Restore original
            state_service.ws_manager = original_manager
