"""
Integration tests for concurrent job execution (multiprocessing)

Tests:
- Race condition prevention in job acquisition
- Slot-based job execution
- Cleanup of stale/orphan jobs
- Pool manager functionality
"""
import pytest
import asyncio
import sys
import threading
import time
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, AsyncMock
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core import database


class TestSlotBasedJobAcquisition:
    """Tests for atomic slot-based job acquisition"""

    def test_acquire_job_for_slot_success(self, test_db):
        """Job can be acquired by a slot"""
        job_id = test_db.add_job("etl_pipeline", {"sistemas": ["amplis"]})

        acquired = test_db.acquire_job_for_slot(0)

        assert acquired is not None
        assert acquired["id"] == job_id
        assert acquired["status"] == "running"
        assert acquired["worker_slot"] == 0
        assert acquired["locked_at"] is not None

    def test_acquire_job_returns_none_when_empty(self, test_db):
        """Returns None when no pending jobs"""
        acquired = test_db.acquire_job_for_slot(0)
        assert acquired is None

    def test_acquire_job_oldest_first(self, test_db):
        """Acquires oldest pending job first"""
        id1 = test_db.add_job("etl_pipeline", {"order": 1})
        id2 = test_db.add_job("etl_pipeline", {"order": 2})
        id3 = test_db.add_job("etl_pipeline", {"order": 3})

        acquired = test_db.acquire_job_for_slot(0)

        assert acquired["id"] == id1

    def test_multiple_slots_acquire_different_jobs(self, test_db):
        """Different slots acquire different jobs"""
        id1 = test_db.add_job("etl_pipeline", {"job": 1})
        id2 = test_db.add_job("etl_pipeline", {"job": 2})
        id3 = test_db.add_job("etl_pipeline", {"job": 3})

        # Acquire jobs sequentially in different slots
        job1 = test_db.acquire_job_for_slot(0)
        job2 = test_db.acquire_job_for_slot(1)
        job3 = test_db.acquire_job_for_slot(2)

        # Each slot gets a different job
        acquired_ids = {job1["id"], job2["id"], job3["id"]}
        assert len(acquired_ids) == 3
        assert acquired_ids == {id1, id2, id3}

    def test_no_race_condition_sequential(self, test_db):
        """Sequential acquisition doesn't allow double-acquire"""
        job_id = test_db.add_job("etl_pipeline", {"sistemas": ["amplis"]})

        # First slot acquires
        job1 = test_db.acquire_job_for_slot(0)
        # Second slot tries to acquire same job
        job2 = test_db.acquire_job_for_slot(1)

        assert job1 is not None
        assert job1["id"] == job_id
        assert job2 is None  # No more pending jobs

    def test_no_race_condition_concurrent_threads(self, test_db):
        """Multiple threads trying to acquire same job - only one succeeds"""
        # Create single job
        job_id = test_db.add_job("etl_pipeline", {"sistemas": ["test"]})

        results = []
        connections = []
        lock = threading.Lock()

        def try_acquire(slot_id):
            # Need separate connection per thread for SQLite
            import sqlite3
            conn = sqlite3.connect(str(test_db.DB_PATH), check_same_thread=False, timeout=10)
            conn.row_factory = sqlite3.Row

            with lock:
                connections.append(conn)

            try:
                conn.execute("PRAGMA busy_timeout=5000")
                cursor = conn.cursor()
                cursor.execute("BEGIN IMMEDIATE")

                cursor.execute('''
                    SELECT id FROM jobs
                    WHERE status = "pending"
                    ORDER BY created_at ASC
                    LIMIT 1
                ''')
                row = cursor.fetchone()

                if not row:
                    cursor.execute("ROLLBACK")
                    with lock:
                        results.append(None)
                    return

                acq_job_id = row[0]
                now = datetime.now().isoformat()

                cursor.execute('''
                    UPDATE jobs
                    SET status = "running",
                        worker_slot = ?,
                        locked_at = ?,
                        started_at = ?
                    WHERE id = ?
                ''', (slot_id, now, now, acq_job_id))

                cursor.execute('SELECT * FROM jobs WHERE id = ?', (acq_job_id,))
                job_row = cursor.fetchone()
                cursor.execute("COMMIT")

                with lock:
                    results.append(dict(job_row) if job_row else None)

            except Exception:
                try:
                    conn.rollback()
                except:
                    pass
                with lock:
                    results.append(None)

        # Launch 5 threads trying to acquire same job
        threads = []
        for i in range(5):
            t = threading.Thread(target=try_acquire, args=(i,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join(timeout=10)

        # Close all connections after threads finish (important for Windows cleanup)
        time.sleep(0.1)  # Small delay for threads to fully complete
        for conn in connections:
            try:
                conn.close()
            except:
                pass

        # Only one should succeed
        successful = [r for r in results if r is not None]
        assert len(successful) == 1
        assert successful[0]["id"] == job_id


class TestSlotRelease:
    """Tests for slot release functionality"""

    def test_release_job_slot(self, test_db):
        """Slot is released after job completion"""
        job_id = test_db.add_job("etl_pipeline", {"sistemas": ["test"]})
        test_db.acquire_job_for_slot(0)

        # Release slot
        test_db.release_job_slot(job_id)

        # Check job slot is null
        job = test_db.get_job(job_id)
        assert job["worker_slot"] is None
        assert job["locked_at"] is None

    def test_slot_can_be_reused_after_release(self, test_db):
        """After release, slot can acquire new job"""
        id1 = test_db.add_job("etl_pipeline", {"job": 1})
        id2 = test_db.add_job("etl_pipeline", {"job": 2})

        # Slot 0 acquires first job
        job1 = test_db.acquire_job_for_slot(0)
        assert job1["id"] == id1

        # Release slot
        test_db.release_job_slot(id1)

        # Slot 0 can now acquire second job
        job2 = test_db.acquire_job_for_slot(0)
        assert job2["id"] == id2


class TestJobCounts:
    """Tests for count functions"""

    def test_get_running_jobs_count(self, test_db):
        """Counts running jobs correctly"""
        # Create 3 jobs, set 2 as running
        id1 = test_db.add_job("etl_pipeline", {})
        id2 = test_db.add_job("etl_pipeline", {})
        id3 = test_db.add_job("etl_pipeline", {})

        test_db.update_job_status(id1, "running")
        test_db.update_job_status(id2, "running")

        count = test_db.get_running_jobs_count()
        assert count == 2

    def test_get_pending_jobs_count(self, test_db):
        """Counts pending jobs correctly"""
        test_db.add_job("etl_pipeline", {})
        test_db.add_job("etl_pipeline", {})
        id3 = test_db.add_job("etl_pipeline", {})

        test_db.update_job_status(id3, "running")

        count = test_db.get_pending_jobs_count()
        assert count == 2

    def test_get_completed_jobs_count(self, test_db):
        """Counts completed jobs in time window"""
        id1 = test_db.add_job("etl_pipeline", {})
        id2 = test_db.add_job("etl_pipeline", {})
        id3 = test_db.add_job("etl_pipeline", {})

        test_db.update_job_status(id1, "completed")
        test_db.update_job_status(id2, "completed")
        test_db.update_job_status(id3, "error")

        count = test_db.get_completed_jobs_count(hours=24)
        assert count == 2


class TestAvailableSlot:
    """Tests for slot availability"""

    def test_get_available_slot_all_free(self, test_db):
        """Returns slot 0 when all free"""
        slot = test_db.get_available_slot(4)
        assert slot == 0

    def test_get_available_slot_some_used(self, test_db):
        """Returns first free slot"""
        # Occupy slots 0 and 1
        id1 = test_db.add_job("etl_pipeline", {})
        id2 = test_db.add_job("etl_pipeline", {})

        test_db.acquire_job_for_slot(0)
        test_db.acquire_job_for_slot(1)

        # Next available should be slot 2
        slot = test_db.get_available_slot(4)
        assert slot == 2

    def test_get_available_slot_all_used(self, test_db):
        """Returns None when all slots occupied"""
        # Create and acquire 4 jobs in 4 slots
        for i in range(4):
            test_db.add_job("etl_pipeline", {"slot": i})
            test_db.acquire_job_for_slot(i)

        slot = test_db.get_available_slot(4)
        assert slot is None


class TestSlotStatus:
    """Tests for slot status queries"""

    def test_get_slot_status_empty(self, test_db):
        """Returns empty list when no running jobs"""
        status = test_db.get_slot_status()
        assert status == []

    def test_get_slot_status_with_running(self, test_db):
        """Returns slot info for running jobs"""
        id1 = test_db.add_job("etl_pipeline", {"job": 1})
        id2 = test_db.add_job("etl_pipeline", {"job": 2})

        test_db.acquire_job_for_slot(0)
        test_db.acquire_job_for_slot(2)

        status = test_db.get_slot_status()

        assert len(status) == 2
        slot_ids = {s["slot_id"] for s in status}
        assert slot_ids == {0, 2}


class TestCleanupStaleJobs:
    """Tests for orphan/stale job cleanup"""

    def test_cleanup_stale_jobs_none_stale(self, test_db):
        """No cleanup when jobs are recent"""
        job_id = test_db.add_job("etl_pipeline", {})
        test_db.acquire_job_for_slot(0)

        # Cleanup with 1 hour timeout - job was just started
        cleaned = test_db.cleanup_stale_jobs(3600)

        assert cleaned == []
        job = test_db.get_job(job_id)
        assert job["status"] == "running"

    def test_cleanup_stale_jobs_marks_as_error(self, test_db):
        """Stale jobs are marked as error"""
        job_id = test_db.add_job("etl_pipeline", {})
        test_db.acquire_job_for_slot(0)

        # Manually set locked_at to past
        import sqlite3
        conn = sqlite3.connect(str(test_db.DB_PATH))
        old_time = (datetime.now() - timedelta(hours=3)).isoformat()
        conn.execute('UPDATE jobs SET locked_at = ? WHERE id = ?', (old_time, job_id))
        conn.commit()
        conn.close()

        # Cleanup with 1 hour timeout
        cleaned = test_db.cleanup_stale_jobs(3600)

        assert job_id in cleaned
        job = test_db.get_job(job_id)
        assert job["status"] == "error"
        assert "timeout" in job["error_message"].lower()
        assert job["worker_slot"] is None

    def test_cleanup_does_not_affect_active_jobs(self, test_db):
        """Active jobs (recent locked_at) are not cleaned"""
        id1 = test_db.add_job("etl_pipeline", {"job": 1})
        id2 = test_db.add_job("etl_pipeline", {"job": 2})

        test_db.acquire_job_for_slot(0)  # id1
        test_db.acquire_job_for_slot(1)  # id2

        # Make id1 stale
        import sqlite3
        conn = sqlite3.connect(str(test_db.DB_PATH))
        old_time = (datetime.now() - timedelta(hours=3)).isoformat()
        conn.execute('UPDATE jobs SET locked_at = ? WHERE id = ?', (old_time, id1))
        conn.commit()
        conn.close()

        # Cleanup
        cleaned = test_db.cleanup_stale_jobs(3600)

        assert id1 in cleaned
        assert id2 not in cleaned

        job1 = test_db.get_job(id1)
        job2 = test_db.get_job(id2)

        assert job1["status"] == "error"
        assert job2["status"] == "running"


class TestMigration:
    """Tests for database migration"""

    def test_migrate_adds_columns(self, test_db):
        """Migration adds worker_slot and locked_at columns"""
        import sqlite3
        conn = sqlite3.connect(str(test_db.DB_PATH))
        cursor = conn.cursor()

        cursor.execute("PRAGMA table_info(jobs)")
        columns = [col[1] for col in cursor.fetchall()]
        conn.close()

        assert "worker_slot" in columns
        assert "locked_at" in columns

    def test_migrate_is_idempotent(self, test_db):
        """Running migration twice doesn't error"""
        # Migration already ran in test_db fixture
        # Running again should not raise
        test_db.migrate_db()

        # Should still work
        job_id = test_db.add_job("etl_pipeline", {})
        test_db.acquire_job_for_slot(0)

        job = test_db.get_job(job_id)
        assert job["worker_slot"] == 0


@pytest.mark.asyncio
class TestPoolManagerBasic:
    """Basic tests for JobPoolManager"""

    async def test_pool_manager_creation(self):
        """Pool manager can be created"""
        from services.pool import JobPoolManager

        pool = JobPoolManager(max_workers=4)

        assert pool.max_workers == 4
        assert len(pool.slots) == 4
        assert not pool.running

    async def test_pool_manager_start_stop(self):
        """Pool manager starts and stops"""
        from services.pool import JobPoolManager

        pool = JobPoolManager(max_workers=2, poll_interval=0.1)

        await pool.start()
        assert pool.running

        await pool.stop()
        assert not pool.running

    async def test_pool_manager_get_status(self):
        """Pool manager returns status"""
        from services.pool import JobPoolManager

        pool = JobPoolManager(max_workers=3)

        status = pool.get_status()

        assert status["max_workers"] == 3
        assert len(status["slots"]) == 3
        assert status["active_count"] == 0
        assert status["idle_count"] == 3


@pytest.mark.asyncio
class TestPoolManagerJobExecution:
    """Tests for job execution in pool"""

    async def test_pool_assigns_job_to_slot(self, test_db):
        """Pool assigns pending job to available slot"""
        from services.pool import JobPoolManager, SlotStatus
        import services.state as state_service

        # Mock ws_manager
        state_service.ws_manager = MagicMock()
        state_service.ws_manager.broadcast_log = AsyncMock()
        state_service.ws_manager.broadcast_status = AsyncMock()
        state_service.ws_manager.broadcast_job_complete = AsyncMock()

        # Create job
        job_id = test_db.add_job("etl_pipeline", {"sistemas": ["test"], "dry_run": True})

        # Create pool with mocked executor
        pool = JobPoolManager(max_workers=2, poll_interval=0.1)

        # Mock executor to complete quickly
        with patch('services.pool.ETLExecutor') as MockExecutor:
            mock_executor = MagicMock()
            mock_executor.execute = AsyncMock(return_value=True)
            MockExecutor.return_value = mock_executor

            await pool.start()

            # Wait for job to be picked up
            await asyncio.sleep(0.5)

            await pool.stop()

        # Job should be completed
        job = test_db.get_job(job_id)
        assert job["status"] == "completed"

    async def test_pool_cancel_job(self, test_db):
        """Pool can cancel running job"""
        from services.pool import JobPoolManager, SlotStatus

        pool = JobPoolManager(max_workers=2)

        # Manually set up a slot with a mock executor
        pool.slots[0].status = SlotStatus.RUNNING
        pool.slots[0].current_job_id = 123
        pool.slots[0].executor = MagicMock()
        pool.slots[0].executor.cancel = MagicMock()

        # Cancel the job
        result = pool.cancel_job(123)

        assert result is True
        pool.slots[0].executor.cancel.assert_called_once()

    async def test_pool_cancel_nonexistent_job(self, test_db):
        """Cancelling non-existent job returns False"""
        from services.pool import JobPoolManager

        pool = JobPoolManager(max_workers=2)

        result = pool.cancel_job(99999)

        assert result is False


@pytest.mark.asyncio
class TestPoolManagerBroadcast:
    """Tests for broadcast helpers in pool manager"""

    async def test_broadcast_log_success(self):
        """Broadcast log calls ws_manager"""
        from services.pool import JobPoolManager
        import services.state as state_service

        mock_manager = MagicMock()
        mock_manager.broadcast_log = AsyncMock()
        original = state_service.ws_manager
        state_service.ws_manager = mock_manager

        try:
            pool = JobPoolManager(max_workers=2)
            log_entry = {"level": "INFO", "message": "Test"}

            await pool._broadcast_log(log_entry)

            mock_manager.broadcast_log.assert_called_once_with(log_entry)
        finally:
            state_service.ws_manager = original

    async def test_broadcast_log_handles_error(self):
        """Broadcast log handles exceptions gracefully"""
        from services.pool import JobPoolManager
        import services.state as state_service

        mock_manager = MagicMock()
        mock_manager.broadcast_log = AsyncMock(side_effect=Exception("WS Error"))
        original = state_service.ws_manager
        state_service.ws_manager = mock_manager

        try:
            pool = JobPoolManager(max_workers=2)
            # Should not raise
            await pool._broadcast_log({"level": "INFO"})
        finally:
            state_service.ws_manager = original

    async def test_broadcast_log_no_manager(self):
        """Broadcast log handles missing ws_manager"""
        from services.pool import JobPoolManager
        import services.state as state_service

        original = state_service.ws_manager
        state_service.ws_manager = None

        try:
            pool = JobPoolManager(max_workers=2)
            # Should not raise
            await pool._broadcast_log({"level": "INFO"})
        finally:
            state_service.ws_manager = original

    async def test_broadcast_status_success(self):
        """Broadcast status calls ws_manager"""
        from services.pool import JobPoolManager
        import services.state as state_service

        mock_manager = MagicMock()
        mock_manager.broadcast_status = AsyncMock()
        original = state_service.ws_manager
        state_service.ws_manager = mock_manager

        try:
            pool = JobPoolManager(max_workers=2)

            await pool._broadcast_status("maps", "RUNNING", 50, "Processing")

            mock_manager.broadcast_status.assert_called_once_with(
                "maps", "RUNNING", 50, "Processing"
            )
        finally:
            state_service.ws_manager = original

    async def test_broadcast_status_handles_error(self):
        """Broadcast status handles exceptions gracefully"""
        from services.pool import JobPoolManager
        import services.state as state_service

        mock_manager = MagicMock()
        mock_manager.broadcast_status = AsyncMock(side_effect=Exception("Error"))
        original = state_service.ws_manager
        state_service.ws_manager = mock_manager

        try:
            pool = JobPoolManager(max_workers=2)
            # Should not raise
            await pool._broadcast_status("maps", "RUNNING", 50, "Processing")
        finally:
            state_service.ws_manager = original

    async def test_broadcast_job_complete_success(self):
        """Broadcast job_complete calls ws_manager"""
        from services.pool import JobPoolManager
        import services.state as state_service

        mock_manager = MagicMock()
        mock_manager.broadcast_job_complete = AsyncMock()
        original = state_service.ws_manager
        state_service.ws_manager = mock_manager

        try:
            pool = JobPoolManager(max_workers=2)

            await pool._broadcast_job_complete(123, "completed", 60)

            mock_manager.broadcast_job_complete.assert_called_once_with(123, "completed", 60)
        finally:
            state_service.ws_manager = original

    async def test_broadcast_job_complete_handles_error(self):
        """Broadcast job_complete handles exceptions gracefully"""
        from services.pool import JobPoolManager
        import services.state as state_service

        mock_manager = MagicMock()
        mock_manager.broadcast_job_complete = AsyncMock(side_effect=Exception("Error"))
        original = state_service.ws_manager
        state_service.ws_manager = mock_manager

        try:
            pool = JobPoolManager(max_workers=2)
            # Should not raise
            await pool._broadcast_job_complete(123, "completed", 60)
        finally:
            state_service.ws_manager = original


@pytest.mark.asyncio
class TestPoolManagerSlotStatus:
    """Tests for slot status enum"""

    def test_slot_status_values(self):
        """SlotStatus has correct values"""
        from services.pool import SlotStatus

        assert SlotStatus.IDLE.value == "idle"
        assert SlotStatus.RUNNING.value == "running"
        assert SlotStatus.ERROR.value == "error"

    def test_worker_slot_defaults(self):
        """WorkerSlot has correct defaults"""
        from services.pool import WorkerSlot, SlotStatus

        slot = WorkerSlot(slot_id=0)

        assert slot.slot_id == 0
        assert slot.status == SlotStatus.IDLE
        assert slot.current_job_id is None
        assert slot.executor is None
        assert slot.task is None
        assert slot.started_at is None


@pytest.mark.asyncio
class TestPoolManagerSingleton:
    """Tests for pool manager singleton functions"""

    def test_get_pool_manager_none_initially(self):
        """get_pool_manager returns None initially"""
        from services.pool import get_pool_manager
        import services.pool as pool_module

        # Reset singleton
        pool_module._pool_instance = None

        result = get_pool_manager()
        assert result is None

    def test_create_pool_manager(self):
        """create_pool_manager creates and returns instance"""
        from services.pool import create_pool_manager, get_pool_manager
        import services.pool as pool_module

        # Reset singleton
        pool_module._pool_instance = None

        pool = create_pool_manager(max_workers=3, poll_interval=1.0)

        assert pool.max_workers == 3
        assert pool.poll_interval == 1.0
        assert get_pool_manager() is pool

    def test_create_pool_manager_overwrites(self):
        """create_pool_manager overwrites existing instance"""
        from services.pool import create_pool_manager, get_pool_manager

        pool1 = create_pool_manager(max_workers=2)
        pool2 = create_pool_manager(max_workers=4)

        assert get_pool_manager() is pool2
        assert pool2.max_workers == 4


@pytest.mark.asyncio
class TestPoolManagerStartStop:
    """Tests for start/stop lifecycle"""

    async def test_start_already_running(self):
        """Starting already running pool logs warning"""
        from services.pool import JobPoolManager

        pool = JobPoolManager(max_workers=2, poll_interval=0.1)
        await pool.start()

        try:
            # Starting again should not error
            await pool.start()
            assert pool.running
        finally:
            await pool.stop()

    async def test_stop_cancels_tasks(self):
        """Stop cancels coordinator and cleanup tasks"""
        from services.pool import JobPoolManager

        pool = JobPoolManager(max_workers=2, poll_interval=0.1)
        await pool.start()

        assert pool._coordinator_task is not None
        assert pool._cleanup_task is not None

        await pool.stop()

        assert not pool.running

    async def test_stop_cancels_running_jobs(self):
        """Stop cancels any running jobs"""
        from services.pool import JobPoolManager, SlotStatus

        pool = JobPoolManager(max_workers=2, poll_interval=0.1)

        # Manually set up a running slot with mock executor
        pool.slots[0].status = SlotStatus.RUNNING
        pool.slots[0].executor = MagicMock()
        pool.slots[0].executor.cancel = MagicMock()
        pool.slots[0].task = asyncio.create_task(asyncio.sleep(100))

        pool.running = True
        await pool.stop()

        pool.slots[0].executor.cancel.assert_called_once()


@pytest.mark.asyncio
class TestPoolManagerEdgeCases:
    """Tests for edge cases and error handling"""

    async def test_get_status_with_running_jobs(self):
        """Status correctly shows running job info"""
        from services.pool import JobPoolManager, SlotStatus
        from datetime import datetime

        pool = JobPoolManager(max_workers=3)

        # Set up slots with different states
        pool.slots[0].status = SlotStatus.RUNNING
        pool.slots[0].current_job_id = 123
        pool.slots[0].started_at = datetime.now()

        pool.slots[1].status = SlotStatus.IDLE

        pool.slots[2].status = SlotStatus.ERROR

        status = pool.get_status()

        assert status["max_workers"] == 3
        assert status["active_count"] == 1  # Only RUNNING counts as active
        assert status["idle_count"] == 1

        # Find the running slot
        running_slot = next(s for s in status["slots"] if s["slot_id"] == 0)
        assert running_slot["status"] == "running"
        assert running_slot["job_id"] == 123
        assert running_slot["started_at"] is not None

    async def test_cancel_job_in_correct_slot(self):
        """Cancel finds job in correct slot"""
        from services.pool import JobPoolManager, SlotStatus

        pool = JobPoolManager(max_workers=3)

        # Set up multiple running slots
        for i, job_id in enumerate([100, 200, 300]):
            pool.slots[i].status = SlotStatus.RUNNING
            pool.slots[i].current_job_id = job_id
            pool.slots[i].executor = MagicMock()
            pool.slots[i].executor.cancel = MagicMock()

        # Cancel job 200 (in slot 1)
        result = pool.cancel_job(200)

        assert result is True
        # Only slot 1's executor should be cancelled
        pool.slots[0].executor.cancel.assert_not_called()
        pool.slots[1].executor.cancel.assert_called_once()
        pool.slots[2].executor.cancel.assert_not_called()
