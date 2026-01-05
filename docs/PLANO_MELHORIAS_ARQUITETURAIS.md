# Plano de Melhorias Arquiteturais - ETL Dashboard

## Principios do Plano

1. **Retrocompatibilidade Total** - Sistema continua funcionando identicamente com `MAX_CONCURRENT_JOBS=1`
2. **Implementacao Incremental** - Cada passo e testavel isoladamente
3. **Feature Flags** - Novas funcionalidades desativadas por padrao
4. **Zero Downtime** - Migracao sem interromper servico
5. **Rollback Facil** - Reverter com uma variavel de ambiente

---

## MELHORIA 1: Multiprocessing para Jobs Concorrentes

### Arquitetura Atual (Problema)

```
┌─────────────────────────────────────────────────────────┐
│                    BackgroundWorker                      │
│  ┌─────────────────────────────────────────────────┐   │
│  │  while running:                                  │   │
│  │    job = get_next_pending_job()  ◄── BLOQUEIA   │   │
│  │    if job:                           se ha job   │   │
│  │      await _process_job(job) ◄── ESPERA acabar  │   │
│  └─────────────────────────────────────────────────┘   │
│                         │                               │
│                         ▼                               │
│            ┌───────────────────────┐                   │
│            │   ETLExecutor         │                   │
│            │   (SINGLETON)         │                   │
│            │   self.process = 1    │                   │
│            └───────────────────────┘                   │
└─────────────────────────────────────────────────────────┘
```

**Arquivos afetados:**
- `backend/core/database.py:145-166` - `get_next_pending_job()` bloqueia se job rodando
- `backend/services/executor.py:160-161` - Erro se processo ja existe
- `backend/services/worker.py:64-84` - Loop processa 1 job por vez

### Arquitetura Nova (Solucao)

```
┌─────────────────────────────────────────────────────────────────┐
│                        BackgroundWorker                          │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    JobPoolManager                        │   │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐                  │   │
│  │  │ Slot 0  │  │ Slot 1  │  │ Slot 2  │  (configurable)  │   │
│  │  │ Job #1  │  │ Job #2  │  │  IDLE   │                  │   │
│  │  └────┬────┘  └────┬────┘  └─────────┘                  │   │
│  │       │            │                                     │   │
│  │       ▼            ▼                                     │   │
│  │  ┌─────────┐  ┌─────────┐                               │   │
│  │  │Executor │  │Executor │  (instancia por slot)         │   │
│  │  │ slot=0  │  │ slot=1  │                               │   │
│  │  └─────────┘  └─────────┘                               │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

### FASE 1: Preparacao da Base (Nao quebra nada)

#### Passo 1.1: Adicionar configuracoes novas

**Arquivo:** `backend/config.py`

```python
# Adicionar apos linha 69:

# === MULTIPROCESSING CONFIG ===
# Numero maximo de jobs concorrentes (1 = comportamento atual)
MAX_CONCURRENT_JOBS = int(os.getenv("ETL_MAX_CONCURRENT_JOBS", "1"))

# Timeout para jobs orfaos (segundos)
JOB_SLOT_TIMEOUT = int(os.getenv("ETL_JOB_SLOT_TIMEOUT", "7200"))  # 2 horas

# Intervalo de limpeza de jobs orfaos (segundos)
JOB_CLEANUP_INTERVAL = int(os.getenv("ETL_JOB_CLEANUP_INTERVAL", "300"))  # 5 min
```

**Arquivo:** `.env.example`

```bash
# Adicionar:
# Multiprocessing (default: 1 = single job mode)
ETL_MAX_CONCURRENT_JOBS=1
ETL_JOB_SLOT_TIMEOUT=7200
ETL_JOB_CLEANUP_INTERVAL=300
```

**Teste:** Iniciar backend, verificar que funciona igual

---

#### Passo 1.2: Migrar schema do banco (retrocompativel)

**Arquivo:** `backend/core/database.py`

Adicionar apos `init_db()`:

```python
def migrate_db():
    """Executa migracoes de schema (retrocompativeis)"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Verificar se coluna worker_slot existe
    cursor.execute("PRAGMA table_info(jobs)")
    columns = [col[1] for col in cursor.fetchall()]

    if "worker_slot" not in columns:
        # Adicionar colunas para multiprocessing
        cursor.execute("ALTER TABLE jobs ADD COLUMN worker_slot INTEGER DEFAULT NULL")
        cursor.execute("ALTER TABLE jobs ADD COLUMN locked_at TEXT DEFAULT NULL")

        # Criar indice para queries eficientes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_status_slot ON jobs(status, worker_slot)")

        conn.commit()
        print("[MIGRATION] Adicionadas colunas worker_slot e locked_at")

    conn.close()
```

Modificar `init_db()`:

```python
def init_db():
    # ... codigo existente ...
    conn.commit()
    conn.close()

    # Executar migracoes
    migrate_db()
```

**Teste:**
1. Iniciar backend com banco existente
2. Verificar que tabela jobs tem novas colunas
3. Verificar que jobs antigos continuam funcionando

---

#### Passo 1.3: Adicionar funcoes de banco para slots (sem usar ainda)

**Arquivo:** `backend/core/database.py`

Adicionar novas funcoes:

```python
def get_running_jobs_count() -> int:
    """Retorna quantidade de jobs em execucao"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) FROM jobs WHERE status = "running"')
    count = cursor.fetchone()[0]

    conn.close()
    return count


def get_available_slot(max_slots: int) -> int | None:
    """
    Retorna um slot disponivel (0 a max_slots-1).
    Retorna None se todos os slots estao ocupados.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Buscar slots em uso
    cursor.execute(
        'SELECT worker_slot FROM jobs WHERE status = "running" AND worker_slot IS NOT NULL'
    )
    used_slots = {row[0] for row in cursor.fetchall()}

    conn.close()

    # Encontrar primeiro slot livre
    for slot in range(max_slots):
        if slot not in used_slots:
            return slot

    return None


def acquire_job_for_slot(slot: int) -> dict | None:
    """
    Busca proximo job pendente e marca como running no slot especificado.
    Operacao atomica para evitar race conditions.

    Returns:
        Job dict ou None se nao ha jobs pendentes
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    now = datetime.now().isoformat()

    try:
        # Buscar e atualizar atomicamente
        cursor.execute('''
            UPDATE jobs
            SET status = "running",
                worker_slot = ?,
                locked_at = ?,
                started_at = ?
            WHERE id = (
                SELECT id FROM jobs
                WHERE status = "pending"
                ORDER BY created_at ASC
                LIMIT 1
            )
            RETURNING *
        ''', (slot, now, now))

        row = cursor.fetchone()
        conn.commit()

        if row:
            return dict(row)
        return None

    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def release_job_slot(job_id: int):
    """Libera o slot de um job (ao terminar ou dar erro)"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        'UPDATE jobs SET worker_slot = NULL, locked_at = NULL WHERE id = ?',
        (job_id,)
    )

    conn.commit()
    conn.close()


def cleanup_stale_jobs(timeout_seconds: int) -> list[int]:
    """
    Marca jobs travados como erro e libera seus slots.

    Returns:
        Lista de job_ids que foram limpos
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Calcular threshold
    from datetime import timedelta
    threshold = (datetime.now() - timedelta(seconds=timeout_seconds)).isoformat()

    # Buscar jobs travados
    cursor.execute('''
        SELECT id FROM jobs
        WHERE status = "running"
        AND locked_at IS NOT NULL
        AND locked_at < ?
    ''', (threshold,))

    stale_ids = [row['id'] for row in cursor.fetchall()]

    if stale_ids:
        # Marcar como erro
        placeholders = ','.join('?' * len(stale_ids))
        now = datetime.now().isoformat()

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

    conn.close()
    return stale_ids
```

**Teste:**
1. Chamar funcoes manualmente em um script de teste
2. Verificar que nao afetam operacao normal

---

### FASE 2: Refatorar Executor (Retrocompativel)

#### Passo 2.1: Adicionar suporte a slot no Executor

**Arquivo:** `backend/services/executor.py`

Modificar `__init__`:

```python
class ETLExecutor:
    """Executor de pipelines ETL via subprocess"""

    def __init__(self, slot_id: int = 0):
        """
        Args:
            slot_id: Identificador do slot (para multiprocessing)
        """
        self.slot_id = slot_id
        self.process: Optional[asyncio.subprocess.Process] = None
        self._cancelled = False

        # ... resto igual ...
```

Modificar validacao em `execute()`:

```python
async def execute(self, params, log_callback, timeout_seconds=3600) -> bool:
    # REMOVER esta validacao (sera feita pelo pool):
    # if self.process and self.process.returncode is None:
    #     raise Exception("Ja existe um processo em execucao")

    # Manter apenas se for singleton mode
    from config import settings
    if settings.MAX_CONCURRENT_JOBS == 1:
        if self.process and self.process.returncode is None:
            raise Exception("Ja existe um processo em execucao")

    # ... resto igual ...
```

**Manter o singleton como fallback:**

```python
# Singleton (para modo MAX_CONCURRENT_JOBS=1)
_executor_instance: Optional[ETLExecutor] = None


def get_executor(slot_id: int = 0) -> ETLExecutor:
    """
    Retorna executor.
    - Se MAX_CONCURRENT_JOBS=1: retorna singleton
    - Se MAX_CONCURRENT_JOBS>1: retorna nova instancia por slot
    """
    from config import settings

    global _executor_instance

    if settings.MAX_CONCURRENT_JOBS == 1:
        # Modo singleton (comportamento atual)
        if _executor_instance is None:
            _executor_instance = ETLExecutor(slot_id=0)
        return _executor_instance
    else:
        # Modo multiprocessing - nova instancia por slot
        return ETLExecutor(slot_id=slot_id)
```

**Teste:**
1. Com `MAX_CONCURRENT_JOBS=1`: comportamento identico
2. Verificar que singleton ainda funciona

---

### FASE 3: Criar Pool Manager (Novo arquivo)

#### Passo 3.1: Criar `backend/services/pool.py`

```python
"""
Job Pool Manager - Gerencia execucao concorrente de jobs ETL
"""
import asyncio
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional, Callable, Any
from datetime import datetime

from core import database
from services.executor import ETLExecutor
from services.sistemas import get_sistema_service
from models.sistema import SistemaStatus
import services.state as state_service

logger = logging.getLogger(__name__)


class SlotStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    ERROR = "error"


@dataclass
class WorkerSlot:
    """Representa um slot de execucao"""
    slot_id: int
    status: SlotStatus = SlotStatus.IDLE
    current_job_id: Optional[int] = None
    executor: Optional[ETLExecutor] = None
    task: Optional[asyncio.Task] = None
    started_at: Optional[datetime] = None


class JobPoolManager:
    """
    Gerencia pool de workers para execucao concorrente de jobs.

    Features:
    - Slots configuraveis (1 a N)
    - Isolamento de processos por slot
    - Cleanup automatico de jobs orfaos
    - Broadcast de eventos via WebSocket
    """

    def __init__(self, max_workers: int = 3, poll_interval: float = 2.0):
        """
        Args:
            max_workers: Numero maximo de jobs simultaneos
            poll_interval: Intervalo de polling em segundos
        """
        self.max_workers = max_workers
        self.poll_interval = poll_interval
        self.running = False

        # Slots de execucao
        self.slots: Dict[int, WorkerSlot] = {
            i: WorkerSlot(slot_id=i) for i in range(max_workers)
        }

        # Tasks de controle
        self._coordinator_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None

        logger.info(f"JobPoolManager criado com {max_workers} slots")

    async def start(self):
        """Inicia o pool manager"""
        if self.running:
            logger.warning("Pool manager ja esta rodando")
            return

        self.running = True

        # Task principal - coordena atribuicao de jobs
        self._coordinator_task = asyncio.create_task(
            self._coordinator_loop(),
            name="pool_coordinator"
        )

        # Task de cleanup - limpa jobs orfaos periodicamente
        from config import settings
        self._cleanup_task = asyncio.create_task(
            self._cleanup_loop(settings.JOB_CLEANUP_INTERVAL),
            name="pool_cleanup"
        )

        logger.info(f"JobPoolManager iniciado com {self.max_workers} workers")

    async def stop(self):
        """Para o pool manager graciosamente"""
        self.running = False

        # Cancelar tasks de controle
        for task in [self._coordinator_task, self._cleanup_task]:
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        # Cancelar jobs em execucao
        for slot in self.slots.values():
            if slot.status == SlotStatus.RUNNING and slot.task:
                slot.task.cancel()
                try:
                    await slot.task
                except asyncio.CancelledError:
                    pass

        logger.info("JobPoolManager parado")

    async def _coordinator_loop(self):
        """Loop principal - atribui jobs a slots disponiveis"""
        logger.info("Coordinator loop iniciado")

        while self.running:
            try:
                # Buscar slots disponiveis
                idle_slots = [
                    slot for slot in self.slots.values()
                    if slot.status == SlotStatus.IDLE
                ]

                # Tentar atribuir jobs aos slots livres
                for slot in idle_slots:
                    job = database.acquire_job_for_slot(slot.slot_id)

                    if job:
                        logger.info(f"Job #{job['id']} atribuido ao slot {slot.slot_id}")

                        # Iniciar execucao em task separada
                        slot.task = asyncio.create_task(
                            self._execute_job_in_slot(slot, job),
                            name=f"job_{job['id']}_slot_{slot.slot_id}"
                        )

                # Aguardar antes de verificar novamente
                await asyncio.sleep(self.poll_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Erro no coordinator loop: {e}")
                await asyncio.sleep(self.poll_interval * 2)

    async def _execute_job_in_slot(self, slot: WorkerSlot, job: dict):
        """Executa um job em um slot especifico"""
        import json

        job_id = job["id"]
        slot.status = SlotStatus.RUNNING
        slot.current_job_id = job_id
        slot.started_at = datetime.now()

        # Criar executor isolado para este slot
        slot.executor = ETLExecutor(slot_id=slot.slot_id)

        logger.info(f"Slot {slot.slot_id}: Iniciando job #{job_id}")

        # Parsear parametros
        try:
            params = json.loads(job["params"]) if job["params"] else {}
        except json.JSONDecodeError:
            params = {}

        sistemas = params.get("sistemas", [])

        # Atualizar status dos sistemas
        sistema_service = get_sistema_service()
        for sistema_id in sistemas:
            sistema_service.update_status(sistema_id, SistemaStatus.RUNNING, 0, "Executando...")
            await self._broadcast_status(sistema_id, "RUNNING", 0, "Executando...")

        start_time = datetime.now()

        # Callback para logs (inclui slot_id)
        async def log_callback(log_entry: dict):
            database.append_log(job_id, f"[{log_entry['level']}] [{log_entry['sistema']}] {log_entry['mensagem']}")
            log_entry["job_id"] = job_id
            log_entry["slot_id"] = slot.slot_id
            await self._broadcast_log(log_entry)

            # Atualizar status do sistema
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

            # Atualizar sistemas
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
            logger.info(f"Slot {slot.slot_id}: Job #{job_id} finalizado: {final_status} ({duration}s)")

        except asyncio.CancelledError:
            logger.warning(f"Slot {slot.slot_id}: Job #{job_id} cancelado")
            database.update_job_status(job_id, "cancelled", "Cancelado pelo usuario")
            database.release_job_slot(job_id)
            raise

        except Exception as e:
            logger.error(f"Slot {slot.slot_id}: Erro no job #{job_id}: {e}")
            database.update_job_status(job_id, "error", str(e))
            database.release_job_slot(job_id)

            for sistema_id in sistemas:
                sistema_service.update_status(sistema_id, SistemaStatus.ERROR, 0, f"Erro: {e}")
                await self._broadcast_status(sistema_id, "ERROR", 0, f"Erro: {e}")

        finally:
            # Resetar slot
            slot.status = SlotStatus.IDLE
            slot.current_job_id = None
            slot.executor = None
            slot.task = None
            slot.started_at = None

    async def _cleanup_loop(self, interval: int):
        """Loop de limpeza de jobs orfaos"""
        from config import settings

        while self.running:
            try:
                await asyncio.sleep(interval)

                stale_ids = database.cleanup_stale_jobs(settings.JOB_SLOT_TIMEOUT)

                if stale_ids:
                    logger.warning(f"Limpeza: {len(stale_ids)} jobs orfaos removidos: {stale_ids}")

                    for job_id in stale_ids:
                        await self._broadcast_job_complete(job_id, "error", 0)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Erro no cleanup loop: {e}")

    def cancel_job(self, job_id: int) -> bool:
        """Cancela um job especifico"""
        for slot in self.slots.values():
            if slot.current_job_id == job_id and slot.executor:
                slot.executor.cancel()
                logger.info(f"Job #{job_id} cancelado no slot {slot.slot_id}")
                return True
        return False

    def get_status(self) -> dict:
        """Retorna status de todos os slots"""
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
            ]
        }

    # === Broadcast helpers ===

    async def _broadcast_log(self, log_entry: dict):
        ws_manager = state_service.ws_manager
        if ws_manager:
            try:
                await ws_manager.broadcast_log(log_entry)
            except Exception as e:
                logger.error(f"Erro ao broadcast log: {e}")

    async def _broadcast_status(self, sistema_id: str, status: str, progresso: int, mensagem: str):
        ws_manager = state_service.ws_manager
        if ws_manager:
            try:
                await ws_manager.broadcast_status(sistema_id, status, progresso, mensagem)
            except Exception as e:
                logger.error(f"Erro ao broadcast status: {e}")

    async def _broadcast_job_complete(self, job_id: int, status: str, duracao: int):
        ws_manager = state_service.ws_manager
        if ws_manager:
            try:
                await ws_manager.broadcast_job_complete(job_id, status, duracao)
            except Exception as e:
                logger.error(f"Erro ao broadcast job_complete: {e}")


# Singleton do pool (None se MAX_CONCURRENT_JOBS=1)
_pool_instance: Optional[JobPoolManager] = None


def get_pool_manager() -> Optional[JobPoolManager]:
    """Retorna pool manager se multiprocessing estiver habilitado"""
    global _pool_instance
    return _pool_instance


def create_pool_manager(max_workers: int, poll_interval: float) -> JobPoolManager:
    """Cria e retorna pool manager"""
    global _pool_instance
    _pool_instance = JobPoolManager(max_workers, poll_interval)
    return _pool_instance
```

**Teste:** Importar modulo e verificar que nao ha erros de sintaxe

---

### FASE 4: Integrar Pool no Worker (Feature Flag)

#### Passo 4.1: Modificar BackgroundWorker para usar Pool

**Arquivo:** `backend/services/worker.py`

```python
"""
Background Worker - Processa jobs da fila em background
Suporta modo single (padrao) e multiprocessing (opcional)
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Optional, Any

import sys
import os

_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from core import database
from services.executor import get_executor
from services.sistemas import get_sistema_service
from models.sistema import SistemaStatus
import services.state as state_service

logger = logging.getLogger(__name__)


class BackgroundWorker:
    """
    Worker que roda em background processando jobs da fila.

    Modos de operacao:
    - MAX_CONCURRENT_JOBS=1: Modo single (comportamento original)
    - MAX_CONCURRENT_JOBS>1: Modo pool (multiprocessing)
    """

    def __init__(self, poll_interval: float = 2.0):
        self.poll_interval = poll_interval
        self.running = False
        self.current_job_id: Optional[int] = None
        self._task: Optional[asyncio.Task] = None

        # Pool manager (criado se multiprocessing habilitado)
        self._pool_manager = None
        self._use_pool = False

    async def start(self):
        """Inicia o worker em background"""
        if self.running:
            logger.warning("Worker ja esta rodando")
            return

        from config import settings

        self.running = True
        self._use_pool = settings.MAX_CONCURRENT_JOBS > 1

        if self._use_pool:
            # Modo multiprocessing
            from services.pool import create_pool_manager

            self._pool_manager = create_pool_manager(
                max_workers=settings.MAX_CONCURRENT_JOBS,
                poll_interval=self.poll_interval
            )
            await self._pool_manager.start()
            logger.info(f"BackgroundWorker iniciado em modo POOL ({settings.MAX_CONCURRENT_JOBS} workers)")
        else:
            # Modo single (original)
            self._task = asyncio.create_task(self._run_loop())
            logger.info("BackgroundWorker iniciado em modo SINGLE")

    async def stop(self):
        """Para o worker"""
        self.running = False

        if self._use_pool and self._pool_manager:
            await self._pool_manager.stop()
        elif self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        logger.info("BackgroundWorker parado")

    # =========================================================================
    # MODO SINGLE (codigo original - MAX_CONCURRENT_JOBS=1)
    # =========================================================================

    async def _run_loop(self):
        """Loop principal do worker (modo single)"""
        logger.info("Worker loop iniciado (modo single) - aguardando jobs...")

        while self.running:
            try:
                job = database.get_next_pending_job()

                if job:
                    await self._process_job(job)
                else:
                    await asyncio.sleep(self.poll_interval)

            except asyncio.CancelledError:
                logger.info("Worker loop cancelado")
                break
            except Exception as e:
                logger.error(f"Erro no worker loop: {e}")
                await asyncio.sleep(self.poll_interval * 2)

    async def _process_job(self, job: dict):
        """Processa um job da fila (modo single)"""
        job_id = job["id"]
        self.current_job_id = job_id

        logger.info(f"Processando job #{job_id}")

        try:
            params = json.loads(job["params"]) if job["params"] else {}
        except json.JSONDecodeError:
            params = {}

        sistemas = params.get("sistemas", [])

        database.update_job_status(job_id, "running")
        start_time = datetime.now()

        sistema_service = get_sistema_service()
        for sistema_id in sistemas:
            sistema_service.update_status(sistema_id, SistemaStatus.RUNNING, 0, "Executando...")
            await self._broadcast_status(sistema_id, "RUNNING", 0, "Executando...")

        async def log_callback(log_entry: dict):
            msg = f"[{log_entry['level']}] [{log_entry['sistema']}] {log_entry['mensagem']}"
            database.append_log(job_id, msg)
            log_entry["job_id"] = job_id
            await self._broadcast_log(log_entry)

            sistema = log_entry.get("sistema", "").lower()
            if sistema and sistema != "sistema" and sistema != "stdout":
                level = log_entry.get("level", "INFO")
                if level == "SUCCESS":
                    await self._broadcast_status(sistema, "SUCCESS", 100, log_entry["mensagem"])
                elif level == "ERROR":
                    await self._broadcast_status(sistema, "ERROR", 0, log_entry["mensagem"])

        executor = get_executor()
        try:
            success = await executor.execute(params, log_callback)

            duration = int((datetime.now() - start_time).total_seconds())
            final_status = "completed" if success else "error"
            database.update_job_status(job_id, final_status)

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
            logger.info(f"Job #{job_id} finalizado: {final_status} ({duration}s)")

        except Exception as e:
            logger.error(f"Erro ao processar job #{job_id}: {e}")
            database.update_job_status(job_id, "error", str(e))

            for sistema_id in sistemas:
                sistema_service.update_status(sistema_id, SistemaStatus.ERROR, 0, f"Erro: {str(e)}")
                await self._broadcast_status(sistema_id, "ERROR", 0, f"Erro: {str(e)}")

        finally:
            self.current_job_id = None

    # =========================================================================
    # METODOS COMPARTILHADOS
    # =========================================================================

    def cancel_current_job(self):
        """Cancela job em execucao"""
        if self._use_pool and self._pool_manager:
            # Modo pool - precisa do job_id
            return False  # Usar cancel_job(job_id) diretamente
        else:
            # Modo single
            if self.current_job_id:
                executor = get_executor()
                executor.cancel()
                logger.info(f"Job #{self.current_job_id} cancelado")
                return True
        return False

    def cancel_job(self, job_id: int) -> bool:
        """Cancela um job especifico por ID"""
        if self._use_pool and self._pool_manager:
            return self._pool_manager.cancel_job(job_id)
        else:
            # Modo single - so pode cancelar job atual
            if self.current_job_id == job_id:
                return self.cancel_current_job()
        return False

    def get_pool_status(self) -> dict | None:
        """Retorna status do pool (se ativo)"""
        if self._use_pool and self._pool_manager:
            return self._pool_manager.get_status()
        return None

    async def _broadcast_log(self, log_entry: dict):
        ws_manager = state_service.ws_manager
        if ws_manager:
            try:
                await ws_manager.broadcast_log(log_entry)
            except Exception as e:
                logger.error(f"Erro ao broadcast log: {e}")

    async def _broadcast_status(self, sistema_id: str, status: str, progresso: int, mensagem: str):
        ws_manager = state_service.ws_manager
        if ws_manager:
            try:
                await ws_manager.broadcast_status(sistema_id, status, progresso, mensagem)
            except Exception as e:
                logger.error(f"Erro ao broadcast status: {e}")

    async def _broadcast_job_complete(self, job_id: int, status: str, duracao: int):
        ws_manager = state_service.ws_manager
        if ws_manager:
            try:
                await ws_manager.broadcast_job_complete(job_id, status, duracao)
            except Exception as e:
                logger.error(f"Erro ao broadcast job_complete: {e}")


# Singleton
_worker_instance: Optional[BackgroundWorker] = None


def get_worker() -> BackgroundWorker:
    """Retorna instancia singleton do BackgroundWorker"""
    global _worker_instance
    if _worker_instance is None:
        _worker_instance = BackgroundWorker()
    return _worker_instance
```

**Teste:**
1. `MAX_CONCURRENT_JOBS=1` (padrao): Verificar comportamento identico
2. `MAX_CONCURRENT_JOBS=3`: Verificar que pool inicia corretamente

---

### FASE 5: Ajustar API de Execucao

#### Passo 5.1: Modificar endpoint /api/execute

**Arquivo:** `backend/routers/execution.py`

Ajustar para nao bloquear quando pool esta ativo:

```python
# Adicionar endpoint para status do pool
@router.get("/api/pool/status")
async def get_pool_status(current_user = Depends(get_current_user)):
    """Retorna status do pool de workers"""
    worker = get_worker()
    pool_status = worker.get_pool_status()

    if pool_status:
        return pool_status
    else:
        return {
            "mode": "single",
            "current_job_id": worker.current_job_id
        }
```

---

### FASE 6: Testes

#### Passo 6.1: Testes unitarios

**Arquivo:** `backend/tests/unit/test_pool.py`

```python
import pytest
import asyncio
from services.pool import JobPoolManager, SlotStatus

class TestJobPoolManager:
    def test_init_creates_slots(self):
        pool = JobPoolManager(max_workers=3)
        assert len(pool.slots) == 3
        assert all(s.status == SlotStatus.IDLE for s in pool.slots.values())

    @pytest.mark.asyncio
    async def test_start_stop(self):
        pool = JobPoolManager(max_workers=2)
        await pool.start()
        assert pool.running
        await pool.stop()
        assert not pool.running
```

#### Passo 6.2: Testes de integracao

**Arquivo:** `backend/tests/integration/test_concurrent_jobs.py`

```python
import pytest
from core import database

class TestConcurrentJobs:
    def test_acquire_job_for_slot(self):
        # Criar job
        job_id = database.add_job("test", {"sistemas": ["amplis"]})

        # Adquirir para slot 0
        job = database.acquire_job_for_slot(0)

        assert job is not None
        assert job["id"] == job_id
        assert job["worker_slot"] == 0
        assert job["status"] == "running"

        # Limpar
        database.release_job_slot(job_id)
```

---

## MELHORIA 2: Redis Pub/Sub para WebSocket Clustering

### Arquitetura Atual (Problema)

```
┌─────────────────────────────────────────────────────────┐
│                    Instancia Unica                       │
│  ┌─────────────────────────────────────────────────┐   │
│  │           ConnectionManager                      │   │
│  │  active_connections: List[WebSocket] = []       │   │
│  │                                                  │   │
│  │  async def _broadcast(message):                 │   │
│  │    for conn in active_connections:  ◄── LOCAL   │   │
│  │      await conn.send_json(message)      ONLY    │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### Arquitetura Nova (Solucao)

```
┌─────────────────────────────────────────────────────────────────┐
│                         Redis Pub/Sub                            │
│                    ┌─────────────────┐                          │
│                    │ Channel: etl:ws │                          │
│                    └────────┬────────┘                          │
│                             │                                    │
│         ┌───────────────────┼───────────────────┐               │
│         │                   │                   │               │
│    ┌────▼────┐        ┌────▼────┐        ┌────▼────┐           │
│    │Instance1│        │Instance2│        │Instance3│           │
│    │  Local  │        │  Local  │        │  Local  │           │
│    │Clients 5│        │Clients 3│        │Clients 7│           │
│    └─────────┘        └─────────┘        └─────────┘           │
└─────────────────────────────────────────────────────────────────┘
```

---

### FASE 1: Preparacao (Nao quebra nada)

#### Passo 1.1: Adicionar dependencia Redis

**Arquivo:** `backend/requirements.txt`

```txt
# Adicionar:
# Redis (opcional - para horizontal scaling)
redis>=5.0.0
```

#### Passo 1.2: Adicionar configuracoes Redis

**Arquivo:** `backend/config.py`

```python
# Adicionar apos linha 78:

# === REDIS CONFIG (opcional) ===
REDIS_ENABLED = os.getenv("REDIS_ENABLED", "false").lower() == "true"
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
REDIS_CHANNEL_PREFIX = os.getenv("REDIS_CHANNEL_PREFIX", "etl")
REDIS_POOL_SIZE = int(os.getenv("REDIS_POOL_SIZE", "10"))
REDIS_SOCKET_TIMEOUT = float(os.getenv("REDIS_SOCKET_TIMEOUT", "5.0"))
```

**Arquivo:** `.env.example`

```bash
# Adicionar:
# Redis (opcional - para horizontal scaling)
REDIS_ENABLED=false
REDIS_URL=redis://localhost:6379/0
REDIS_CHANNEL_PREFIX=etl
```

---

### FASE 2: Criar Cliente Redis (Novo arquivo)

#### Passo 2.1: Criar `backend/services/redis_client.py`

```python
"""
Redis Pub/Sub Client - Para WebSocket distribuido
"""
import asyncio
import json
import logging
from typing import Optional, Callable, Any
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import socket

logger = logging.getLogger(__name__)

# Importar redis apenas se disponivel
try:
    import redis.asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis nao disponivel - instale com: pip install redis")


class MessageType(str, Enum):
    LOG = "log"
    STATUS = "status"
    JOB_COMPLETE = "job_complete"


@dataclass
class PubSubMessage:
    """Mensagem para pub/sub"""
    type: MessageType
    payload: dict
    source_instance: str

    def to_json(self) -> str:
        data = asdict(self)
        data["type"] = self.type.value
        return json.dumps(data)

    @classmethod
    def from_json(cls, data: str) -> "PubSubMessage":
        obj = json.loads(data)
        obj["type"] = MessageType(obj["type"])
        return cls(**obj)


class RedisPubSubClient:
    """
    Cliente Redis para pub/sub.
    Graceful degradation se Redis indisponivel.
    """

    def __init__(self, redis_url: str, channel_prefix: str = "etl"):
        self.redis_url = redis_url
        self.channel_prefix = channel_prefix
        self.instance_id = f"{socket.gethostname()}-{uuid.uuid4().hex[:8]}"

        self._redis: Optional[Any] = None
        self._pubsub: Optional[Any] = None
        self._listener_task: Optional[asyncio.Task] = None
        self._connected = False
        self._handler: Optional[Callable] = None

    @property
    def ws_channel(self) -> str:
        return f"{self.channel_prefix}:ws"

    @property
    def is_connected(self) -> bool:
        return self._connected

    async def connect(self) -> bool:
        """Conecta ao Redis"""
        if not REDIS_AVAILABLE:
            logger.warning("Redis nao disponivel")
            return False

        try:
            self._redis = aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_timeout=5.0
            )

            # Testar conexao
            await self._redis.ping()
            self._connected = True
            logger.info(f"Conectado ao Redis: {self.redis_url}")
            return True

        except Exception as e:
            logger.warning(f"Falha ao conectar ao Redis: {e}")
            self._connected = False
            return False

    async def disconnect(self):
        """Desconecta do Redis"""
        if self._listener_task:
            self._listener_task.cancel()
            try:
                await self._listener_task
            except asyncio.CancelledError:
                pass

        if self._pubsub:
            await self._pubsub.close()

        if self._redis:
            await self._redis.close()

        self._connected = False
        logger.info("Desconectado do Redis")

    async def publish(self, message: PubSubMessage) -> bool:
        """Publica mensagem no canal"""
        if not self._connected or not self._redis:
            return False

        try:
            await self._redis.publish(self.ws_channel, message.to_json())
            return True
        except Exception as e:
            logger.error(f"Erro ao publicar: {e}")
            return False

    async def subscribe(self, handler: Callable[[PubSubMessage], Any]):
        """Inscreve no canal e processa mensagens"""
        if not self._connected or not self._redis:
            return

        self._handler = handler
        self._pubsub = self._redis.pubsub()
        await self._pubsub.subscribe(self.ws_channel)

        self._listener_task = asyncio.create_task(self._listen_loop())
        logger.info(f"Inscrito no canal: {self.ws_channel}")

    async def _listen_loop(self):
        """Loop de escuta de mensagens"""
        while True:
            try:
                message = await self._pubsub.get_message(
                    ignore_subscribe_messages=True,
                    timeout=1.0
                )

                if message and message["type"] == "message":
                    pubsub_msg = PubSubMessage.from_json(message["data"])

                    # Ignorar mensagens de si mesmo
                    if pubsub_msg.source_instance != self.instance_id:
                        if self._handler:
                            if asyncio.iscoroutinefunction(self._handler):
                                await self._handler(pubsub_msg)
                            else:
                                self._handler(pubsub_msg)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Erro no listener: {e}")
                await asyncio.sleep(1)
```

---

### FASE 3: Criar WebSocket Manager Distribuido

#### Passo 3.1: Criar `backend/services/distributed_ws.py`

```python
"""
Distributed WebSocket Manager - Suporta Redis pub/sub
"""
import asyncio
import logging
from typing import List, Optional
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class DistributedConnectionManager:
    """
    WebSocket manager com suporte opcional a Redis.

    Comportamento:
    - REDIS_ENABLED=false: Funciona localmente (igual ao original)
    - REDIS_ENABLED=true: Broadcast via Redis para outras instancias
    """

    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self._redis_client = None
        self._redis_enabled = False
        self._initialized = False

    async def initialize(self):
        """Inicializa conexao Redis se habilitado"""
        if self._initialized:
            return

        from config import settings

        self._redis_enabled = settings.REDIS_ENABLED

        if self._redis_enabled:
            from services.redis_client import RedisPubSubClient

            self._redis_client = RedisPubSubClient(
                redis_url=settings.REDIS_URL,
                channel_prefix=settings.REDIS_CHANNEL_PREFIX
            )

            connected = await self._redis_client.connect()

            if connected:
                await self._redis_client.subscribe(self._handle_redis_message)
                logger.info("WebSocket manager inicializado com Redis")
            else:
                logger.warning("Redis indisponivel - usando modo local")
                self._redis_client = None
        else:
            logger.info("WebSocket manager inicializado (modo local)")

        self._initialized = True

    async def shutdown(self):
        """Encerra conexao Redis"""
        if self._redis_client:
            await self._redis_client.disconnect()

    async def connect(self, websocket: WebSocket):
        """Aceita conexao WebSocket"""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.debug(f"WebSocket conectado. Total: {self.connection_count}")

    def disconnect(self, websocket: WebSocket):
        """Remove conexao WebSocket"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.debug(f"WebSocket desconectado. Total: {self.connection_count}")

    async def broadcast_log(self, log_entry: dict):
        """Broadcast log para todos os clientes"""
        message = {"type": "log", "payload": log_entry}
        await self._broadcast_local(message)
        await self._publish_to_redis("log", log_entry)

    async def broadcast_status(self, sistema_id: str, status: str, progresso: int = 0, mensagem: str = None):
        """Broadcast status para todos os clientes"""
        payload = {
            "sistema_id": sistema_id,
            "status": status,
            "progresso": progresso,
            "mensagem": mensagem
        }
        message = {"type": "status", "payload": payload}
        await self._broadcast_local(message)
        await self._publish_to_redis("status", payload)

    async def broadcast_job_complete(self, job_id: int, status: str, duracao: int = 0):
        """Broadcast job complete para todos os clientes"""
        payload = {
            "job_id": job_id,
            "status": status,
            "duracao_segundos": duracao
        }
        message = {"type": "job_complete", "payload": payload}
        await self._broadcast_local(message)
        await self._publish_to_redis("job_complete", payload)

    async def _broadcast_local(self, message: dict):
        """Broadcast apenas para conexoes locais"""
        disconnect_list = []

        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning(f"Erro ao enviar WebSocket: {e}")
                disconnect_list.append(connection)

        for conn in disconnect_list:
            self.disconnect(conn)

    async def _publish_to_redis(self, msg_type: str, payload: dict):
        """Publica no Redis para outras instancias"""
        if self._redis_client and self._redis_client.is_connected:
            from services.redis_client import PubSubMessage, MessageType

            message = PubSubMessage(
                type=MessageType(msg_type),
                payload=payload,
                source_instance=self._redis_client.instance_id
            )
            await self._redis_client.publish(message)

    async def _handle_redis_message(self, message):
        """Processa mensagem recebida do Redis"""
        ws_message = {
            "type": message.type.value,
            "payload": message.payload
        }
        await self._broadcast_local(ws_message)

    @property
    def connection_count(self) -> int:
        return len(self.active_connections)

    @property
    def is_distributed(self) -> bool:
        return self._redis_client is not None and self._redis_client.is_connected
```

---

### FASE 4: Integrar no App (Feature Flag)

#### Passo 4.1: Modificar `backend/app.py`

```python
# Substituir ConnectionManager por DistributedConnectionManager

# ANTES:
# class ConnectionManager: ...
# manager = ConnectionManager()

# DEPOIS:
from services.distributed_ws import DistributedConnectionManager

manager = DistributedConnectionManager()
state_service.ws_manager = manager

# No lifespan, adicionar inicializacao:
@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Startup
    from core import database
    database.init_db()

    init_auth_tables()

    # Inicializar WebSocket distribuido
    await manager.initialize()
    logger.info(f"WebSocket manager: distributed={manager.is_distributed}")

    worker = get_worker()
    await worker.start()

    yield

    # Shutdown
    await worker.stop()
    await manager.shutdown()  # Novo
```

---

### FASE 5: Docker Compose

#### Passo 5.1: Adicionar Redis ao docker-compose.yml

```yaml
services:
  redis:
    image: redis:7-alpine
    container_name: etl-redis
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    command: redis-server --appendonly yes
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 3

  backend:
    # ... config existente ...
    environment:
      - REDIS_ENABLED=true
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      redis:
        condition: service_healthy

volumes:
  redis-data:
```

---

## Checklist de Implementacao

### Melhoria 1: Multiprocessing

- [ ] **FASE 1: Preparacao**
  - [ ] 1.1 Adicionar config `MAX_CONCURRENT_JOBS` em `config.py`
  - [ ] 1.2 Criar migracao de schema em `database.py`
  - [ ] 1.3 Adicionar funcoes de slot em `database.py`
  - [ ] Testar: Backend inicia normalmente

- [ ] **FASE 2: Refatorar Executor**
  - [ ] 2.1 Adicionar `slot_id` ao `ETLExecutor`
  - [ ] 2.2 Modificar `get_executor()` para suportar pool
  - [ ] Testar: `MAX_CONCURRENT_JOBS=1` funciona igual

- [ ] **FASE 3: Pool Manager**
  - [ ] 3.1 Criar `backend/services/pool.py`
  - [ ] Testar: Importar sem erros

- [ ] **FASE 4: Integrar Worker**
  - [ ] 4.1 Modificar `BackgroundWorker` para usar pool
  - [ ] Testar: Modo single funciona
  - [ ] Testar: Modo pool funciona com `MAX_CONCURRENT_JOBS=3`

- [ ] **FASE 5: API**
  - [ ] 5.1 Adicionar endpoint `/api/pool/status`
  - [ ] Testar: Endpoint retorna status correto

- [ ] **FASE 6: Testes**
  - [ ] 6.1 Testes unitarios do pool
  - [ ] 6.2 Testes de integracao

### Melhoria 2: Redis Pub/Sub

- [ ] **FASE 1: Preparacao**
  - [ ] 1.1 Adicionar `redis>=5.0.0` em `requirements.txt`
  - [ ] 1.2 Adicionar config Redis em `config.py`
  - [ ] Testar: Backend inicia sem Redis

- [ ] **FASE 2: Cliente Redis**
  - [ ] 2.1 Criar `backend/services/redis_client.py`
  - [ ] Testar: Importar sem erros

- [ ] **FASE 3: WebSocket Distribuido**
  - [ ] 3.1 Criar `backend/services/distributed_ws.py`
  - [ ] Testar: Funciona sem Redis

- [ ] **FASE 4: Integracao**
  - [ ] 4.1 Modificar `app.py` para usar `DistributedConnectionManager`
  - [ ] Testar: `REDIS_ENABLED=false` funciona igual
  - [ ] Testar: `REDIS_ENABLED=true` com Redis local

- [ ] **FASE 5: Docker**
  - [ ] 5.1 Adicionar Redis ao `docker-compose.yml`
  - [ ] Testar: Deploy completo funciona

---

## Comandos de Teste

```bash
# Modo single (padrao)
ETL_MAX_CONCURRENT_JOBS=1 python -m uvicorn app:app --reload

# Modo pool (3 workers)
ETL_MAX_CONCURRENT_JOBS=3 python -m uvicorn app:app --reload

# Com Redis
REDIS_ENABLED=true REDIS_URL=redis://localhost:6379/0 python -m uvicorn app:app --reload

# Rodar testes
pytest backend/tests/ -v
```

---

## Rollback

| Melhoria | Como reverter |
|----------|---------------|
| Multiprocessing | `ETL_MAX_CONCURRENT_JOBS=1` |
| Redis | `REDIS_ENABLED=false` |

Ambas as melhorias sao **feature flags** que podem ser desabilitadas instantaneamente via variavel de ambiente, sem necessidade de rollback de codigo.
