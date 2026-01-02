"""
Testes unitarios para BackgroundWorker
"""
import pytest
import asyncio
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.worker import BackgroundWorker, get_worker


class TestBackgroundWorkerInit:
    """Testes para inicializacao do worker"""

    def test_default_poll_interval(self):
        """Worker tem poll_interval padrao de 2.0"""
        worker = BackgroundWorker()
        assert worker.poll_interval == 2.0

    def test_custom_poll_interval(self):
        """Worker aceita poll_interval customizado"""
        worker = BackgroundWorker(poll_interval=5.0)
        assert worker.poll_interval == 5.0

    def test_initial_state(self):
        """Worker inicia com estado correto"""
        worker = BackgroundWorker()
        assert worker.running is False
        assert worker.current_job_id is None
        assert worker._task is None


class TestBackgroundWorkerStart:
    """Testes para start/stop do worker"""

    @pytest.mark.asyncio
    async def test_start_sets_running_true(self):
        """Start define running como True"""
        worker = BackgroundWorker()

        with patch.object(worker, '_run_loop', new_callable=AsyncMock):
            await worker.start()
            assert worker.running is True
            await worker.stop()

    @pytest.mark.asyncio
    async def test_start_creates_task(self):
        """Start cria task asyncio"""
        worker = BackgroundWorker()

        with patch.object(worker, '_run_loop', new_callable=AsyncMock):
            await worker.start()
            assert worker._task is not None
            await worker.stop()

    @pytest.mark.asyncio
    async def test_start_when_already_running(self):
        """Start nao reinicia se ja estiver rodando"""
        worker = BackgroundWorker()
        worker.running = True

        with patch.object(worker, '_run_loop', new_callable=AsyncMock) as mock_loop:
            await worker.start()
            mock_loop.assert_not_called()

    @pytest.mark.asyncio
    async def test_stop_sets_running_false(self):
        """Stop define running como False"""
        worker = BackgroundWorker()

        with patch.object(worker, '_run_loop', new_callable=AsyncMock):
            await worker.start()
            await worker.stop()
            assert worker.running is False


class TestBackgroundWorkerProcessJob:
    """Testes para processamento de jobs"""

    @pytest.fixture
    def worker(self):
        """Fixture do worker"""
        return BackgroundWorker()

    @pytest.fixture
    def sample_job(self):
        """Job de exemplo"""
        return {
            "id": 1,
            "type": "etl_pipeline",
            "params": '{"sistemas": ["maps"]}',
            "status": "pending"
        }

    @pytest.mark.asyncio
    async def test_process_job_sets_current_job_id(self, worker, sample_job):
        """Processa job define current_job_id"""
        with patch("services.worker.database") as mock_db, \
             patch("services.worker.get_executor") as mock_exec, \
             patch("services.worker.get_sistema_service") as mock_sis, \
             patch.object(worker, "_broadcast_status", new_callable=AsyncMock), \
             patch.object(worker, "_broadcast_log", new_callable=AsyncMock), \
             patch.object(worker, "_broadcast_job_complete", new_callable=AsyncMock):

            mock_exec.return_value.execute = AsyncMock(return_value=True)
            mock_sis.return_value.update_status = MagicMock()

            await worker._process_job(sample_job)

            # current_job_id deve ser None apos processar (limpo no finally)
            assert worker.current_job_id is None

    @pytest.mark.asyncio
    async def test_process_job_updates_status_to_running(self, worker, sample_job):
        """Processa job atualiza status para running"""
        with patch("services.worker.database") as mock_db, \
             patch("services.worker.get_executor") as mock_exec, \
             patch("services.worker.get_sistema_service") as mock_sis, \
             patch.object(worker, "_broadcast_status", new_callable=AsyncMock), \
             patch.object(worker, "_broadcast_log", new_callable=AsyncMock), \
             patch.object(worker, "_broadcast_job_complete", new_callable=AsyncMock):

            mock_exec.return_value.execute = AsyncMock(return_value=True)
            mock_sis.return_value.update_status = MagicMock()

            await worker._process_job(sample_job)

            mock_db.update_job_status.assert_any_call(1, "running")

    @pytest.mark.asyncio
    async def test_process_job_success_updates_completed(self, worker, sample_job):
        """Job com sucesso atualiza status para completed"""
        with patch("services.worker.database") as mock_db, \
             patch("services.worker.get_executor") as mock_exec, \
             patch("services.worker.get_sistema_service") as mock_sis, \
             patch.object(worker, "_broadcast_status", new_callable=AsyncMock), \
             patch.object(worker, "_broadcast_log", new_callable=AsyncMock), \
             patch.object(worker, "_broadcast_job_complete", new_callable=AsyncMock):

            mock_exec.return_value.execute = AsyncMock(return_value=True)
            mock_sis.return_value.update_status = MagicMock()

            await worker._process_job(sample_job)

            mock_db.update_job_status.assert_any_call(1, "completed")

    @pytest.mark.asyncio
    async def test_process_job_failure_updates_error(self, worker, sample_job):
        """Job com falha atualiza status para error"""
        with patch("services.worker.database") as mock_db, \
             patch("services.worker.get_executor") as mock_exec, \
             patch("services.worker.get_sistema_service") as mock_sis, \
             patch.object(worker, "_broadcast_status", new_callable=AsyncMock), \
             patch.object(worker, "_broadcast_log", new_callable=AsyncMock), \
             patch.object(worker, "_broadcast_job_complete", new_callable=AsyncMock):

            mock_exec.return_value.execute = AsyncMock(return_value=False)
            mock_sis.return_value.update_status = MagicMock()

            await worker._process_job(sample_job)

            mock_db.update_job_status.assert_any_call(1, "error")

    @pytest.mark.asyncio
    async def test_process_job_broadcasts_job_complete(self, worker, sample_job):
        """Job completo envia broadcast"""
        with patch("services.worker.database") as mock_db, \
             patch("services.worker.get_executor") as mock_exec, \
             patch("services.worker.get_sistema_service") as mock_sis, \
             patch.object(worker, "_broadcast_status", new_callable=AsyncMock), \
             patch.object(worker, "_broadcast_log", new_callable=AsyncMock), \
             patch.object(worker, "_broadcast_job_complete", new_callable=AsyncMock) as mock_broadcast:

            mock_exec.return_value.execute = AsyncMock(return_value=True)
            mock_sis.return_value.update_status = MagicMock()

            await worker._process_job(sample_job)

            mock_broadcast.assert_called_once()
            args = mock_broadcast.call_args[0]
            assert args[0] == 1  # job_id
            assert args[1] == "completed"  # status


class TestBackgroundWorkerCancel:
    """Testes para cancelamento de jobs"""

    def test_cancel_calls_executor_cancel(self):
        """Cancel chama executor.cancel()"""
        worker = BackgroundWorker()
        worker.current_job_id = 1

        with patch("services.worker.get_executor") as mock_exec:
            mock_executor = MagicMock()
            mock_exec.return_value = mock_executor

            worker.cancel_current_job()

            mock_executor.cancel.assert_called_once()

    def test_cancel_no_current_job(self):
        """Cancel sem job nao faz nada"""
        worker = BackgroundWorker()
        worker.current_job_id = None

        with patch("services.worker.get_executor") as mock_exec:
            worker.cancel_current_job()
            mock_exec.assert_not_called()


class TestGetWorker:
    """Testes para singleton get_worker"""

    def test_returns_worker_instance(self):
        """get_worker retorna BackgroundWorker"""
        with patch("services.worker._worker_instance", None):
            worker = get_worker()
            assert isinstance(worker, BackgroundWorker)

    def test_returns_same_instance(self):
        """get_worker retorna mesma instancia"""
        with patch("services.worker._worker_instance", None):
            worker1 = get_worker()
            worker2 = get_worker()
            assert worker1 is worker2
