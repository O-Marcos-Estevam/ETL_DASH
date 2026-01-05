# Environment Variables

## Server Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `ETL_HOST` | `0.0.0.0` | Server bind address |
| `ETL_PORT` | `4001` | Server port |
| `ETL_DEBUG` | `false` | Enable debug mode (enables /docs) |
| `ETL_CORS_ORIGINS` | `http://localhost:4000,...` | Comma-separated allowed origins |
| `ETL_LOG_LEVEL` | `INFO` | Log level (DEBUG, INFO, WARNING, ERROR) |

## Execution Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `ETL_TIMEOUT` | `3600` | Default job timeout in seconds (1 hour) |
| `ETL_POLL_INTERVAL` | `2.0` | Worker poll interval in seconds |

## Multiprocessing Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `ETL_MAX_CONCURRENT_JOBS` | `1` | Max concurrent jobs. `1` = single mode, `>1` = pool mode |
| `ETL_JOB_SLOT_TIMEOUT` | `14400` | Timeout for orphan jobs in seconds (4 hours) |
| `ETL_JOB_CLEANUP_INTERVAL` | `300` | Cleanup check interval in seconds (5 min) |

## Redis Configuration (Optional)

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_ENABLED` | `false` | Enable distributed WebSocket via Redis |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection URL |
| `REDIS_CHANNEL_PREFIX` | `etl` | Prefix for Redis streams |
| `REDIS_POOL_SIZE` | `10` | Redis connection pool size |
| `REDIS_SOCKET_TIMEOUT` | `5.0` | Redis socket timeout in seconds |

## Authentication Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `JWT_SECRET_KEY` | (required) | Secret key for JWT tokens |
| `ETL_MASTER_KEY` | (required) | Master key for encryption |
| `AUTH_REQUIRED` | `false` | Require authentication for WebSocket |

## Usage Examples

### Single Mode (Default)

```bash
# Just run with defaults
python -m uvicorn app:app --host 0.0.0.0 --port 4001
```

### Pool Mode (4 concurrent jobs)

```bash
ETL_MAX_CONCURRENT_JOBS=4 python -m uvicorn app:app
```

### Pool Mode with Redis (Horizontal Scaling)

```bash
ETL_MAX_CONCURRENT_JOBS=4 \
REDIS_ENABLED=true \
REDIS_URL=redis://redis-server:6379/0 \
python -m uvicorn app:app
```

### Windows (cmd)

```cmd
set ETL_MAX_CONCURRENT_JOBS=4
set REDIS_ENABLED=true
set REDIS_URL=redis://localhost:6379/0
python -m uvicorn app:app
```

### Windows (PowerShell)

```powershell
$env:ETL_MAX_CONCURRENT_JOBS = "4"
$env:REDIS_ENABLED = "true"
$env:REDIS_URL = "redis://localhost:6379/0"
python -m uvicorn app:app
```

## Rollback

Both multiprocessing and Redis can be instantly disabled:

```bash
# Disable multiprocessing (back to single mode)
ETL_MAX_CONCURRENT_JOBS=1

# Disable Redis (back to local WebSocket)
REDIS_ENABLED=false
```

No code changes or restart delays required.
