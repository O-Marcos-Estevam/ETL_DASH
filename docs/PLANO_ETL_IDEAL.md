# Plano: Sistema ETL Ideal

## Visão Geral

Este documento descreve a arquitetura do **melhor sistema ETL possível**, incorporando as melhores práticas da indústria, padrões modernos de arquitetura e lições aprendidas do sistema atual.

---

## 1. Arquitetura de Alto Nível

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           ETL SYSTEM - ARQUITETURA IDEAL                        │
└─────────────────────────────────────────────────────────────────────────────────┘

                                    ┌─────────────┐
                                    │   USERS     │
                                    │  (Browser)  │
                                    └──────┬──────┘
                                           │
                              ┌────────────┴────────────┐
                              │      LOAD BALANCER      │
                              │    (Nginx / Traefik)    │
                              └────────────┬────────────┘
                                           │
                    ┌──────────────────────┼──────────────────────┐
                    │                      │                      │
             ┌──────┴──────┐        ┌──────┴──────┐        ┌──────┴──────┐
             │  FRONTEND   │        │  FRONTEND   │        │  FRONTEND   │
             │  (React)    │        │  (React)    │        │  (React)    │
             └──────┬──────┘        └──────┬──────┘        └──────┬──────┘
                    │                      │                      │
                    └──────────────────────┼──────────────────────┘
                                           │
                              ┌────────────┴────────────┐
                              │       API GATEWAY       │
                              │   (Kong / AWS API GW)   │
                              └────────────┬────────────┘
                                           │
         ┌─────────────────────────────────┼─────────────────────────────────┐
         │                                 │                                 │
  ┌──────┴──────┐                   ┌──────┴──────┐                   ┌──────┴──────┐
  │   AUTH      │                   │   BACKEND   │                   │   BACKEND   │
  │  SERVICE    │                   │  INSTANCE 1 │                   │  INSTANCE N │
  │  (FastAPI)  │                   │  (FastAPI)  │                   │  (FastAPI)  │
  └──────┬──────┘                   └──────┬──────┘                   └──────┬──────┘
         │                                 │                                 │
         └─────────────────────────────────┼─────────────────────────────────┘
                                           │
         ┌─────────────────────────────────┼─────────────────────────────────┐
         │                                 │                                 │
  ┌──────┴──────┐                   ┌──────┴──────┐                   ┌──────┴──────┐
  │   REDIS     │                   │  POSTGRES   │                   │   MINIO     │
  │  (Cache +   │                   │  (Database) │                   │  (Storage)  │
  │   Pub/Sub)  │                   │             │                   │             │
  └─────────────┘                   └─────────────┘                   └─────────────┘

                                           │
                              ┌────────────┴────────────┐
                              │      MESSAGE QUEUE      │
                              │   (RabbitMQ / Kafka)    │
                              └────────────┬────────────┘
                                           │
         ┌─────────────────────────────────┼─────────────────────────────────┐
         │                                 │                                 │
  ┌──────┴──────┐                   ┌──────┴──────┐                   ┌──────┴──────┐
  │   WORKER    │                   │   WORKER    │                   │   WORKER    │
  │  INSTANCE 1 │                   │  INSTANCE 2 │                   │  INSTANCE N │
  │  (Celery)   │                   │  (Celery)   │                   │  (Celery)   │
  └──────┬──────┘                   └──────┬──────┘                   └──────┬──────┘
         │                                 │                                 │
         └─────────────────────────────────┼─────────────────────────────────┘
                                           │
                              ┌────────────┴────────────┐
                              │     EXECUTOR POOL       │
                              │   (Kubernetes Jobs /    │
                              │    Docker Containers)   │
                              └────────────┬────────────┘
                                           │
                    ┌──────────────────────┼──────────────────────┐
                    │                      │                      │
             ┌──────┴──────┐        ┌──────┴──────┐        ┌──────┴──────┐
             │   AMPLIS    │        │    MAPS     │        │    QORE     │
             │  CONNECTOR  │        │  CONNECTOR  │        │  CONNECTOR  │
             └─────────────┘        └─────────────┘        └─────────────┘

                                           │
                              ┌────────────┴────────────┐
                              │     OBSERVABILITY       │
                              │  Prometheus + Grafana   │
                              │  Jaeger + ELK Stack     │
                              └─────────────────────────┘
```

---

## 2. Componentes Core

### 2.1 API Layer

| Componente | Tecnologia | Responsabilidade |
|------------|------------|------------------|
| **API Gateway** | Kong / Traefik | Rate limiting, auth, routing |
| **Auth Service** | FastAPI + JWT | Autenticação centralizada |
| **Backend API** | FastAPI | Orquestração de jobs |
| **WebSocket Server** | FastAPI + Socket.IO | Real-time updates |

### 2.2 Data Layer

| Componente | Tecnologia | Responsabilidade |
|------------|------------|------------------|
| **Primary DB** | PostgreSQL | Jobs, users, configs |
| **Cache** | Redis | Sessions, rate limits, pub/sub |
| **Object Storage** | MinIO / S3 | Arquivos, logs, resultados |
| **Time-Series** | TimescaleDB | Métricas de execução |

### 2.3 Processing Layer

| Componente | Tecnologia | Responsabilidade |
|------------|------------|------------------|
| **Message Queue** | RabbitMQ / Kafka | Fila de jobs distribuída |
| **Workers** | Celery | Processamento assíncrono |
| **Executors** | K8s Jobs / Docker | Isolamento de execução |
| **Scheduler** | Celery Beat | Jobs agendados (cron) |

### 2.4 Observability Layer

| Componente | Tecnologia | Responsabilidade |
|------------|------------|------------------|
| **Metrics** | Prometheus | Coleta de métricas |
| **Dashboards** | Grafana | Visualização |
| **Tracing** | Jaeger / OpenTelemetry | Distributed tracing |
| **Logs** | ELK Stack | Agregação de logs |
| **Alerting** | AlertManager | Notificações |

---

## 3. Modelo de Dados

### 3.1 Schema Principal (PostgreSQL)

```sql
-- Pipelines (definições)
CREATE TABLE pipelines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    config JSONB NOT NULL DEFAULT '{}',
    schedule VARCHAR(100), -- Cron expression
    is_active BOOLEAN DEFAULT true,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Pipeline Steps (DAG)
CREATE TABLE pipeline_steps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pipeline_id UUID REFERENCES pipelines(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    connector_type VARCHAR(100) NOT NULL, -- 'amplis', 'maps', 'fidc'
    config JSONB NOT NULL DEFAULT '{}',
    dependencies UUID[] DEFAULT '{}', -- Step IDs que devem completar antes
    retry_count INT DEFAULT 3,
    timeout_seconds INT DEFAULT 3600,
    order_index INT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Job Executions
CREATE TABLE job_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pipeline_id UUID REFERENCES pipelines(id),
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    -- pending, queued, running, success, failed, cancelled, timeout

    trigger_type VARCHAR(50) NOT NULL, -- 'manual', 'scheduled', 'api', 'webhook'
    triggered_by UUID REFERENCES users(id),

    parameters JSONB DEFAULT '{}',
    context JSONB DEFAULT '{}', -- Runtime context

    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    duration_ms BIGINT,

    worker_id VARCHAR(255),
    retry_attempt INT DEFAULT 0,

    error_message TEXT,
    error_stack TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Step Executions
CREATE TABLE step_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID REFERENCES job_executions(id) ON DELETE CASCADE,
    step_id UUID REFERENCES pipeline_steps(id),

    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    progress INT DEFAULT 0, -- 0-100

    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    duration_ms BIGINT,

    input_data JSONB,
    output_data JSONB,

    logs_url VARCHAR(500), -- S3/MinIO URL
    artifacts_url VARCHAR(500),

    error_message TEXT,
    metrics JSONB DEFAULT '{}',

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Credentials (encrypted)
CREATE TABLE credentials (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    connector_type VARCHAR(100) NOT NULL,
    encrypted_data BYTEA NOT NULL, -- AES-256-GCM

    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Audit Log
CREATE TABLE audit_log (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    user_id UUID REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100),
    resource_id UUID,
    old_value JSONB,
    new_value JSONB,
    ip_address INET,
    user_agent TEXT
);

-- Indexes
CREATE INDEX idx_jobs_status ON job_executions(status);
CREATE INDEX idx_jobs_pipeline ON job_executions(pipeline_id);
CREATE INDEX idx_jobs_created ON job_executions(created_at DESC);
CREATE INDEX idx_steps_job ON step_executions(job_id);
CREATE INDEX idx_audit_timestamp ON audit_log(timestamp DESC);
```

### 3.2 Cache Schema (Redis)

```
# Session tokens
session:{user_id}:{token_hash} → {user_data, expires_at}

# Rate limiting
ratelimit:{ip}:{endpoint} → {count, window_start}

# Job status (real-time)
job:{job_id}:status → {status, progress, current_step}

# Pub/Sub channels
channel:job:{job_id}:logs → Stream de logs
channel:job:{job_id}:status → Status updates
channel:global:notifications → Notificações globais

# Distributed locks
lock:pipeline:{pipeline_id} → {worker_id, acquired_at}
lock:credential:{cred_id} → {worker_id, acquired_at}
```

---

## 4. Fluxo de Execução

### 4.1 Fluxo Completo

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                         FLUXO DE EXECUÇÃO ETL                                │
└──────────────────────────────────────────────────────────────────────────────┘

    ┌─────────┐
    │ TRIGGER │  ← Manual / Scheduled / Webhook / API
    └────┬────┘
         │
         ▼
    ┌─────────────────────────────────────────────────────────────────────────┐
    │ 1. VALIDATION                                                           │
    │    • Valida parâmetros                                                  │
    │    • Verifica permissões                                                │
    │    • Verifica rate limits                                               │
    │    • Valida credenciais disponíveis                                     │
    └────┬────────────────────────────────────────────────────────────────────┘
         │
         ▼
    ┌─────────────────────────────────────────────────────────────────────────┐
    │ 2. JOB CREATION                                                         │
    │    • Cria registro job_executions (status: pending)                     │
    │    • Cria registros step_executions para cada step                      │
    │    • Gera trace_id para distributed tracing                             │
    │    • Publica evento: job.created                                        │
    └────┬────────────────────────────────────────────────────────────────────┘
         │
         ▼
    ┌─────────────────────────────────────────────────────────────────────────┐
    │ 3. QUEUE                                                                │
    │    • Publica mensagem no RabbitMQ/Kafka                                 │
    │    • Inclui: job_id, priority, routing_key                              │
    │    • Status: pending → queued                                           │
    │    • Retorna imediatamente ao cliente                                   │
    └────┬────────────────────────────────────────────────────────────────────┘
         │
         ▼
    ┌─────────────────────────────────────────────────────────────────────────┐
    │ 4. WORKER PICKUP                                                        │
    │    • Celery worker consome mensagem da fila                             │
    │    • Adquire distributed lock para o job                                │
    │    • Status: queued → running                                           │
    │    • Inicia trace span                                                  │
    └────┬────────────────────────────────────────────────────────────────────┘
         │
         ▼
    ┌─────────────────────────────────────────────────────────────────────────┐
    │ 5. DAG EXECUTION                                                        │
    │                                                                         │
    │    Para cada step (respeitando dependências):                           │
    │                                                                         │
    │    ┌─────────────────────────────────────────────────────────────────┐  │
    │    │ 5.1 STEP START                                                 │  │
    │    │     • Cria container/K8s Job isolado                           │  │
    │    │     • Injeta credenciais (via secrets)                         │  │
    │    │     • Monta volumes para input/output                          │  │
    │    └────┬────────────────────────────────────────────────────────────┘  │
    │         │                                                               │
    │         ▼                                                               │
    │    ┌─────────────────────────────────────────────────────────────────┐  │
    │    │ 5.2 CONNECTOR EXECUTION                                        │  │
    │    │     • Executa lógica do connector (AMPLIS, MAPS, etc)          │  │
    │    │     • Streaming de logs para Redis/S3                          │  │
    │    │     • Checkpoints periódicos                                   │  │
    │    │     • Métricas: rows_processed, bytes_transferred              │  │
    │    └────┬────────────────────────────────────────────────────────────┘  │
    │         │                                                               │
    │         ▼                                                               │
    │    ┌─────────────────────────────────────────────────────────────────┐  │
    │    │ 5.3 STEP COMPLETE                                              │  │
    │    │     • Salva output (S3/MinIO)                                  │  │
    │    │     • Atualiza step_execution                                  │  │
    │    │     • Publica: step.completed                                  │  │
    │    │     • Libera recursos do container                             │  │
    │    └─────────────────────────────────────────────────────────────────┘  │
    │                                                                         │
    │    Se step falhar:                                                      │
    │    ┌─────────────────────────────────────────────────────────────────┐  │
    │    │ 5.4 RETRY LOGIC                                                │  │
    │    │     • Exponential backoff: 2^attempt * base_delay              │  │
    │    │     • Max retries: configurável por step                       │  │
    │    │     • Dead Letter Queue se esgotar retries                     │  │
    │    └─────────────────────────────────────────────────────────────────┘  │
    │                                                                         │
    └────┬────────────────────────────────────────────────────────────────────┘
         │
         ▼
    ┌─────────────────────────────────────────────────────────────────────────┐
    │ 6. JOB COMPLETION                                                       │
    │    • Calcula métricas agregadas                                         │
    │    • Status: running → success/failed                                   │
    │    • Libera distributed lock                                            │
    │    • Publica: job.completed                                             │
    │    • Notifica via WebSocket                                             │
    │    • Envia alertas se configurado                                       │
    └────┬────────────────────────────────────────────────────────────────────┘
         │
         ▼
    ┌─────────────────────────────────────────────────────────────────────────┐
    │ 7. POST-PROCESSING                                                      │
    │    • Executa webhooks configurados                                      │
    │    • Trigger de pipelines dependentes                                   │
    │    • Limpeza de arquivos temporários                                    │
    │    • Arquiva logs no S3                                                 │
    └─────────────────────────────────────────────────────────────────────────┘
```

### 4.2 DAG (Directed Acyclic Graph)

```
Exemplo de Pipeline com Dependências:

    ┌──────────┐
    │ Extract  │
    │  AMPLIS  │
    └────┬─────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌──────┐  ┌──────┐
│ Trans│  │ Trans│
│ form │  │ form │
│  CSV │  │  PDF │
└──┬───┘  └──┬───┘
   │         │
   └────┬────┘
        │
        ▼
   ┌─────────┐
   │  Load   │
   │   DB    │
   └────┬────┘
        │
        ▼
   ┌─────────┐
   │ Notify  │
   └─────────┘
```

---

## 5. Connectors (Plugins)

### 5.1 Interface Base

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, AsyncGenerator
from dataclasses import dataclass

@dataclass
class ConnectorResult:
    success: bool
    rows_processed: int = 0
    bytes_transferred: int = 0
    output_path: str = None
    metadata: Dict[str, Any] = None
    error: str = None

@dataclass
class LogEntry:
    level: str  # INFO, WARN, ERROR, DEBUG
    message: str
    timestamp: str
    metadata: Dict[str, Any] = None

class BaseConnector(ABC):
    """Interface base para todos os connectors ETL"""

    def __init__(self, config: Dict[str, Any], credentials: Dict[str, Any]):
        self.config = config
        self.credentials = credentials
        self._cancelled = False

    @property
    @abstractmethod
    def name(self) -> str:
        """Nome único do connector"""
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """Versão do connector"""
        pass

    @abstractmethod
    async def validate(self) -> bool:
        """Valida configuração e credenciais antes de executar"""
        pass

    @abstractmethod
    async def execute(
        self,
        parameters: Dict[str, Any],
        log_callback: callable
    ) -> AsyncGenerator[LogEntry, None]:
        """
        Executa o connector.
        Yield LogEntry para streaming de logs.
        """
        pass

    @abstractmethod
    async def get_progress(self) -> int:
        """Retorna progresso atual (0-100)"""
        pass

    async def cancel(self):
        """Cancela execução em andamento"""
        self._cancelled = True

    @abstractmethod
    async def cleanup(self):
        """Limpa recursos após execução"""
        pass

    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        """Retorna JSON Schema para configuração"""
        pass
```

### 5.2 Exemplo: AMPLIS Connector

```python
class AMPLISConnector(BaseConnector):
    """Connector para sistema AMPLIS"""

    name = "amplis"
    version = "2.0.0"

    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "account_type": {
                    "type": "string",
                    "enum": ["reag", "master"],
                    "description": "Tipo de conta AMPLIS"
                },
                "download_csv": {
                    "type": "boolean",
                    "default": True
                },
                "download_pdf": {
                    "type": "boolean",
                    "default": True
                },
                "date_range": {
                    "type": "object",
                    "properties": {
                        "start": {"type": "string", "format": "date"},
                        "end": {"type": "string", "format": "date"}
                    }
                }
            },
            "required": ["account_type", "date_range"]
        }

    async def validate(self) -> bool:
        required = ["url", "username", "password"]
        return all(k in self.credentials for k in required)

    async def execute(self, parameters, log_callback):
        yield LogEntry("INFO", "Iniciando conexão AMPLIS...")

        async with self._create_browser() as browser:
            yield LogEntry("INFO", "Login realizado com sucesso")

            # Download CSV
            if parameters.get("download_csv", True):
                yield LogEntry("INFO", "Baixando arquivos CSV...")
                await self._download_csv(browser, parameters)
                yield LogEntry("SUCCESS", "CSV baixado")

            # Download PDF
            if parameters.get("download_pdf", True):
                yield LogEntry("INFO", "Baixando arquivos PDF...")
                await self._download_pdf(browser, parameters)
                yield LogEntry("SUCCESS", "PDF baixado")

        yield LogEntry("SUCCESS", "AMPLIS concluído com sucesso")
```

### 5.3 Registry de Connectors

```python
class ConnectorRegistry:
    """Registry central de connectors disponíveis"""

    _connectors: Dict[str, Type[BaseConnector]] = {}

    @classmethod
    def register(cls, connector_class: Type[BaseConnector]):
        """Decorator para registrar connector"""
        cls._connectors[connector_class.name] = connector_class
        return connector_class

    @classmethod
    def get(cls, name: str) -> Type[BaseConnector]:
        if name not in cls._connectors:
            raise ValueError(f"Connector '{name}' não encontrado")
        return cls._connectors[name]

    @classmethod
    def list_all(cls) -> List[Dict[str, Any]]:
        return [
            {
                "name": c.name,
                "version": c.version,
                "schema": c.get_schema()
            }
            for c in cls._connectors.values()
        ]

# Uso
@ConnectorRegistry.register
class AMPLISConnector(BaseConnector):
    ...
```

---

## 6. Isolamento de Execução

### 6.1 Container por Step

```yaml
# Kubernetes Job Template
apiVersion: batch/v1
kind: Job
metadata:
  name: etl-step-${step_id}
  labels:
    job-id: ${job_id}
    step-id: ${step_id}
    connector: ${connector_type}
spec:
  ttlSecondsAfterFinished: 3600
  backoffLimit: 3
  activeDeadlineSeconds: 3600
  template:
    spec:
      restartPolicy: Never

      # Security Context
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000

      containers:
      - name: executor
        image: etl-executor:${version}

        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "2Gi"
            cpu: "1000m"

        env:
        - name: JOB_ID
          value: "${job_id}"
        - name: STEP_ID
          value: "${step_id}"
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: etl-secrets
              key: redis-url

        volumeMounts:
        - name: workspace
          mountPath: /workspace
        - name: credentials
          mountPath: /secrets
          readOnly: true

      volumes:
      - name: workspace
        emptyDir:
          sizeLimit: 10Gi
      - name: credentials
        secret:
          secretName: etl-credentials-${job_id}
```

### 6.2 Benefícios do Isolamento

| Aspecto | Benefício |
|---------|-----------|
| **Segurança** | Credenciais isoladas por job |
| **Recursos** | Limites de CPU/memória por step |
| **Falhas** | Falha em um step não afeta outros |
| **Escalabilidade** | Steps podem rodar em nós diferentes |
| **Cleanup** | Container destruído após execução |

---

## 7. Observabilidade

### 7.1 Métricas (Prometheus)

```python
from prometheus_client import Counter, Histogram, Gauge

# Counters
jobs_total = Counter(
    'etl_jobs_total',
    'Total de jobs executados',
    ['pipeline', 'status', 'trigger_type']
)

steps_total = Counter(
    'etl_steps_total',
    'Total de steps executados',
    ['connector', 'status']
)

# Histograms
job_duration = Histogram(
    'etl_job_duration_seconds',
    'Duração dos jobs',
    ['pipeline'],
    buckets=[60, 300, 600, 1800, 3600, 7200]
)

step_duration = Histogram(
    'etl_step_duration_seconds',
    'Duração dos steps',
    ['connector'],
    buckets=[10, 30, 60, 300, 600, 1800]
)

# Gauges
active_jobs = Gauge(
    'etl_active_jobs',
    'Jobs em execução agora'
)

queue_depth = Gauge(
    'etl_queue_depth',
    'Jobs na fila aguardando'
)

workers_available = Gauge(
    'etl_workers_available',
    'Workers disponíveis'
)
```

### 7.2 Tracing (OpenTelemetry)

```python
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

tracer = trace.get_tracer(__name__)

async def execute_job(job_id: str):
    with tracer.start_as_current_span(
        "job.execute",
        attributes={
            "job.id": job_id,
            "job.pipeline": pipeline_name
        }
    ) as span:
        try:
            for step in steps:
                with tracer.start_as_current_span(
                    f"step.{step.connector}",
                    attributes={
                        "step.id": step.id,
                        "step.connector": step.connector
                    }
                ) as step_span:
                    result = await execute_step(step)
                    step_span.set_attribute("rows_processed", result.rows)

            span.set_status(Status(StatusCode.OK))
        except Exception as e:
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)
            raise
```

### 7.3 Logging Estruturado

```python
import structlog

logger = structlog.get_logger()

logger.info(
    "step_started",
    job_id=job_id,
    step_id=step_id,
    connector=connector_type,
    parameters=parameters
)

logger.info(
    "step_completed",
    job_id=job_id,
    step_id=step_id,
    duration_ms=duration,
    rows_processed=rows,
    status="success"
)
```

### 7.4 Dashboard Grafana

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ETL MONITORING DASHBOARD                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │ Jobs/hora    │  │ Success Rate │  │ Avg Duration │  │ Queue Depth  │    │
│  │    127       │  │    98.5%     │  │   4m 32s     │  │     12       │    │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘    │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    Jobs por Hora (últimas 24h)                      │   │
│  │  ▄▄▄                                                                │   │
│  │ ████▄▄                                    ▄▄▄▄                      │   │
│  │ ██████▄▄▄                              ▄▄█████▄▄                    │   │
│  │ █████████▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄██████████                    │   │
│  │ 00  02  04  06  08  10  12  14  16  18  20  22                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌────────────────────────────┐  ┌────────────────────────────┐            │
│  │   Duração por Connector    │  │   Erros por Tipo           │            │
│  │                            │  │                            │            │
│  │  AMPLIS  ████████  4m      │  │  Timeout     ███  3        │            │
│  │  MAPS    ██████    3m      │  │  Auth        ██   2        │            │
│  │  FIDC    ████      2m      │  │  Network     █    1        │            │
│  │  QORE    ██████████ 5m     │  │  Other       █    1        │            │
│  └────────────────────────────┘  └────────────────────────────┘            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 8. API Design

### 8.1 REST Endpoints

```yaml
# Pipelines
GET    /api/v1/pipelines                    # Listar pipelines
POST   /api/v1/pipelines                    # Criar pipeline
GET    /api/v1/pipelines/{id}               # Detalhes pipeline
PUT    /api/v1/pipelines/{id}               # Atualizar pipeline
DELETE /api/v1/pipelines/{id}               # Deletar pipeline
POST   /api/v1/pipelines/{id}/execute       # Executar pipeline
POST   /api/v1/pipelines/{id}/validate      # Validar pipeline

# Jobs
GET    /api/v1/jobs                         # Listar jobs
GET    /api/v1/jobs/{id}                    # Detalhes job
POST   /api/v1/jobs/{id}/cancel             # Cancelar job
POST   /api/v1/jobs/{id}/retry              # Retry job
GET    /api/v1/jobs/{id}/logs               # Logs do job
GET    /api/v1/jobs/{id}/artifacts          # Artefatos do job

# Steps
GET    /api/v1/jobs/{id}/steps              # Steps do job
GET    /api/v1/jobs/{id}/steps/{step_id}    # Detalhes step
GET    /api/v1/jobs/{id}/steps/{step_id}/logs  # Logs do step

# Connectors
GET    /api/v1/connectors                   # Listar connectors
GET    /api/v1/connectors/{name}            # Detalhes connector
GET    /api/v1/connectors/{name}/schema     # Schema do connector

# Credentials
GET    /api/v1/credentials                  # Listar credentials (masked)
POST   /api/v1/credentials                  # Criar credential
PUT    /api/v1/credentials/{id}             # Atualizar credential
DELETE /api/v1/credentials/{id}             # Deletar credential
POST   /api/v1/credentials/{id}/test        # Testar credential

# Schedules
GET    /api/v1/schedules                    # Listar schedules
POST   /api/v1/schedules                    # Criar schedule
PUT    /api/v1/schedules/{id}               # Atualizar schedule
DELETE /api/v1/schedules/{id}               # Deletar schedule
POST   /api/v1/schedules/{id}/pause         # Pausar schedule
POST   /api/v1/schedules/{id}/resume        # Resumir schedule

# Metrics
GET    /api/v1/metrics/summary              # Resumo métricas
GET    /api/v1/metrics/pipelines/{id}       # Métricas por pipeline
GET    /api/v1/metrics/connectors/{name}    # Métricas por connector
```

### 8.2 WebSocket Events

```typescript
// Client → Server
interface ClientMessage {
    type: 'subscribe' | 'unsubscribe';
    channel: string;  // 'job:{id}' | 'pipeline:{id}' | 'global'
}

// Server → Client
interface ServerMessage {
    type: 'log' | 'status' | 'progress' | 'complete' | 'error';
    channel: string;
    payload: LogPayload | StatusPayload | ProgressPayload | CompletePayload;
    timestamp: string;
}

interface LogPayload {
    job_id: string;
    step_id?: string;
    level: 'INFO' | 'WARN' | 'ERROR' | 'DEBUG';
    message: string;
    metadata?: Record<string, any>;
}

interface ProgressPayload {
    job_id: string;
    step_id: string;
    progress: number;  // 0-100
    rows_processed?: number;
    estimated_remaining?: number;  // seconds
}

interface CompletePayload {
    job_id: string;
    status: 'success' | 'failed' | 'cancelled';
    duration_ms: number;
    summary: {
        steps_total: number;
        steps_success: number;
        steps_failed: number;
        rows_processed: number;
    };
}
```

---

## 9. Segurança

### 9.1 Autenticação & Autorização

```python
# RBAC (Role-Based Access Control)
ROLES = {
    "admin": {
        "pipelines": ["create", "read", "update", "delete", "execute"],
        "jobs": ["read", "cancel", "retry"],
        "credentials": ["create", "read", "update", "delete"],
        "users": ["create", "read", "update", "delete"],
    },
    "operator": {
        "pipelines": ["read", "execute"],
        "jobs": ["read", "cancel"],
        "credentials": ["read"],
        "users": [],
    },
    "viewer": {
        "pipelines": ["read"],
        "jobs": ["read"],
        "credentials": [],
        "users": [],
    }
}

# JWT com refresh tokens
ACCESS_TOKEN_EXPIRE = 15  # minutos
REFRESH_TOKEN_EXPIRE = 7  # dias
```

### 9.2 Criptografia

```python
# Credenciais: AES-256-GCM + PBKDF2
ENCRYPTION = {
    "algorithm": "AES-256-GCM",
    "key_derivation": "PBKDF2-SHA256",
    "iterations": 600_000,
    "salt_length": 32,
    "nonce_length": 12,
    "tag_length": 16,
}

# Secrets em Kubernetes
# - Credenciais injetadas como secrets
# - Rotação automática
# - Nunca em variáveis de ambiente
```

### 9.3 Network Security

```yaml
# Network Policies (Kubernetes)
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: etl-executor-policy
spec:
  podSelector:
    matchLabels:
      app: etl-executor
  policyTypes:
  - Ingress
  - Egress
  ingress: []  # Nenhum ingress permitido
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: redis
  - to:
    - podSelector:
        matchLabels:
          app: postgres
  - to:  # External APIs apenas
    - ipBlock:
        cidr: 0.0.0.0/0
        except:
        - 10.0.0.0/8
        - 172.16.0.0/12
        - 192.168.0.0/16
```

---

## 10. Resiliência

### 10.1 Retry Strategy

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=60),
    retry=retry_if_exception_type((ConnectionError, TimeoutError))
)
async def execute_with_retry(step):
    return await step.execute()
```

### 10.2 Circuit Breaker

```python
from circuitbreaker import circuit

@circuit(
    failure_threshold=5,
    recovery_timeout=30,
    expected_exception=ConnectionError
)
async def call_external_service():
    ...
```

### 10.3 Dead Letter Queue

```python
# Jobs que falharam após todas retries
# vão para DLQ para análise manual

async def handle_failed_job(job_id: str, error: str):
    await queue.publish(
        "dlq.jobs",
        {
            "job_id": job_id,
            "error": error,
            "failed_at": datetime.utcnow().isoformat(),
            "retry_count": job.retry_count
        }
    )

    # Notificar admins
    await notify_admins(
        f"Job {job_id} movido para DLQ após {job.retry_count} tentativas"
    )
```

### 10.4 Checkpoints

```python
# Para jobs longos, salvar checkpoints periódicos

class CheckpointManager:
    async def save(self, step_id: str, state: dict):
        await redis.hset(
            f"checkpoint:{step_id}",
            mapping={
                "state": json.dumps(state),
                "updated_at": datetime.utcnow().isoformat()
            }
        )

    async def restore(self, step_id: str) -> Optional[dict]:
        data = await redis.hget(f"checkpoint:{step_id}", "state")
        return json.loads(data) if data else None

# Uso
checkpoint = CheckpointManager()

async def process_large_file(file_path: str, step_id: str):
    # Tentar restaurar checkpoint
    state = await checkpoint.restore(step_id)
    start_line = state.get("last_line", 0) if state else 0

    with open(file_path) as f:
        for i, line in enumerate(f):
            if i < start_line:
                continue

            await process_line(line)

            # Checkpoint a cada 1000 linhas
            if i % 1000 == 0:
                await checkpoint.save(step_id, {"last_line": i})
```

---

## 11. Deployment

### 11.1 Kubernetes Architecture

```yaml
# Namespace
apiVersion: v1
kind: Namespace
metadata:
  name: etl-system

---
# Backend Deployment (Auto-scaling)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: etl-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: etl-backend
  template:
    spec:
      containers:
      - name: backend
        image: etl-backend:latest
        ports:
        - containerPort: 8000
        resources:
          requests:
            cpu: "500m"
            memory: "512Mi"
          limits:
            cpu: "2000m"
            memory: "2Gi"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5

---
# HPA (Horizontal Pod Autoscaler)
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: etl-backend-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: etl-backend
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70

---
# Workers (Celery)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: etl-worker
spec:
  replicas: 5
  template:
    spec:
      containers:
      - name: worker
        image: etl-worker:latest
        command: ["celery", "-A", "worker", "worker", "-l", "info"]
        resources:
          requests:
            cpu: "1000m"
            memory: "1Gi"
          limits:
            cpu: "2000m"
            memory: "4Gi"
```

### 11.2 Docker Compose (Development)

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://etl:etl@postgres:5432/etl
      - REDIS_URL=redis://redis:6379/0
      - RABBITMQ_URL=amqp://rabbitmq:5672
    depends_on:
      - postgres
      - redis
      - rabbitmq

  worker:
    build: ./backend
    command: celery -A worker worker -l info -c 4
    environment:
      - DATABASE_URL=postgresql://etl:etl@postgres:5432/etl
      - REDIS_URL=redis://redis:6379/0
      - RABBITMQ_URL=amqp://rabbitmq:5672
    depends_on:
      - postgres
      - redis
      - rabbitmq

  scheduler:
    build: ./backend
    command: celery -A worker beat -l info
    depends_on:
      - worker

  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    depends_on:
      - backend

  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: etl
      POSTGRES_PASSWORD: etl
      POSTGRES_DB: etl
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

  rabbitmq:
    image: rabbitmq:3-management-alpine
    ports:
      - "15672:15672"

  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana
    ports:
      - "3001:3000"

volumes:
  postgres_data:
  redis_data:
```

---

## 12. Comparação: Atual vs Ideal

| Aspecto | Sistema Atual | Sistema Ideal |
|---------|---------------|---------------|
| **Database** | SQLite | PostgreSQL |
| **Queue** | Polling SQLite | RabbitMQ/Kafka |
| **Workers** | Single process | Celery distributed |
| **Isolation** | Subprocess | Kubernetes Jobs |
| **Scaling** | Manual | Auto-scaling (HPA) |
| **Observability** | Logs básicos | Prometheus + Grafana + Jaeger |
| **Retry** | Básico | Exponential backoff + DLQ |
| **DAG** | Sequencial | Paralelo com dependências |
| **Connectors** | Hardcoded | Plugin architecture |
| **API** | Básica | REST + GraphQL + WebSocket |
| **Auth** | JWT simples | RBAC + MFA |
| **Deploy** | Manual | CI/CD + GitOps |

---

## 13. Roadmap de Implementação

### Fase 1: Foundation (4-6 semanas)
- [ ] Migrar SQLite → PostgreSQL
- [ ] Implementar Celery + RabbitMQ
- [ ] Criar interface BaseConnector
- [ ] Migrar connectors existentes

### Fase 2: Observability (2-4 semanas)
- [ ] Integrar Prometheus
- [ ] Configurar Grafana dashboards
- [ ] Implementar OpenTelemetry
- [ ] Estruturar logs (structlog)

### Fase 3: Resilience (2-4 semanas)
- [ ] Implementar retry strategy
- [ ] Adicionar circuit breakers
- [ ] Criar Dead Letter Queue
- [ ] Implementar checkpoints

### Fase 4: Scaling (4-6 semanas)
- [ ] Containerizar com Docker
- [ ] Deploy Kubernetes
- [ ] Configurar HPA
- [ ] Implementar job isolation

### Fase 5: Advanced (4-6 semanas)
- [ ] DAG execution engine
- [ ] Scheduler (cron jobs)
- [ ] API v2 (GraphQL)
- [ ] UI redesign

---

## 14. Conclusão

Este plano define um sistema ETL **enterprise-grade** com:

- **Escalabilidade**: De 1 a 1000+ jobs/hora
- **Resiliência**: Retry, circuit breaker, DLQ
- **Observabilidade**: Métricas, traces, logs
- **Segurança**: RBAC, criptografia, isolamento
- **Extensibilidade**: Plugin architecture
- **Operabilidade**: GitOps, auto-scaling

A implementação pode ser feita de forma incremental, mantendo compatibilidade com o sistema atual enquanto evolui para a arquitetura ideal.
