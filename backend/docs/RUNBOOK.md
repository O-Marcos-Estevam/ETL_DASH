# Operations Runbook

## Startup

### Development Mode (Single)

```bash
cd backend
python -m uvicorn app:app --reload
```

### Development Mode (Pool)

```bash
cd backend
ETL_MAX_CONCURRENT_JOBS=4 python -m uvicorn app:app --reload
```

### Production Mode

```bash
cd backend
python -m uvicorn app:app --host 0.0.0.0 --port 4001
```

### With Redis (Distributed)

```bash
# Start Redis first
docker run -d --name redis -p 6379:6379 redis:7

# Start backend
REDIS_ENABLED=true python -m uvicorn app:app
```

## Health Checks

### API Health

```bash
curl http://localhost:4001/api/health
# Expected: {"status":"ok","version":"2.2.0"}
```

### WebSocket Stats

```bash
curl http://localhost:4001/api/ws/stats
# Shows Redis connection status if enabled
```

### Pool Metrics

```bash
curl http://localhost:4001/api/pool/metrics
# Shows slots, pending jobs, running jobs
```

## Monitoring

### View Pool Status

```bash
curl http://localhost:4001/api/pool/status
```

Response example (pool mode):
```json
{
  "mode": "pool",
  "running": true,
  "max_workers": 4,
  "slots": [
    {"slot_id": 0, "status": "running", "job_id": 123},
    {"slot_id": 1, "status": "idle", "job_id": null},
    {"slot_id": 2, "status": "idle", "job_id": null},
    {"slot_id": 3, "status": "idle", "job_id": null}
  ],
  "active_count": 1,
  "idle_count": 3
}
```

### View Jobs

```bash
# All jobs
curl http://localhost:4001/api/jobs

# Running jobs only
curl "http://localhost:4001/api/jobs?status=running"

# Pending jobs
curl "http://localhost:4001/api/jobs?status=pending"
```

## Troubleshooting

### Issue: Database Locked

**Symptom:** `sqlite3.OperationalError: database is locked`

**Solution:**
1. Ensure WAL mode is enabled (automatic on startup)
2. Increase busy timeout if needed (default: 5000ms)
3. Check for orphan connections

### Issue: Jobs Stuck in Running

**Symptom:** Jobs show "running" but no activity

**Diagnosis:**
```bash
curl http://localhost:4001/api/pool/status
```

**Solution:**
1. Wait for automatic cleanup (every 5 min by default)
2. Or manually cancel:
```bash
curl -X POST http://localhost:4001/api/cancel/{job_id}
```

### Issue: Redis Connection Failed

**Symptom:** Logs show "Failed to connect to Redis"

**Diagnosis:**
```bash
curl http://localhost:4001/api/ws/stats
```

**Solution:**
1. Check Redis is running: `redis-cli ping`
2. Check URL is correct: `REDIS_URL=redis://host:port/db`
3. System will automatically fallback to local mode

### Issue: Circuit Breaker Open

**Symptom:** Redis publishes are skipped (circuit open in logs)

**Diagnosis:**
```bash
curl http://localhost:4001/api/ws/stats
# Check circuit_breaker.state
```

**Solution:**
1. Fix Redis connection
2. Wait for recovery timeout (default: 30s)
3. Circuit will auto-recover when Redis is healthy

## Scaling

### Vertical Scaling (More Concurrent Jobs)

```bash
# Increase slots
ETL_MAX_CONCURRENT_JOBS=8 python -m uvicorn app:app
```

### Horizontal Scaling (Multiple Instances)

1. Start Redis:
```bash
docker run -d --name redis -p 6379:6379 redis:7
```

2. Start multiple instances:
```bash
# Instance 1
ETL_MAX_CONCURRENT_JOBS=4 REDIS_ENABLED=true ETL_PORT=4001 python -m uvicorn app:app

# Instance 2
ETL_MAX_CONCURRENT_JOBS=4 REDIS_ENABLED=true ETL_PORT=4002 python -m uvicorn app:app
```

3. Load balance between instances (nginx, haproxy, etc.)

## Maintenance

### Cancel All Running Jobs

```bash
# Get running jobs
curl "http://localhost:4001/api/jobs?status=running"

# Cancel each
curl -X POST http://localhost:4001/api/cancel/{job_id}
```

### Clear Stale Jobs

Automatic cleanup runs every `ETL_JOB_CLEANUP_INTERVAL` seconds (default: 300).

Jobs running longer than `ETL_JOB_SLOT_TIMEOUT` (default: 4 hours) are marked as error.

### Restart Without Losing Jobs

1. Pending jobs are preserved in database
2. Running jobs may be marked as error on restart
3. Jobs will resume from queue after restart

## Rollback Procedures

### Disable Multiprocessing

```bash
# Set back to single mode
ETL_MAX_CONCURRENT_JOBS=1 python -m uvicorn app:app
```

### Disable Redis

```bash
# Set back to local mode
REDIS_ENABLED=false python -m uvicorn app:app
```

Both changes are instant - no code changes required.
