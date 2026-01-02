"""
Authentication Database Operations

SQLite operations for users, tokens, and rate limiting.
"""
import sqlite3
import hashlib
from datetime import datetime, timedelta
from typing import Optional, List
from contextlib import contextmanager
import os

from .models import UserInDB, UserRole, UserResponse
from .config import auth_settings

# Database path (same directory as tasks.db)
DB_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "data", "tasks.db")
)


@contextmanager
def get_db():
    """Context manager for database connections"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_auth_tables():
    """Initialize authentication tables in the database"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    with get_db() as conn:
        cursor = conn.cursor()

        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE,
                hashed_password TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'viewer',
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_login DATETIME,
                failed_attempts INTEGER DEFAULT 0,
                locked_until DATETIME
            )
        ''')

        # Refresh tokens table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS refresh_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token_hash TEXT NOT NULL,
                expires_at DATETIME NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                revoked BOOLEAN DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')

        # Rate limiting table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rate_limits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT NOT NULL,
                endpoint TEXT NOT NULL,
                request_count INTEGER DEFAULT 1,
                window_start DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(key, endpoint)
            )
        ''')

        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user ON refresh_tokens(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_refresh_tokens_hash ON refresh_tokens(token_hash)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_rate_limits_key ON rate_limits(key, endpoint)')


# User Operations

def get_user_by_username(username: str) -> Optional[UserInDB]:
    """Get user by username"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        row = cursor.fetchone()

        if row:
            return UserInDB(
                id=row['id'],
                username=row['username'],
                email=row['email'],
                hashed_password=row['hashed_password'],
                role=UserRole(row['role']),
                is_active=bool(row['is_active']),
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else datetime.now(),
                last_login=datetime.fromisoformat(row['last_login']) if row['last_login'] else None
            )
        return None


def get_user_by_id(user_id: int) -> Optional[UserInDB]:
    """Get user by ID"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        row = cursor.fetchone()

        if row:
            return UserInDB(
                id=row['id'],
                username=row['username'],
                email=row['email'],
                hashed_password=row['hashed_password'],
                role=UserRole(row['role']),
                is_active=bool(row['is_active']),
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else datetime.now(),
                last_login=datetime.fromisoformat(row['last_login']) if row['last_login'] else None
            )
        return None


def create_user(
    username: str,
    hashed_password: str,
    email: Optional[str] = None,
    role: UserRole = UserRole.VIEWER
) -> UserResponse:
    """Create a new user"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (username, email, hashed_password, role)
            VALUES (?, ?, ?, ?)
        ''', (username, email, hashed_password, role.value))

        user_id = cursor.lastrowid
        return UserResponse(
            id=user_id,
            username=username,
            email=email,
            role=role,
            is_active=True,
            created_at=datetime.now(),
            last_login=None
        )


def get_all_users() -> List[UserResponse]:
    """Get all users"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users ORDER BY created_at DESC')
        rows = cursor.fetchall()

        return [
            UserResponse(
                id=row['id'],
                username=row['username'],
                email=row['email'],
                role=UserRole(row['role']),
                is_active=bool(row['is_active']),
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else datetime.now(),
                last_login=datetime.fromisoformat(row['last_login']) if row['last_login'] else None
            )
            for row in rows
        ]


def update_last_login(user_id: int):
    """Update user's last login timestamp"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE users SET last_login = ? WHERE id = ?
        ''', (datetime.now().isoformat(), user_id))


def update_password(user_id: int, hashed_password: str):
    """Update user's password"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE users SET hashed_password = ?, updated_at = ? WHERE id = ?
        ''', (hashed_password, datetime.now().isoformat(), user_id))


def update_user(user_id: int, email: Optional[str] = None, role: Optional[UserRole] = None, is_active: Optional[bool] = None):
    """Update user details"""
    with get_db() as conn:
        cursor = conn.cursor()
        updates = []
        params = []

        if email is not None:
            updates.append("email = ?")
            params.append(email)
        if role is not None:
            updates.append("role = ?")
            params.append(role.value)
        if is_active is not None:
            updates.append("is_active = ?")
            params.append(1 if is_active else 0)

        if updates:
            updates.append("updated_at = ?")
            params.append(datetime.now().isoformat())
            params.append(user_id)

            cursor.execute(f'''
                UPDATE users SET {", ".join(updates)} WHERE id = ?
            ''', params)


def delete_user(user_id: int):
    """Delete a user"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))


# Account Lockout Operations

def increment_failed_attempts(user_id: int):
    """Increment failed login attempts"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE users SET failed_attempts = failed_attempts + 1 WHERE id = ?
        ''', (user_id,))

        # Check if should lock
        cursor.execute('SELECT failed_attempts FROM users WHERE id = ?', (user_id,))
        row = cursor.fetchone()

        if row and row['failed_attempts'] >= auth_settings.MAX_FAILED_ATTEMPTS:
            lock_until = datetime.now() + timedelta(minutes=auth_settings.LOCKOUT_DURATION_MINUTES)
            cursor.execute('''
                UPDATE users SET locked_until = ? WHERE id = ?
            ''', (lock_until.isoformat(), user_id))


def reset_failed_attempts(user_id: int):
    """Reset failed login attempts on successful login"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE users SET failed_attempts = 0, locked_until = NULL WHERE id = ?
        ''', (user_id,))


def is_account_locked(username: str) -> bool:
    """Check if account is locked"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT locked_until FROM users WHERE username = ?', (username,))
        row = cursor.fetchone()

        if row and row['locked_until']:
            locked_until = datetime.fromisoformat(row['locked_until'])
            if locked_until > datetime.now():
                return True
            # Lockout expired, reset
            cursor.execute('''
                UPDATE users SET locked_until = NULL, failed_attempts = 0
                WHERE username = ?
            ''', (username,))

        return False


# Refresh Token Operations

def store_refresh_token(user_id: int, token_hash: str, expires_days: int):
    """Store refresh token hash"""
    expires_at = datetime.now() + timedelta(days=expires_days)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO refresh_tokens (user_id, token_hash, expires_at)
            VALUES (?, ?, ?)
        ''', (user_id, token_hash, expires_at.isoformat()))


def is_refresh_token_valid(token: str, user_id: int) -> bool:
    """Check if refresh token is valid (exists, not revoked, not expired)"""
    token_hash = hashlib.sha256(token.encode()).hexdigest()

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM refresh_tokens
            WHERE token_hash = ? AND user_id = ? AND revoked = 0 AND expires_at > ?
        ''', (token_hash, user_id, datetime.now().isoformat()))

        return cursor.fetchone() is not None


def revoke_refresh_token(token: str):
    """Revoke a specific refresh token"""
    token_hash = hashlib.sha256(token.encode()).hexdigest()

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE refresh_tokens SET revoked = 1 WHERE token_hash = ?
        ''', (token_hash,))


def revoke_all_user_tokens(user_id: int):
    """Revoke all refresh tokens for a user"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE refresh_tokens SET revoked = 1 WHERE user_id = ?
        ''', (user_id,))


def cleanup_expired_tokens():
    """Remove expired refresh tokens"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            DELETE FROM refresh_tokens WHERE expires_at < ? OR revoked = 1
        ''', (datetime.now().isoformat(),))


# Rate Limiting Operations

def check_rate_limit(key: str, endpoint: str, limit: int, window_seconds: int = 60) -> bool:
    """
    Check if request should be rate limited.

    Returns True if rate limited, False if allowed.
    """
    now = datetime.now()
    window_start = now - timedelta(seconds=window_seconds)

    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute('''
            SELECT request_count, window_start FROM rate_limits
            WHERE key = ? AND endpoint = ?
        ''', (key, endpoint))

        row = cursor.fetchone()

        if row:
            stored_window = datetime.fromisoformat(row['window_start'])

            if stored_window < window_start:
                # Window expired, reset
                cursor.execute('''
                    UPDATE rate_limits SET request_count = 1, window_start = ?
                    WHERE key = ? AND endpoint = ?
                ''', (now.isoformat(), key, endpoint))
                return False
            elif row['request_count'] >= limit:
                return True
            else:
                cursor.execute('''
                    UPDATE rate_limits SET request_count = request_count + 1
                    WHERE key = ? AND endpoint = ?
                ''', (key, endpoint))
                return False
        else:
            cursor.execute('''
                INSERT INTO rate_limits (key, endpoint, request_count, window_start)
                VALUES (?, ?, 1, ?)
            ''', (key, endpoint, now.isoformat()))
            return False


def cleanup_rate_limits():
    """Remove old rate limit entries"""
    cutoff = datetime.now() - timedelta(hours=1)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            DELETE FROM rate_limits WHERE window_start < ?
        ''', (cutoff.isoformat(),))


# Initialize tables on import
init_auth_tables()
