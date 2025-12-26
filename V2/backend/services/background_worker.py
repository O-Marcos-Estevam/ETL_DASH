"""
Background Worker - Processa jobs da fila em background
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Optional, Any

import sys
import os

# Garantir imports
_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

import database
from services.executor import get_executor
from services.sistema_service import get_sistema_service
from models.sistema import SistemaStatus
import services.state as state_service

logger = logging.getLogger(__name__)


class BackgroundWorker:
    """
    Worker que roda em background processando jobs da fila.
    Integra com WebSocket para enviar logs em tempo real.
    """

    def __init__(self, poll_interval: float = 2.0):
        """
        Args:
            poll_interval: Intervalo em segundos entre polls do banco
        """
        self.poll_interval = poll_interval
        self.running = False
        self.current_job_id: Optional[int] = None
        self._task: Optional[asyncio.Task] = None

    async def start(self):
        """Inicia o worker em background"""
        if self.running:
            logger.warning("Worker ja esta rodando")
            return

        self.running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("BackgroundWorker iniciado")

    async def stop(self):
        """Para o worker"""
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("BackgroundWorker parado")

    async def _run_loop(self):
        """Loop principal do worker"""
        logger.info("Worker loop iniciado - aguardando jobs...")

        while self.running:
            try:
                # Buscar proximo job pendente
                job = database.get_next_pending_job()

                if job:
                    await self._process_job(job)
                else:
                    # Aguardar antes de verificar novamente
                    await asyncio.sleep(self.poll_interval)

            except asyncio.CancelledError:
                logger.info("Worker loop cancelado")
                break
            except Exception as e:
                logger.error(f"Erro no worker loop: {e}")
                await asyncio.sleep(self.poll_interval * 2)

    async def _process_job(self, job: dict):
        """
        Processa um job da fila

        Args:
            job: Dict com dados do job do banco
        """
        job_id = job["id"]
        self.current_job_id = job_id

        logger.info(f"Processando job #{job_id}")

        # Parsear parametros
        try:
            params = json.loads(job["params"]) if job["params"] else {}
        except json.JSONDecodeError:
            params = {}

        sistemas = params.get("sistemas", [])

        # Marcar job como running
        database.update_job_status(job_id, "running")
        start_time = datetime.now()

        # Atualizar status dos sistemas
        sistema_service = get_sistema_service()
        for sistema_id in sistemas:
            sistema_service.update_status(
                sistema_id,
                SistemaStatus.RUNNING,
                0,
                "Executando..."
            )
            # Broadcast status via WebSocket
            await self._broadcast_status(sistema_id, "RUNNING", 0, "Executando...")

        # Callback para logs
        async def log_callback(log_entry: dict):
            # Salvar no banco
            msg = f"[{log_entry['level']}] [{log_entry['sistema']}] {log_entry['mensagem']}"
            database.append_log(job_id, msg)

            # Adicionar job_id ao log
            log_entry["job_id"] = job_id

            # Broadcast via WebSocket
            await self._broadcast_log(log_entry)

            # Atualizar status do sistema se identificado
            sistema = log_entry.get("sistema", "").lower()
            if sistema and sistema != "sistema" and sistema != "stdout":
                # Estimar progresso baseado no log (simplificado)
                level = log_entry.get("level", "INFO")
                if level == "SUCCESS":
                    await self._broadcast_status(sistema, "SUCCESS", 100, log_entry["mensagem"])
                elif level == "ERROR":
                    await self._broadcast_status(sistema, "ERROR", 0, log_entry["mensagem"])

        # Executar
        executor = get_executor()
        try:
            success = await executor.execute(params, log_callback)

            # Calcular duracao
            duration = int((datetime.now() - start_time).total_seconds())

            # Atualizar status final
            final_status = "completed" if success else "error"
            database.update_job_status(job_id, final_status)

            # Atualizar status dos sistemas
            for sistema_id in sistemas:
                sistema_service.update_status(
                    sistema_id,
                    SistemaStatus.SUCCESS if success else SistemaStatus.ERROR,
                    100 if success else 0,
                    "Concluido" if success else "Erro na execucao"
                )
                await self._broadcast_status(
                    sistema_id,
                    "SUCCESS" if success else "ERROR",
                    100 if success else 0,
                    "Concluido" if success else "Erro na execucao"
                )

            # Broadcast job complete
            await self._broadcast_job_complete(job_id, final_status, duration)

            logger.info(f"Job #{job_id} finalizado: {final_status} ({duration}s)")

        except Exception as e:
            logger.error(f"Erro ao processar job #{job_id}: {e}")
            database.update_job_status(job_id, "error", str(e))

            # Atualizar status dos sistemas para erro
            for sistema_id in sistemas:
                sistema_service.update_status(
                    sistema_id,
                    SistemaStatus.ERROR,
                    0,
                    f"Erro: {str(e)}"
                )
                await self._broadcast_status(sistema_id, "ERROR", 0, f"Erro: {str(e)}")

        finally:
            self.current_job_id = None

    async def _broadcast_log(self, log_entry: dict):
        """Envia log via WebSocket"""
        ws_manager = state_service.ws_manager
        if ws_manager:
            try:
                await ws_manager.broadcast_log(log_entry)
            except Exception as e:
                logger.error(f"Erro ao broadcast log: {e}")

    async def _broadcast_status(self, sistema_id: str, status: str, progresso: int, mensagem: str):
        """Envia status update via WebSocket"""
        ws_manager = state_service.ws_manager
        if ws_manager:
            try:
                await ws_manager.broadcast_status(sistema_id, status, progresso, mensagem)
            except Exception as e:
                logger.error(f"Erro ao broadcast status: {e}")

    async def _broadcast_job_complete(self, job_id: int, status: str, duracao: int):
        """Envia notificacao de job completo via WebSocket"""
        ws_manager = state_service.ws_manager
        if ws_manager:
            try:
                await ws_manager.broadcast_job_complete(job_id, status, duracao)
            except Exception as e:
                logger.error(f"Erro ao broadcast job_complete: {e}")

    def cancel_current_job(self):
        """Cancela job em execucao"""
        if self.current_job_id:
            executor = get_executor()
            executor.cancel()
            logger.info(f"Job #{self.current_job_id} cancelado")


# Singleton
_worker_instance: Optional[BackgroundWorker] = None


def get_worker() -> BackgroundWorker:
    """Retorna instancia singleton do BackgroundWorker"""
    global _worker_instance
    if _worker_instance is None:
        _worker_instance = BackgroundWorker()
    return _worker_instance
