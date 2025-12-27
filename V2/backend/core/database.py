"""
Database module - SQLite operations for job queue
"""
import sqlite3
import json
from datetime import datetime
from pathlib import Path

# Caminho para o banco na pasta data/
DB_PATH = Path(__file__).parent.parent / "data" / "tasks.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
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

def add_job(job_type, params):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    now = datetime.now().isoformat()
    params_json = json.dumps(params)
    
    cursor.execute('''
    INSERT INTO jobs (type, params, status, created_at)
    VALUES (?, ?, ?, ?)
    ''', (job_type, params_json, 'pending', now))
    
    job_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return job_id

def get_job(job_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM jobs WHERE id = ?', (job_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None

def update_job_status(job_id, status, error=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    now = datetime.now().isoformat()

    if status == 'running':
        cursor.execute('UPDATE jobs SET status = ?, started_at = ? WHERE id = ?', (status, now, job_id))
    elif status in ['completed', 'error', 'cancelled']:
        cursor.execute('UPDATE jobs SET status = ?, finished_at = ?, error_message = ? WHERE id = ?', (status, now, error, job_id))
    else:
        cursor.execute('UPDATE jobs SET status = ? WHERE id = ?', (status, job_id))

    conn.commit()
    conn.close()

def append_log(job_id, message):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor() # A bit inefficient to open/close for every log, but safer for concurrent access in SQLite
    
    # Append to existing logs
    cursor.execute('UPDATE jobs SET logs = logs || ? || "\n" WHERE id = ?', (message, job_id))
    
    conn.commit()
    conn.close()

def get_pending_job():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM jobs WHERE status = "pending" ORDER BY created_at ASC LIMIT 1')
    row = cursor.fetchone()
    conn.close()

    if row:
        return dict(row)
    return None


def get_running_job():
    """Retorna job em execucao, se houver"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM jobs WHERE status = "running" ORDER BY started_at DESC LIMIT 1')
    row = cursor.fetchone()
    conn.close()

    if row:
        return dict(row)
    return None


def list_jobs(status=None, limit=20, offset=0):
    """Lista jobs com filtro opcional por status"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
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
    conn.close()

    return [dict(row) for row in rows]


def get_next_pending_job():
    """Retorna proximo job pendente para processamento (se nao houver job rodando)"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Verificar se nao ha job rodando
    cursor.execute('SELECT COUNT(*) as count FROM jobs WHERE status = "running"')
    running = cursor.fetchone()

    if running and running['count'] > 0:
        conn.close()
        return None

    # Buscar proximo pendente
    cursor.execute('SELECT * FROM jobs WHERE status = "pending" ORDER BY created_at ASC LIMIT 1')
    row = cursor.fetchone()
    conn.close()

    if row:
        return dict(row)
    return None
