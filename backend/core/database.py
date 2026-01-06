"""
Database module - SQLite operations for job queue
Supports multiprocessing with connection pooling and WAL mode
"""
import sqlite3
import json
import threading
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List, Any

logger = logging.getLogger(__name__)

# Caminho para o banco na pasta data/
DB_PATH = Path(__file__).parent.parent / "data" / "tasks.db"

# === SQLITE VERSION CHECK ===
SQLITE_VERSION = tuple(map(int, sqlite3.sqlite_version.split('.')))
SUPPORTS_RETURNING = SQLITE_VERSION >= (3, 35, 0)
logger.info(f"SQLite version: {sqlite3.sqlite_version} (RETURNING: {SUPPORTS_RETURNING})")

# === CONNECTION POOL (thread-local) ===
_local = threading.local()


def get_connection() -> sqlite3.Connection:
    """
    Returns a thread-local SQLite connection with WAL mode enabled.
    WAL mode allows concurrent reads during writes.
    """
    if not hasattr(_local, 'conn') or _local.conn is None:
        _local.conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        _local.conn.row_factory = sqlite3.Row
        # Enable WAL mode for better concurrency
        _local.conn.execute("PRAGMA journal_mode=WAL")
        _local.conn.execute("PRAGMA busy_timeout=5000")  # 5s timeout for locks
    return _local.conn


def close_connection():
    """Closes the thread-local connection if it exists."""
    if hasattr(_local, 'conn') and _local.conn is not None:
        _local.conn.close()
        _local.conn = None

def init_db():
    """
    Initializes the database schema.
    Creates tables if they don't exist and runs migrations.
    """
    # Garantir que o diretorio data/ existe
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Enable WAL mode for better concurrency
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA busy_timeout=5000")

    # Create Jobs Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT NOT NULL,
        params TEXT,
        status TEXT DEFAULT 'pending', -- pending, running, completed, error
        logs TEXT DEFAULT '',
        error_message TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        started_at DATETIME,
        finished_at DATETIME
    )
    ''')

    conn.commit()
    conn.close()

    # Run migrations for multiprocessing support
    migrate_db()

def add_job(job_type, params):
    conn = get_connection()
    cursor = conn.cursor()

    now = datetime.now().isoformat()
    params_json = json.dumps(params)

    cursor.execute('''
    INSERT INTO jobs (type, params, status, created_at)
    VALUES (?, ?, ?, ?)
    ''', (job_type, params_json, 'pending', now))

    job_id = cursor.lastrowid
    conn.commit()
    return job_id

def get_job(job_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM jobs WHERE id = ?', (job_id,))
    row = cursor.fetchone()

    if row:
        return dict(row)
    return None

def update_job_status(job_id, status, error=None):
    conn = get_connection()
    cursor = conn.cursor()

    now = datetime.now().isoformat()

    if status == 'running':
        cursor.execute('UPDATE jobs SET status = ?, started_at = ? WHERE id = ?', (status, now, job_id))
    elif status in ['completed', 'error', 'cancelled']:
        cursor.execute('UPDATE jobs SET status = ?, finished_at = ?, error_message = ? WHERE id = ?', (status, now, error, job_id))
    else:
        cursor.execute('UPDATE jobs SET status = ? WHERE id = ?', (status, job_id))

    conn.commit()

def append_log(job_id, message):
    conn = get_connection()
    cursor = conn.cursor()

    # Append to existing logs
    cursor.execute('UPDATE jobs SET logs = logs || ? || "\n" WHERE id = ?', (message, job_id))

    conn.commit()

def get_pending_job():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM jobs WHERE status = "pending" ORDER BY created_at ASC LIMIT 1')
    row = cursor.fetchone()

    if row:
        return dict(row)
    return None


def get_running_job():
    """Retorna job em execucao, se houver"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM jobs WHERE status = "running" ORDER BY started_at DESC LIMIT 1')
    row = cursor.fetchone()

    if row:
        return dict(row)
    return None


def list_jobs(status=None, limit=20, offset=0):
    """Lista jobs com filtro opcional por status"""
    conn = get_connection()
    cursor = conn.cursor()

    if status:
        cursor.execute(
            'SELECT * FROM jobs WHERE status = ? ORDER BY created_at DESC LIMIT ? OFFSET ?',
            (status, limit, offset)
        )
    else:
        cursor.execute(
            'SELECT * FROM jobs ORDER BY created_at DESC LIMIT ? OFFSET ?',
            (limit, offset)
        )

    rows = cursor.fetchall()

    return [dict(row) for row in rows]


def get_next_pending_job() -> Optional[Dict[str, Any]]:
    """
    Atomically acquires next pending job for single-mode processing.
    Uses BEGIN IMMEDIATE for exclusive locking to prevent race conditions.

    Only acquires if no other job is currently running (single mode constraint).

    Returns:
        Job dict or None if no pending jobs or if a job is already running
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Start exclusive transaction to prevent race conditions
        cursor.execute("BEGIN IMMEDIATE")

        # Check if any job is already running (single mode constraint)
        cursor.execute('SELECT COUNT(*) FROM jobs WHERE status = "running"')
        running_count = cursor.fetchone()[0]

        if running_count > 0:
            cursor.execute("ROLLBACK")
            return None

        # Find next pending job
        cursor.execute('''
            SELECT id FROM jobs
            WHERE status = "pending"
            ORDER BY created_at ASC
            LIMIT 1
        ''')
        row = cursor.fetchone()

        if not row:
            cursor.execute("ROLLBACK")
            return None

        job_id = row[0]
        now = datetime.now().isoformat()

        # Atomically mark job as running
        cursor.execute('''
            UPDATE jobs
            SET status = "running",
                started_at = ?
            WHERE id = ?
        ''', (now, job_id))

        # Fetch complete job record
        cursor.execute('SELECT * FROM jobs WHERE id = ?', (job_id,))
        job_row = cursor.fetchone()

        cursor.execute("COMMIT")

        if job_row:
            logger.info(f"[SINGLE] Acquired job #{job_id}")
            return dict(job_row)
        return None

    except Exception as e:
        logger.error(f"[SINGLE] Error acquiring job: {e}")
        try:
            cursor.execute("ROLLBACK")
        except:
            pass
        return None


# =============================================================================
# MULTIPROCESSING SUPPORT - Slot-based job acquisition
# =============================================================================

def migrate_db():
    """
    Executes retrocompatible schema migrations.
    Adds columns for multiprocessing support without breaking existing data.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Enable WAL mode for better concurrency
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA busy_timeout=5000")

    # Check if worker_slot column exists
    cursor.execute("PRAGMA table_info(jobs)")
    columns = [col[1] for col in cursor.fetchall()]

    if "worker_slot" not in columns:
        logger.info("[MIGRATION] Adding multiprocessing columns...")

        # Add columns for multiprocessing
        cursor.execute("ALTER TABLE jobs ADD COLUMN worker_slot INTEGER DEFAULT NULL")
        cursor.execute("ALTER TABLE jobs ADD COLUMN locked_at TEXT DEFAULT NULL")

        # Create index for efficient queries
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_status_slot ON jobs(status, worker_slot)")

        conn.commit()
        logger.info("[MIGRATION] Added worker_slot and locked_at columns")

    conn.close()


def get_running_jobs_count() -> int:
    """Returns the count of currently running jobs."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) FROM jobs WHERE status = "running"')
    count = cursor.fetchone()[0]

    return count


def get_pending_jobs_count() -> int:
    """Returns the count of pending jobs in queue."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) FROM jobs WHERE status = "pending"')
    count = cursor.fetchone()[0]

    return count


def get_completed_jobs_count(hours: int = 24) -> int:
    """Returns the count of completed jobs in the last N hours."""
    conn = get_connection()
    cursor = conn.cursor()

    threshold = (datetime.now() - timedelta(hours=hours)).isoformat()
    cursor.execute(
        'SELECT COUNT(*) FROM jobs WHERE status = "completed" AND finished_at > ?',
        (threshold,)
    )
    count = cursor.fetchone()[0]

    return count


def get_available_slot(max_slots: int) -> Optional[int]:
    """
    Returns an available slot (0 to max_slots-1).
    Returns None if all slots are occupied.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Get slots in use
    cursor.execute(
        'SELECT worker_slot FROM jobs WHERE status = "running" AND worker_slot IS NOT NULL'
    )
    used_slots = {row[0] for row in cursor.fetchall()}

    # Find first free slot
    for slot in range(max_slots):
        if slot not in used_slots:
            return slot

    return None


def acquire_job_for_slot(slot: int) -> Optional[Dict[str, Any]]:
    """
    Atomically acquires the next pending job for a specific slot.
    Uses BEGIN IMMEDIATE for exclusive locking to prevent race conditions.

    Compatible with all SQLite versions (no RETURNING clause).

    Args:
        slot: The worker slot ID (0 to max_workers-1)

    Returns:
        Job dict or None if no pending jobs
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Start exclusive transaction
        cursor.execute("BEGIN IMMEDIATE")

        # Find next pending job
        cursor.execute('''
            SELECT id FROM jobs
            WHERE status = "pending"
            ORDER BY created_at ASC
            LIMIT 1
        ''')
        row = cursor.fetchone()

        if not row:
            cursor.execute("ROLLBACK")
            return None

        job_id = row[0]
        now = datetime.now().isoformat()

        # Update job to running state with slot assignment
        cursor.execute('''
            UPDATE jobs
            SET status = "running",
                worker_slot = ?,
                locked_at = ?,
                started_at = ?
            WHERE id = ?
        ''', (slot, now, now, job_id))

        # Fetch the complete job record
        cursor.execute('SELECT * FROM jobs WHERE id = ?', (job_id,))
        job_row = cursor.fetchone()

        cursor.execute("COMMIT")

        if job_row:
            logger.info(f"[SLOT {slot}] Acquired job #{job_id}")
            return dict(job_row)
        return None

    except Exception as e:
        logger.error(f"[SLOT {slot}] Error acquiring job: {e}")
        try:
            cursor.execute("ROLLBACK")
        except:
            pass
        raise


def release_job_slot(job_id: int):
    """
    Releases the slot assignment for a job (on completion or error).

    Args:
        job_id: The job ID to release
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        'UPDATE jobs SET worker_slot = NULL, locked_at = NULL WHERE id = ?',
        (job_id,)
    )
    conn.commit()
    logger.debug(f"Released slot for job #{job_id}")


def cleanup_stale_jobs(timeout_seconds: int) -> List[int]:
    """
    Marks stale/orphaned jobs as error and releases their slots.
    A job is considered stale if it's been running longer than timeout_seconds.

    Args:
        timeout_seconds: Maximum allowed runtime before considering job stale

    Returns:
        List of job IDs that were cleaned up
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Calculate threshold time
    threshold = (datetime.now() - timedelta(seconds=timeout_seconds)).isoformat()

    # Find stale jobs
    cursor.execute('''
        SELECT id FROM jobs
        WHERE status = "running"
        AND locked_at IS NOT NULL
        AND locked_at < ?
    ''', (threshold,))

    stale_ids = [row[0] for row in cursor.fetchall()]

    if stale_ids:
        now = datetime.now().isoformat()
        placeholders = ','.join('?' * len(stale_ids))

        cursor.execute(f'''
            UPDATE jobs
            SET status = "error",
                error_message = "Job timeout - cleaned up automatically",
                worker_slot = NULL,
                locked_at = NULL,
                finished_at = ?
            WHERE id IN ({placeholders})
        ''', [now] + stale_ids)

        conn.commit()
        logger.warning(f"[CLEANUP] Marked {len(stale_ids)} stale jobs as error: {stale_ids}")

    return stale_ids


def get_slot_status() -> List[Dict[str, Any]]:
    """
    Returns status of all currently occupied slots.

    Returns:
        List of dicts with slot info: {slot_id, job_id, started_at, locked_at}
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT worker_slot, id, started_at, locked_at
        FROM jobs
        WHERE status = "running" AND worker_slot IS NOT NULL
        ORDER BY worker_slot
    ''')

    return [
        {
            "slot_id": row[0],
            "job_id": row[1],
            "started_at": row[2],
            "locked_at": row[3]
        }
        for row in cursor.fetchall()
    ]
