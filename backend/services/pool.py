"""
Job Pool Manager - Manages concurrent execution of ETL jobs

Provides slot-based job execution with:
- Configurable number of concurrent workers (slots)
- Isolated executor instances per slot
- Automatic cleanup of orphan jobs
- WebSocket broadcast integration
"""
import asyncio
import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional, Callable, Any, List
from datetime import datetime

from core import database
from services.executor import ETLExecutor
from services.sistemas import get_sistema_service
from models.sistema import SistemaStatus
import services.state as state_service

logger = logging.getLogger(__name__)


class SlotStatus(str, Enum):
    """Status of a worker slot"""
    IDLE = "idle"
    RUNNING = "running"
    ERROR = "error"


@dataclass
class WorkerSlot:
    """Represents a single execution slot"""
    slot_id: int
    status: SlotStatus = SlotStatus.IDLE
    current_job_id: Optional[int] = None
    executor: Optional[ETLExecutor] = None
    task: Optional[asyncio.Task] = None
    started_at: Optional[datetime] = None


class JobPoolManager:
    """
    Manages a pool of workers for concurrent job execution.

    Features:
    - Configurable slots (1 to N)
    - Process isolation per slot
    - Automatic cleanup of orphan jobs
    - WebSocket event broadcasting
    - Thread-safe state management via asyncio.Lock
    """

    def __init__(self, max_workers: int = 4, poll_interval: float = 2.0):
        """
        Args:
            max_workers: Maximum number of concurrent jobs
            poll_interval: Polling interval in seconds
        """
        self.max_workers = max_workers
        self.poll_interval = poll_interval
        self.running = False

        # Execution slots
        self.slots: Dict[int, WorkerSlot] = {
            i: WorkerSlot(slot_id=i) for i in range(max_workers)
        }

        # State protection lock
        self._lock = asyncio.Lock()

        # Control tasks
        self._coordinator_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None

        logger.info(f"JobPoolManager created with {max_workers} slots")

    async def start(self):
        """Starts the pool manager"""
        if self.running:
            logger.warning("Pool manager is already running")
            return

        self.running = True

        # Main coordinator task - assigns jobs to available slots
        self._coordinator_task = asyncio.create_task(
            self._coordinator_loop(),
            name="pool_coordinator"
        )

        # Cleanup task - removes orphan jobs periodically
        from config import settings
        self._cleanup_task = asyncio.create_task(
            self._cleanup_loop(settings.JOB_CLEANUP_INTERVAL),
            name="pool_cleanup"
        )

        logger.info(f"JobPoolManager started with {self.max_workers} workers")

    async def stop(self):
        """Gracefully stops the pool manager"""
        self.running = False

        # Cancel control tasks
        for task in [self._coordinator_task, self._cleanup_task]:
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        # Cancel running jobs
        async with self._lock:
            for slot in self.slots.values():
                if slot.status == SlotStatus.RUNNING:
                    if slot.executor:
                        slot.executor.cancel()
                    if slot.task:
                        slot.task.cancel()
                        try:
                            await slot.task
                        except asyncio.CancelledError:
                            pass

        logger.info("JobPoolManager stopped")

    async def _coordinator_loop(self):
        """Main loop - assigns jobs to available slots"""
        logger.info("Coordinator loop started")

        while self.running:
            try:
                # Find available slots
                async with self._lock:
                    idle_slots = [
                        slot for slot in self.slots.values()
                        if slot.status == SlotStatus.IDLE
                    ]

                # Try to assign jobs to free slots
                for slot in idle_slots:
                    job = database.acquire_job_for_slot(slot.slot_id)

                    if job:
                        logger.info(f"Job #{job['id']} assigned to slot {slot.slot_id}")

                        # Start execution in separate task
                        async with self._lock:
                            slot.task = asyncio.create_task(
                                self._execute_job_in_slot(slot, job),
                                name=f"job_{job['id']}_slot_{slot.slot_id}"
                            )

                # Wait before checking again
                await asyncio.sleep(self.poll_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in coordinator loop: {e}")
                await asyncio.sleep(self.poll_interval * 2)

    async def _execute_job_in_slot(self, slot: WorkerSlot, job: dict):
        """
        Executes a job in a specific slot.

        Args:
            slot: The worker slot to use
            job: Job dict from database
        """
        job_id = job["id"]

        # Update slot state
        async with self._lock:
            slot.status = SlotStatus.RUNNING
            slot.current_job_id = job_id
            slot.started_at = datetime.now()
            slot.executor = ETLExecutor(slot_id=slot.slot_id)

        logger.info(f"Slot {slot.slot_id}: Starting job #{job_id}")

        # Parse parameters
        try:
            params = json.loads(job["params"]) if job["params"] else {}
        except json.JSONDecodeError:
            params = {}

        sistemas = params.get("sistemas", [])

        # Update system status
        sistema_service = get_sistema_service()
        for sistema_id in sistemas:
            sistema_service.update_status(sistema_id, SistemaStatus.RUNNING, 0, "Executando...")
            await self._broadcast_status(sistema_id, "RUNNING", 0, "Executando...")

        start_time = datetime.now()

        # Log callback (includes slot_id)
        async def log_callback(log_entry: dict):
            database.append_log(job_id, f"[{log_entry['level']}] [{log_entry['sistema']}] {log_entry['mensagem']}")
            log_entry["job_id"] = job_id
            log_entry["slot_id"] = slot.slot_id
            await self._broadcast_log(log_entry)

            # Update system status based on log level
            sistema = log_entry.get("sistema", "").lower()
            if sistema and sistema not in ("sistema", "stdout", "stderr"):
                level = log_entry.get("level", "INFO")
                if level == "SUCCESS":
                    await self._broadcast_status(sistema, "SUCCESS", 100, log_entry["mensagem"])
                elif level == "ERROR":
                    await self._broadcast_status(sistema, "ERROR", 0, log_entry["mensagem"])

        try:
            success = await slot.executor.execute(params, log_callback)

            duration = int((datetime.now() - start_time).total_seconds())
            final_status = "completed" if success else "error"

            database.update_job_status(job_id, final_status)
            database.release_job_slot(job_id)

            # Update system status
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

            await self._broadcast_job_complete(job_id, final_status, duration)
            logger.info(f"Slot {slot.slot_id}: Job #{job_id} finished: {final_status} ({duration}s)")

        except asyncio.CancelledError:
            logger.warning(f"Slot {slot.slot_id}: Job #{job_id} cancelled")
            database.update_job_status(job_id, "cancelled", "Cancelado pelo usuario")
            database.release_job_slot(job_id)
            raise

        except Exception as e:
            logger.error(f"Slot {slot.slot_id}: Error in job #{job_id}: {e}")
            database.update_job_status(job_id, "error", str(e))
            database.release_job_slot(job_id)

            for sistema_id in sistemas:
                sistema_service.update_status(sistema_id, SistemaStatus.ERROR, 0, f"Erro: {e}")
                await self._broadcast_status(sistema_id, "ERROR", 0, f"Erro: {e}")

        finally:
            # Reset slot state
            async with self._lock:
                slot.status = SlotStatus.IDLE
                slot.current_job_id = None
                slot.executor = None
                slot.task = None
                slot.started_at = None

    async def _cleanup_loop(self, interval: int):
        """Loop for cleaning up orphan jobs"""
        from config import settings

        while self.running:
            try:
                await asyncio.sleep(interval)

                stale_ids = database.cleanup_stale_jobs(settings.JOB_SLOT_TIMEOUT)

                if stale_ids:
                    logger.warning(f"Cleanup: {len(stale_ids)} orphan jobs removed: {stale_ids}")

                    for job_id in stale_ids:
                        await self._broadcast_job_complete(job_id, "error", 0)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")

    def cancel_job(self, job_id: int) -> bool:
        """
        Cancels a specific job.

        Args:
            job_id: The job ID to cancel

        Returns:
            True if job was found and cancelled
        """
        for slot in self.slots.values():
            if slot.current_job_id == job_id and slot.executor:
                slot.executor.cancel()
                logger.info(f"Job #{job_id} cancelled in slot {slot.slot_id}")
                return True
        return False

    def get_status(self) -> dict:
        """Returns status of all slots"""
        return {
            "max_workers": self.max_workers,
            "running": self.running,
            "slots": [
                {
                    "slot_id": slot.slot_id,
                    "status": slot.status.value,
                    "job_id": slot.current_job_id,
                    "started_at": slot.started_at.isoformat() if slot.started_at else None
                }
                for slot in self.slots.values()
            ],
            "active_count": len([s for s in self.slots.values() if s.status == SlotStatus.RUNNING]),
            "idle_count": len([s for s in self.slots.values() if s.status == SlotStatus.IDLE])
        }

    # === Broadcast helpers ===

    async def _broadcast_log(self, log_entry: dict):
        ws_manager = state_service.ws_manager
        if ws_manager:
            try:
                await ws_manager.broadcast_log(log_entry)
            except Exception as e:
                logger.error(f"Error broadcasting log: {e}")

    async def _broadcast_status(self, sistema_id: str, status: str, progresso: int, mensagem: str):
        ws_manager = state_service.ws_manager
        if ws_manager:
            try:
                await ws_manager.broadcast_status(sistema_id, status, progresso, mensagem)
            except Exception as e:
                logger.error(f"Error broadcasting status: {e}")

    async def _broadcast_job_complete(self, job_id: int, status: str, duracao: int):
        ws_manager = state_service.ws_manager
        if ws_manager:
            try:
                await ws_manager.broadcast_job_complete(job_id, status, duracao)
            except Exception as e:
                logger.error(f"Error broadcasting job_complete: {e}")


# Singleton (None if MAX_CONCURRENT_JOBS=1)
_pool_instance: Optional[JobPoolManager] = None


def get_pool_manager() -> Optional[JobPoolManager]:
    """Returns pool manager if multiprocessing is enabled"""
    global _pool_instance
    return _pool_instance


def create_pool_manager(max_workers: int, poll_interval: float = 2.0) -> JobPoolManager:
    """Creates and returns pool manager"""
    global _pool_instance
    _pool_instance = JobPoolManager(max_workers, poll_interval)
    return _pool_instance
