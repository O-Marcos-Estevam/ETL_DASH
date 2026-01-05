# ETL Dashboard Backend - Architecture

## Overview

The ETL Dashboard Backend is a FastAPI application that manages ETL pipeline execution, real-time monitoring via WebSocket, and system configuration.

## Core Features

### 1. Job Execution System

The backend supports two execution modes:

#### Single Mode (Default)
- `ETL_MAX_CONCURRENT_JOBS=1`
- One job at a time
- Simple sequential processing
- Retrocompatible with original behavior

#### Pool Mode
- `ETL_MAX_CONCURRENT_JOBS>1` (e.g., 4)
- Multiple concurrent jobs
- Slot-based execution with isolated executor instances
- Automatic cleanup of orphaned jobs

```
Pool Mode Architecture:

                    ┌─────────────────┐
                    │  JobPoolManager │
                    │   (Coordinator) │
                    └────────┬────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
    ┌────▼────┐        ┌────▼────┐        ┌────▼────┐
    │  Slot 0 │        │  Slot 1 │        │  Slot N │
    │Executor │        │Executor │        │Executor │
    └────┬────┘        └────┬────┘        └────┬────┘
         │                   │                   │
         └───────────────────┼───────────────────┘
                             │
                    ┌────────▼────────┐
                    │    Database     │
                    │   (SQLite WAL)  │
                    └─────────────────┘
```

### 2. Database Layer

SQLite with WAL (Write-Ahead Logging) mode for concurrent access:

- **Connection Pool**: Thread-local connections with WAL mode
- **Atomic Job Acquisition**: `BEGIN IMMEDIATE` transactions prevent race conditions
- **Slot Assignment**: Jobs are assigned to specific slots during execution
- **Cleanup**: Automatic cleanup of stale jobs (configurable timeout)

### 3. WebSocket Real-Time Updates

Two modes supported:

#### Local Mode (Default)
- `REDIS_ENABLED=false`
- Broadcasts to WebSocket clients on same instance
- No external dependencies

#### Distributed Mode
- `REDIS_ENABLED=true`
- Uses Redis Streams for cross-instance messaging
- Circuit Breaker pattern for resilient fallback
- Consumer Groups ensure each instance receives messages

```
Distributed Mode Architecture:

┌─────────────────────────────────────────────────────────────────┐
│                      Redis Streams                               │
│              ┌─────────────────────────┐                        │
│              │ Stream: etl:events      │                        │
│              │ - Persists messages     │                        │
│              │ - Consumer groups       │                        │
│              └───────────┬─────────────┘                        │
│         ┌────────────────┼────────────────┐                     │
│         │                │                │                     │
│    ┌────▼────┐     ┌────▼────┐     ┌────▼────┐                 │
│    │Instance1│     │Instance2│     │Instance3│                 │
│    │Consumer │     │Consumer │     │Consumer │                 │
│    │Group:ws │     │Group:ws │     │Group:ws │                 │
│    └─────────┘     └─────────┘     └─────────┘                 │
└─────────────────────────────────────────────────────────────────┘
```

### 4. Circuit Breaker Pattern

Prevents cascading failures when Redis is unavailable:

```
States:
  CLOSED -> Normal operation, requests pass through
  OPEN   -> Service down, fallback immediately
  HALF_OPEN -> Testing recovery

Flow:
  [CLOSED] --failures >= threshold--> [OPEN]
  [OPEN] --timeout elapsed--> [HALF_OPEN]
  [HALF_OPEN] --success--> [CLOSED]
  [HALF_OPEN] --failure--> [OPEN]
```

## Key Components

### Services

| File | Purpose |
|------|---------|
| `services/worker.py` | Background worker (single/pool mode) |
| `services/pool.py` | JobPoolManager for concurrent execution |
| `services/executor.py` | ETL script execution via subprocess |
| `services/redis_client.py` | Redis Streams client |
| `services/distributed_ws.py` | Distributed WebSocket manager |
| `services/circuit_breaker.py` | Circuit breaker for resilience |

### Core

| File | Purpose |
|------|---------|
| `core/database.py` | SQLite operations with slot support |
| `config.py` | Centralized configuration |

### Routers

| File | Endpoints |
|------|-----------|
| `routers/execution.py` | `/api/execute`, `/api/cancel`, `/api/jobs`, `/api/pool/*` |
| `routers/sistemas.py` | `/api/sistemas` |
| `routers/credentials.py` | `/api/credentials`, `/api/paths` |
| `routers/config.py` | `/api/config` |
| `auth/router.py` | `/api/auth/*` |

## API Endpoints

### Execution

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/execute` | Start ETL pipeline (admin) |
| POST | `/api/execute/{sistema}` | Execute single system (admin) |
| POST | `/api/cancel/{job_id}` | Cancel running job (admin) |
| GET | `/api/jobs` | List jobs (viewer) |
| GET | `/api/jobs/{job_id}` | Get job details (viewer) |
| GET | `/api/pool/status` | Worker/pool status (viewer) |
| GET | `/api/pool/metrics` | Execution metrics (viewer) |

### Monitoring

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/ws/stats` | WebSocket manager statistics |
| WS | `/ws` | Real-time logs and status |

## Feature Flags

Both multiprocessing and Redis features use feature flags for easy rollback:

| Feature | How to Disable |
|---------|----------------|
| Multiprocessing | `ETL_MAX_CONCURRENT_JOBS=1` |
| Redis Distributed | `REDIS_ENABLED=false` |

Both changes are instant and require no code changes.

## Testing

Run tests:

```bash
# All tests
pytest backend/tests/ -v

# Integration tests only
pytest backend/tests/integration/ -v

# Specific test file
pytest backend/tests/integration/test_concurrent_jobs.py -v
pytest backend/tests/integration/test_distributed_ws.py -v
```

## Security

- JWT authentication required for protected endpoints
- Rate limiting middleware
- Security headers middleware
- CORS configuration for allowed origins
