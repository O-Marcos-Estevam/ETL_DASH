# 🚀 Plano de Profissionalização - ETL_DASH

## Visão Geral

Este documento detalha todos os passos necessários para transformar o ETL_DASH em um **sistema de produção profissional**, seguindo as melhores práticas da indústria.

**Estimativa Total**: 8-12 semanas
**Prioridade**: Segurança → Escalabilidade → Qualidade → DevOps

---

## 📊 Resumo das Fases

| Fase | Descrição | Prioridade | Estimativa |
|------|-----------|------------|------------|
| 1 | Segurança | 🔴 Crítica | 1-2 semanas |
| 2 | Banco de Dados | 🔴 Crítica | 1 semana |
| 3 | Arquitetura | 🟠 Alta | 1-2 semanas |
| 4 | Qualidade (Testes) | 🟠 Alta | 2 semanas |
| 5 | Escalabilidade | 🟡 Média | 1-2 semanas |
| 6 | Observabilidade | 🟡 Média | 1 semana |
| 7 | DevOps | 🟡 Média | 1 semana |
| 8 | Documentação | 🟢 Normal | 3-5 dias |

---

# FASE 1: Segurança 🔐

## 1.1 Autenticação JWT

### Objetivo
Implementar autenticação baseada em JWT (JSON Web Tokens) para proteger todos os endpoints da API.

### Passos

#### 1.1.1 Criar módulo de autenticação
```
backend/
├── core/
│   ├── auth.py          # NOVO: Lógica de autenticação
│   ├── security.py      # NOVO: Funções de criptografia
│   └── dependencies.py  # NOVO: Dependências FastAPI
```

**Arquivo: `backend/core/auth.py`**
- Implementar `create_access_token(data: dict) -> str`
- Implementar `verify_token(token: str) -> TokenPayload`
- Implementar `get_password_hash(password: str) -> str`
- Implementar `verify_password(plain: str, hashed: str) -> bool`

**Bibliotecas necessárias:**
```
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
```

#### 1.1.2 Criar modelo de usuário
```python
# backend/models/user.py
class User(BaseModel):
    id: int
    username: str
    email: str
    hashed_password: str
    is_active: bool = True
    is_admin: bool = False
    created_at: datetime
```

#### 1.1.3 Criar endpoints de autenticação
```
POST /api/auth/login      → Retorna access_token + refresh_token
POST /api/auth/refresh    → Renova access_token
POST /api/auth/logout     → Invalida tokens
GET  /api/auth/me         → Retorna usuário atual
```

#### 1.1.4 Proteger rotas existentes
```python
# Exemplo de proteção
from core.dependencies import get_current_user

@router.post("/execute")
async def execute_pipeline(
    request: ExecuteRequest,
    current_user: User = Depends(get_current_user)  # Requer auth
):
    ...
```

#### 1.1.5 Atualizar frontend
- Criar página de login (`/login`)
- Armazenar token em httpOnly cookie (mais seguro que localStorage)
- Implementar interceptor Axios para incluir token
- Implementar refresh automático de token
- Redirecionar para login quando 401

### Entregáveis
- [ ] Módulo `core/auth.py` com JWT
- [ ] Modelo `User` com senha hash
- [ ] Endpoints `/api/auth/*`
- [ ] Middleware de autenticação
- [ ] Página de login no frontend
- [ ] Interceptor Axios com token

---

## 1.2 Criptografia de Credenciais

### Objetivo
Criptografar credenciais em repouso usando AES-256.

### Passos

#### 1.2.1 Implementar serviço de criptografia
```python
# backend/core/crypto.py
from cryptography.fernet import Fernet

class CryptoService:
    def __init__(self, key: bytes):
        self.fernet = Fernet(key)

    def encrypt(self, data: str) -> str:
        return self.fernet.encrypt(data.encode()).decode()

    def decrypt(self, encrypted: str) -> str:
        return self.fernet.decrypt(encrypted.encode()).decode()
```

#### 1.2.2 Gerar e armazenar chave mestra
- Gerar chave com `Fernet.generate_key()`
- Armazenar em variável de ambiente `ETL_ENCRYPTION_KEY`
- Alternativa: usar AWS KMS, Azure Key Vault, ou HashiCorp Vault

#### 1.2.3 Migrar credentials.json
```python
# Estrutura atual (INSEGURO)
{
    "amplis": {
        "username": "user",
        "password": "plain_text_password"  # ❌
    }
}

# Estrutura nova (SEGURO)
{
    "amplis": {
        "username": "user",
        "password": "gAAAAABf..."  # ✅ Criptografado
    }
}
```

#### 1.2.4 Atualizar CredentialsService
- Descriptografar ao carregar
- Criptografar ao salvar
- Nunca logar senhas em texto plano

### Entregáveis
- [ ] Módulo `core/crypto.py`
- [ ] Script de migração de credenciais existentes
- [ ] `CredentialsService` atualizado
- [ ] Documentação de gerenciamento de chaves

---

## 1.3 Validação de Entrada

### Objetivo
Validar todas as entradas do usuário para prevenir injeção e dados inválidos.

### Passos

#### 1.3.1 Criar schemas Pydantic para todas as requests
```python
# backend/schemas/execution.py
from pydantic import BaseModel, Field, validator
from datetime import date

class ExecuteRequest(BaseModel):
    sistemas: list[str] = Field(..., min_items=1)
    data_inicial: date
    data_final: date
    limpar: bool = False

    @validator('sistemas')
    def validate_sistemas(cls, v):
        allowed = {'amplis_reag', 'amplis_master', 'maps', ...}
        for s in v:
            if s not in allowed:
                raise ValueError(f'Sistema inválido: {s}')
        return v

    @validator('data_final')
    def validate_dates(cls, v, values):
        if 'data_inicial' in values and v < values['data_inicial']:
            raise ValueError('data_final deve ser >= data_inicial')
        return v
```

#### 1.3.2 Sanitizar logs
- Remover credenciais de mensagens de log
- Mascarar dados sensíveis (CPF, CNPJ, etc.)

### Entregáveis
- [ ] Schemas Pydantic para todos os endpoints
- [ ] Validadores customizados
- [ ] Sanitização de logs
- [ ] Testes de validação

---

## 1.4 Rate Limiting

### Objetivo
Proteger API contra abuso e ataques de força bruta.

### Passos

#### 1.4.1 Implementar rate limiting
```python
# Usar slowapi
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/auth/login")
@limiter.limit("5/minute")  # 5 tentativas por minuto
async def login(...):
    ...

@app.post("/api/execute")
@limiter.limit("10/minute")  # 10 execuções por minuto
async def execute(...):
    ...
```

### Entregáveis
- [ ] Rate limiting configurado
- [ ] Limites por endpoint
- [ ] Headers de rate limit na resposta

---

## 1.5 CORS e Headers de Segurança

### Passos

#### 1.5.1 Restringir CORS
```python
# Apenas origens permitidas
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://etl.empresa.com"],  # Específico
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
```

#### 1.5.2 Adicionar headers de segurança
```python
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000"
    return response
```

### Entregáveis
- [ ] CORS restritivo
- [ ] Security headers
- [ ] CSP (Content Security Policy)

---

# FASE 2: Banco de Dados 🗄️

## 2.1 Migração SQLite → PostgreSQL

### Objetivo
Substituir SQLite por PostgreSQL para suportar concorrência e escala.

### Passos

#### 2.1.1 Configurar PostgreSQL
```yaml
# docker-compose.yml
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: etl_dash
      POSTGRES_USER: etl_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
```

#### 2.1.2 Implementar SQLAlchemy ORM
```python
# backend/core/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://...")

engine = create_async_engine(DATABASE_URL, echo=False)
Base = declarative_base()

async def get_db() -> AsyncSession:
    async with AsyncSession(engine) as session:
        yield session
```

#### 2.1.3 Criar modelos ORM
```python
# backend/models/job.py
from sqlalchemy import Column, Integer, String, DateTime, JSON, Enum
from core.database import Base

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(50), nullable=False)
    status = Column(Enum(JobStatus), default=JobStatus.PENDING)
    sistemas = Column(JSON, nullable=False)
    params = Column(JSON)
    logs = Column(Text)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    finished_at = Column(DateTime)
    created_by = Column(Integer, ForeignKey("users.id"))
```

#### 2.1.4 Implementar Alembic para migrações
```bash
# Estrutura
backend/
├── alembic/
│   ├── versions/
│   │   ├── 001_initial.py
│   │   ├── 002_add_users.py
│   │   └── ...
│   ├── env.py
│   └── alembic.ini
```

```bash
# Comandos
alembic revision --autogenerate -m "initial"
alembic upgrade head
```

#### 2.1.5 Script de migração de dados
```python
# scripts/migrate_sqlite_to_postgres.py
# Migrar jobs existentes do SQLite para PostgreSQL
```

### Entregáveis
- [ ] PostgreSQL configurado (Docker)
- [ ] SQLAlchemy ORM implementado
- [ ] Modelos ORM para todas as entidades
- [ ] Alembic configurado
- [ ] Migrações iniciais
- [ ] Script de migração de dados
- [ ] Connection pooling configurado

---

## 2.2 Modelo de Dados Expandido

### Novos modelos

```
users           → Usuários do sistema
jobs            → Fila de execução (expandido)
job_logs        → Logs separados por job
systems         → Configuração de sistemas
credentials     → Credenciais (criptografadas)
audit_logs      → Trilha de auditoria
```

### Schema completo

```sql
-- users
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP
);

-- jobs (expandido)
CREATE TABLE jobs (
    id SERIAL PRIMARY KEY,
    type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    priority INTEGER DEFAULT 0,
    sistemas JSONB NOT NULL,
    params JSONB,
    result JSONB,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    created_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    finished_at TIMESTAMP,
    created_by INTEGER REFERENCES users(id),

    INDEX idx_jobs_status (status),
    INDEX idx_jobs_created_at (created_at)
);

-- job_logs (separado para performance)
CREATE TABLE job_logs (
    id SERIAL PRIMARY KEY,
    job_id INTEGER REFERENCES jobs(id) ON DELETE CASCADE,
    level VARCHAR(10) NOT NULL,
    sistema VARCHAR(50),
    message TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT NOW(),

    INDEX idx_job_logs_job_id (job_id),
    INDEX idx_job_logs_timestamp (timestamp)
);

-- audit_logs
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id INTEGER,
    details JSONB,
    ip_address INET,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Entregáveis
- [ ] Schema SQL completo
- [ ] Modelos SQLAlchemy
- [ ] Índices otimizados
- [ ] Relacionamentos definidos

---

# FASE 3: Arquitetura 🏗️

## 3.1 Dependency Injection

### Objetivo
Implementar injeção de dependências para melhor testabilidade e desacoplamento.

### Passos

#### 3.1.1 Criar container de dependências
```python
# backend/core/container.py
from dependency_injector import containers, providers

class Container(containers.DeclarativeContainer):
    config = providers.Configuration()

    # Database
    db_engine = providers.Singleton(
        create_async_engine,
        config.database_url
    )

    # Services
    credentials_service = providers.Factory(
        CredentialsService,
        crypto=providers.Dependency()
    )

    sistema_service = providers.Singleton(SistemaService)

    executor_service = providers.Factory(
        ETLExecutor,
        sistema_service=sistema_service
    )

    worker_service = providers.Singleton(
        BackgroundWorker,
        executor=executor_service
    )
```

#### 3.1.2 Integrar com FastAPI
```python
# backend/app.py
from core.container import Container

container = Container()
container.config.from_dict(settings.dict())

app = FastAPI()
app.container = container

# Usar em rotas
@router.post("/execute")
async def execute(
    request: ExecuteRequest,
    executor: ETLExecutor = Depends(Provide[Container.executor_service])
):
    ...
```

### Entregáveis
- [ ] Container de DI configurado
- [ ] Todos os services refatorados
- [ ] Testes usando mocks via DI

---

## 3.2 Consolidar Configuração

### Objetivo
Centralizar toda configuração em um único módulo.

### Passos

#### 3.2.1 Criar Settings com Pydantic
```python
# backend/core/settings.py
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Server
    host: str = "0.0.0.0"
    port: int = 4001
    debug: bool = False

    # Database
    database_url: str = "postgresql+asyncpg://..."

    # Security
    secret_key: str
    encryption_key: str
    access_token_expire_minutes: int = 30

    # Redis
    redis_url: str = "redis://localhost:6379"

    # Execution
    job_timeout: int = 3600
    max_retries: int = 3

    # Paths
    config_dir: Path = Path("config")
    logs_dir: Path = Path("logs")

    class Config:
        env_file = ".env"
        env_prefix = "ETL_"

@lru_cache
def get_settings() -> Settings:
    return Settings()
```

#### 3.2.2 Remover paths hardcoded
- Usar `settings.config_dir` em vez de `os.path.dirname(__file__)`
- Injetar paths via configuração

### Entregáveis
- [ ] `Settings` centralizado
- [ ] Arquivo `.env.example` atualizado
- [ ] Paths injetados via config
- [ ] Validação de configuração no startup

---

## 3.3 Estado Global → Gerenciado

### Objetivo
Eliminar variáveis globais e centralizar estado.

### Passos

#### 3.3.1 Backend - Eliminar state.py
```python
# ANTES (state.py)
ws_manager = None  # Global mutável

# DEPOIS (via DI)
class AppState:
    def __init__(self):
        self.ws_manager = ConnectionManager()
        self.worker = None

    async def startup(self):
        self.worker = BackgroundWorker(...)
        await self.worker.start()

    async def shutdown(self):
        await self.worker.stop()
```

#### 3.3.2 Frontend - Implementar Zustand
```typescript
// frontend/src/stores/etl-store.ts
import { create } from 'zustand'
import { devtools, persist } from 'zustand/middleware'

interface ETLState {
    // Estado
    config: ConfiguracaoETL | null
    sistemas: Sistema[]
    currentJob: Job | null
    logs: LogEntry[]
    isExecuting: boolean
    isConnected: boolean

    // Actions
    setConfig: (config: ConfiguracaoETL) => void
    updateSistema: (id: string, updates: Partial<Sistema>) => void
    addLog: (log: LogEntry) => void
    clearLogs: () => void
    setExecuting: (value: boolean) => void
}

export const useETLStore = create<ETLState>()(
    devtools(
        persist(
            (set) => ({
                config: null,
                sistemas: [],
                currentJob: null,
                logs: [],
                isExecuting: false,
                isConnected: false,

                setConfig: (config) => set({ config }),
                updateSistema: (id, updates) => set((state) => ({
                    sistemas: state.sistemas.map(s =>
                        s.id === id ? { ...s, ...updates } : s
                    )
                })),
                addLog: (log) => set((state) => ({
                    logs: [...state.logs.slice(-999), log]  // Max 1000 logs
                })),
                clearLogs: () => set({ logs: [] }),
                setExecuting: (value) => set({ isExecuting: value })
            }),
            { name: 'etl-storage' }
        )
    )
)
```

### Entregáveis
- [ ] `state.py` eliminado
- [ ] `AppState` implementado
- [ ] Zustand store criado
- [ ] Componentes usando store

---

## 3.4 Separar Logs em Tabela Própria

### Objetivo
Melhorar performance separando logs dos jobs.

### Passos

```python
# ANTES: logs concatenados no job
UPDATE jobs SET logs = logs || 'nova linha'

# DEPOIS: tabela separada
INSERT INTO job_logs (job_id, level, sistema, message) VALUES (...)
```

### Entregáveis
- [ ] Tabela `job_logs` criada
- [ ] `LogRepository` implementado
- [ ] Queries otimizadas com paginação

---

# FASE 4: Qualidade 🧪

## 4.1 Testes Unitários Backend

### Objetivo
Atingir 80%+ de cobertura de código.

### Estrutura de testes
```
backend/tests/
├── conftest.py              # Fixtures globais
├── unit/
│   ├── test_auth.py         # Testes de autenticação
│   ├── test_crypto.py       # Testes de criptografia
│   ├── test_executor.py     # Testes do executor
│   ├── test_worker.py       # Testes do worker
│   ├── test_credentials.py  # Testes de credenciais
│   ├── test_sistemas.py     # Testes de sistemas
│   └── test_models.py       # Testes de modelos
├── integration/
│   ├── test_api_auth.py     # Testes de API auth
│   ├── test_api_execute.py  # Testes de API execute
│   ├── test_api_config.py   # Testes de API config
│   ├── test_websocket.py    # Testes WebSocket
│   └── test_database.py     # Testes de banco
└── e2e/
    └── test_full_pipeline.py # Teste end-to-end
```

### Ferramentas
```
pytest==8.3.4
pytest-asyncio==0.24.0
pytest-cov==4.1.0
pytest-mock==3.14.0
httpx==0.27.0          # Async HTTP client para testes
factory-boy==3.3.0     # Factories para modelos
faker==24.0.0          # Dados fake
```

### Meta de cobertura
```bash
pytest --cov=backend --cov-report=html --cov-fail-under=80
```

### Entregáveis
- [ ] 80%+ cobertura
- [ ] Testes de auth
- [ ] Testes de API (integration)
- [ ] Testes de WebSocket
- [ ] Testes de database
- [ ] CI rodando testes

---

## 4.2 Testes Frontend

### Estrutura
```
frontend/
├── src/
│   └── __tests__/           # Testes unitários
│       ├── components/
│       ├── hooks/
│       ├── stores/
│       └── utils/
├── e2e/                     # Testes E2E
│   ├── auth.spec.ts
│   ├── etl.spec.ts
│   └── settings.spec.ts
├── vitest.config.ts
└── playwright.config.ts
```

### Ferramentas
```json
{
  "devDependencies": {
    "@testing-library/react": "^14.0.0",
    "@testing-library/jest-dom": "^6.0.0",
    "@testing-library/user-event": "^14.0.0",
    "vitest": "^1.0.0",
    "@vitest/coverage-v8": "^1.0.0",
    "msw": "^2.0.0",
    "playwright": "^1.40.0"
  }
}
```

### Entregáveis
- [ ] Vitest configurado
- [ ] Testes de componentes
- [ ] Testes de hooks
- [ ] Testes de store
- [ ] Playwright E2E
- [ ] 70%+ cobertura frontend

---

## 4.3 CI/CD Pipeline

### GitHub Actions

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_PASSWORD: test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r backend/requirements-dev.txt
      - run: pytest backend/tests --cov --cov-fail-under=80

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: cd frontend && npm ci
      - run: cd frontend && npm run test -- --coverage
      - run: cd frontend && npm run build

  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install ruff
      - run: ruff check backend/
      - run: cd frontend && npm ci && npm run lint

  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install bandit safety
      - run: bandit -r backend/
      - run: safety check -r backend/requirements.txt
```

### Entregáveis
- [ ] CI configurado
- [ ] Testes automatizados
- [ ] Linting automatizado
- [ ] Security scanning
- [ ] Build automático

---

## 4.4 Linting e Formatação

### Backend
```toml
# pyproject.toml
[tool.ruff]
line-length = 100
select = ["E", "F", "W", "I", "N", "S", "B"]

[tool.black]
line-length = 100

[tool.mypy]
python_version = "3.11"
strict = true
```

### Frontend
```json
// .eslintrc.json
{
  "extends": [
    "eslint:recommended",
    "plugin:@typescript-eslint/recommended",
    "plugin:react-hooks/recommended",
    "prettier"
  ]
}
```

### Pre-commit hooks
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.0
    hooks:
      - id: ruff
      - id: ruff-format
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.0.0
    hooks:
      - id: mypy
```

### Entregáveis
- [ ] Ruff + Black configurados
- [ ] ESLint + Prettier configurados
- [ ] MyPy para type checking
- [ ] Pre-commit hooks
- [ ] Editor configs (.editorconfig)

---

# FASE 5: Escalabilidade 📈

## 5.1 Message Queue (Celery + Redis)

### Objetivo
Permitir execução paralela de jobs e melhor gerenciamento de filas.

### Arquitetura
```
┌─────────────┐     ┌─────────┐     ┌──────────────┐
│  FastAPI    │────▶│  Redis  │────▶│ Celery       │
│  (Producer) │     │ (Broker)│     │ Workers (N)  │
└─────────────┘     └─────────┘     └──────────────┘
```

### Implementação

```python
# backend/core/celery.py
from celery import Celery

celery_app = Celery(
    "etl_dash",
    broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1"),
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="America/Sao_Paulo",
    task_track_started=True,
    task_time_limit=3600,
    worker_prefetch_multiplier=1,
    worker_concurrency=4,
)
```

```python
# backend/tasks/etl.py
from core.celery import celery_app

@celery_app.task(bind=True, max_retries=3)
def execute_pipeline(self, job_id: int, sistemas: list, params: dict):
    try:
        # Executar ETL
        executor = ETLExecutor()
        result = executor.execute(sistemas, params)
        return {"status": "success", "result": result}
    except Exception as e:
        self.retry(exc=e, countdown=60)
```

```python
# Endpoint atualizado
@router.post("/execute")
async def execute(request: ExecuteRequest):
    job = await create_job(request)
    task = execute_pipeline.delay(job.id, request.sistemas, request.params)
    return {"job_id": job.id, "task_id": task.id}
```

### Docker Compose
```yaml
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  celery-worker:
    build: ./backend
    command: celery -A core.celery worker -l info -c 4
    depends_on:
      - redis
      - postgres
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0

  celery-beat:
    build: ./backend
    command: celery -A core.celery beat -l info
    depends_on:
      - redis
```

### Entregáveis
- [ ] Celery configurado
- [ ] Tasks de ETL
- [ ] Workers escaláveis
- [ ] Monitoramento (Flower)
- [ ] Retry automático

---

## 5.2 Redis para WebSocket Pub/Sub

### Objetivo
Permitir broadcast entre múltiplas instâncias do backend.

### Implementação
```python
# backend/core/pubsub.py
import aioredis

class RedisPubSub:
    def __init__(self, redis_url: str):
        self.redis = aioredis.from_url(redis_url)
        self.pubsub = self.redis.pubsub()

    async def publish(self, channel: str, message: dict):
        await self.redis.publish(channel, json.dumps(message))

    async def subscribe(self, channel: str, callback):
        await self.pubsub.subscribe(channel)
        async for message in self.pubsub.listen():
            if message["type"] == "message":
                await callback(json.loads(message["data"]))
```

```python
# backend/app.py
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Inscrever no Redis
        await pubsub.subscribe("etl:logs",
            lambda msg: websocket.send_json(msg))

        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
```

### Entregáveis
- [ ] Redis pub/sub implementado
- [ ] WebSocket usando Redis
- [ ] Múltiplas instâncias suportadas

---

## 5.3 Cache com Redis

### Implementação
```python
# backend/core/cache.py
from functools import wraps
import aioredis

redis = aioredis.from_url(settings.redis_url)

def cached(ttl: int = 300):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"

            cached = await redis.get(key)
            if cached:
                return json.loads(cached)

            result = await func(*args, **kwargs)
            await redis.setex(key, ttl, json.dumps(result))
            return result
        return wrapper
    return decorator

# Uso
@cached(ttl=60)
async def get_sistemas():
    return await db.query(Sistema).all()
```

### Entregáveis
- [ ] Cache layer implementado
- [ ] Invalidação de cache
- [ ] Cache de configuração
- [ ] Cache de sistemas

---

# FASE 6: Observabilidade 📊

## 6.1 Logging Estruturado

### Implementação
```python
# backend/core/logging.py
import structlog

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
)

log = structlog.get_logger()

# Uso
log.info("job_started", job_id=123, sistemas=["maps", "qore"])
```

### Output
```json
{
  "event": "job_started",
  "job_id": 123,
  "sistemas": ["maps", "qore"],
  "level": "info",
  "timestamp": "2024-01-15T10:30:00Z",
  "request_id": "abc-123"
}
```

### Entregáveis
- [ ] structlog configurado
- [ ] Request ID em todos os logs
- [ ] Logs JSON para ELK/Loki
- [ ] Log rotation configurado

---

## 6.2 Métricas (Prometheus)

### Implementação
```python
# backend/core/metrics.py
from prometheus_client import Counter, Histogram, Gauge

# Métricas
jobs_total = Counter(
    "etl_jobs_total",
    "Total de jobs executados",
    ["sistema", "status"]
)

job_duration = Histogram(
    "etl_job_duration_seconds",
    "Duração dos jobs em segundos",
    ["sistema"]
)

active_connections = Gauge(
    "etl_websocket_connections",
    "Conexões WebSocket ativas"
)

# Uso
jobs_total.labels(sistema="maps", status="success").inc()
job_duration.labels(sistema="maps").observe(45.2)
```

### Endpoint
```python
from prometheus_client import make_asgi_app

app.mount("/metrics", make_asgi_app())
```

### Entregáveis
- [ ] Métricas de jobs
- [ ] Métricas de API (latência, erros)
- [ ] Métricas de WebSocket
- [ ] Dashboard Grafana

---

## 6.3 Health Checks

### Implementação
```python
# backend/routers/health.py
@router.get("/health")
async def health():
    return {"status": "ok"}

@router.get("/health/ready")
async def readiness():
    checks = {
        "database": await check_database(),
        "redis": await check_redis(),
        "celery": await check_celery(),
    }

    all_healthy = all(c["status"] == "ok" for c in checks.values())
    status_code = 200 if all_healthy else 503

    return JSONResponse(
        content={"status": "ready" if all_healthy else "not_ready", "checks": checks},
        status_code=status_code
    )

@router.get("/health/live")
async def liveness():
    return {"status": "alive"}
```

### Entregáveis
- [ ] `/health` básico
- [ ] `/health/ready` com checks
- [ ] `/health/live` para k8s
- [ ] Alertas configurados

---

## 6.4 Tracing (OpenTelemetry)

### Implementação
```python
# backend/core/tracing.py
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

# Configurar
tracer = trace.get_tracer(__name__)

# Instrumentar FastAPI
FastAPIInstrumentor.instrument_app(app)

# Uso manual
with tracer.start_as_current_span("execute_etl") as span:
    span.set_attribute("job_id", job_id)
    span.set_attribute("sistemas", sistemas)
    result = await executor.execute(...)
```

### Entregáveis
- [ ] OpenTelemetry configurado
- [ ] Auto-instrumentação
- [ ] Traces distribuídos
- [ ] Jaeger/Tempo para visualização

---

# FASE 7: DevOps 🐳

## 7.1 Containerização

### Dockerfile Backend
```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Dependências do sistema
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Código
COPY . .

# Usuário não-root
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 4001

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "4001"]
```

### Dockerfile Frontend
```dockerfile
# frontend/Dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### Entregáveis
- [ ] Dockerfile backend
- [ ] Dockerfile frontend
- [ ] .dockerignore
- [ ] Multi-stage builds
- [ ] Security scanning (Trivy)

---

## 7.2 Docker Compose Completo

```yaml
# docker-compose.yml
version: '3.8'

services:
  # Banco de dados
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: etl_dash
      POSTGRES_USER: etl
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U etl"]
      interval: 5s
      timeout: 5s
      retries: 5

  # Cache e Message Broker
  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s

  # Backend API
  backend:
    build: ./backend
    environment:
      - DATABASE_URL=postgresql+asyncpg://etl:${DB_PASSWORD}@postgres/etl_dash
      - REDIS_URL=redis://redis:6379
      - ETL_SECRET_KEY=${SECRET_KEY}
      - ETL_ENCRYPTION_KEY=${ENCRYPTION_KEY}
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    ports:
      - "4001:4001"

  # Celery Worker
  celery-worker:
    build: ./backend
    command: celery -A core.celery worker -l info -c 4
    environment:
      - DATABASE_URL=postgresql+asyncpg://etl:${DB_PASSWORD}@postgres/etl_dash
      - CELERY_BROKER_URL=redis://redis:6379/0
    depends_on:
      - backend
      - redis
    deploy:
      replicas: 2

  # Frontend
  frontend:
    build: ./frontend
    ports:
      - "4000:80"
    depends_on:
      - backend

  # Monitoramento
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana:latest
    volumes:
      - grafana_data:/var/lib/grafana
    ports:
      - "3000:3000"

volumes:
  postgres_data:
  redis_data:
  grafana_data:
```

### Entregáveis
- [ ] docker-compose.yml completo
- [ ] docker-compose.override.yml (dev)
- [ ] docker-compose.prod.yml
- [ ] Secrets management
- [ ] Health checks

---

## 7.3 Kubernetes (Opcional)

### Estrutura
```
k8s/
├── base/
│   ├── namespace.yaml
│   ├── backend-deployment.yaml
│   ├── backend-service.yaml
│   ├── frontend-deployment.yaml
│   ├── frontend-service.yaml
│   ├── ingress.yaml
│   └── kustomization.yaml
├── overlays/
│   ├── dev/
│   └── prod/
└── secrets/
    └── sealed-secrets.yaml
```

### Entregáveis
- [ ] Deployments
- [ ] Services
- [ ] Ingress
- [ ] ConfigMaps
- [ ] Secrets (sealed)
- [ ] HPA (autoscaling)
- [ ] PDB (disruption budget)

---

## 7.4 CD Pipeline

```yaml
# .github/workflows/cd.yml
name: CD

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Build and push Docker images
        run: |
          docker build -t registry/etl-backend:${{ github.sha }} ./backend
          docker build -t registry/etl-frontend:${{ github.sha }} ./frontend
          docker push registry/etl-backend:${{ github.sha }}
          docker push registry/etl-frontend:${{ github.sha }}

      - name: Deploy to Kubernetes
        run: |
          kubectl set image deployment/backend backend=registry/etl-backend:${{ github.sha }}
          kubectl set image deployment/frontend frontend=registry/etl-frontend:${{ github.sha }}
```

### Entregáveis
- [ ] CI/CD completo
- [ ] Deploy automático
- [ ] Rollback automático
- [ ] Canary/Blue-Green

---

# FASE 8: Documentação 📚

## 8.1 Documentação Técnica

### Estrutura
```
docs/
├── README.md                    # Visão geral
├── ARCHITECTURE.md              # Arquitetura detalhada
├── API.md                       # Referência da API
├── DEPLOYMENT.md                # Guia de deploy
├── DEVELOPMENT.md               # Guia de desenvolvimento
├── SECURITY.md                  # Práticas de segurança
├── TROUBLESHOOTING.md           # Problemas comuns
└── CHANGELOG.md                 # Histórico de mudanças
```

### Entregáveis
- [ ] README atualizado
- [ ] Arquitetura documentada
- [ ] API documentada (OpenAPI)
- [ ] Guia de deploy
- [ ] Runbook operacional

---

## 8.2 API Documentation (OpenAPI)

```python
# backend/app.py
app = FastAPI(
    title="ETL Dashboard API",
    description="API para gerenciamento de pipelines ETL",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)
```

### Entregáveis
- [ ] Swagger UI (`/api/docs`)
- [ ] ReDoc (`/api/redoc`)
- [ ] Exemplos de request/response
- [ ] Autenticação documentada

---

## 8.3 ADRs (Architecture Decision Records)

```
docs/adr/
├── 001-use-fastapi.md
├── 002-postgresql-over-sqlite.md
├── 003-celery-for-jobs.md
├── 004-jwt-authentication.md
└── template.md
```

### Template ADR
```markdown
# ADR-XXX: Título

## Status
Aceito | Rejeitado | Substituído

## Contexto
Por que essa decisão foi necessária?

## Decisão
O que foi decidido?

## Consequências
Quais os impactos positivos e negativos?
```

### Entregáveis
- [ ] ADRs para decisões principais
- [ ] Template de ADR
- [ ] Processo de revisão

---

# 📋 Checklist Final

## Segurança
- [ ] Autenticação JWT implementada
- [ ] Credenciais criptografadas
- [ ] Validação de entrada
- [ ] Rate limiting
- [ ] Headers de segurança
- [ ] CORS restritivo

## Banco de Dados
- [ ] PostgreSQL configurado
- [ ] SQLAlchemy ORM
- [ ] Migrações Alembic
- [ ] Índices otimizados

## Arquitetura
- [ ] Dependency Injection
- [ ] Configuração centralizada
- [ ] Estado gerenciado
- [ ] Logs separados

## Qualidade
- [ ] 80%+ cobertura backend
- [ ] 70%+ cobertura frontend
- [ ] CI/CD configurado
- [ ] Linting + formatação

## Escalabilidade
- [ ] Celery para jobs
- [ ] Redis pub/sub
- [ ] Cache implementado
- [ ] Múltiplos workers

## Observabilidade
- [ ] Logging estruturado
- [ ] Métricas Prometheus
- [ ] Health checks
- [ ] Tracing (opcional)

## DevOps
- [ ] Docker images
- [ ] Docker Compose
- [ ] Kubernetes (opcional)
- [ ] Deploy automático

## Documentação
- [ ] README completo
- [ ] API documentada
- [ ] Guia de deploy
- [ ] ADRs

---

# 🗓️ Cronograma Sugerido

```
Semana 1-2:  FASE 1 - Segurança
Semana 3:    FASE 2 - Banco de Dados
Semana 4-5:  FASE 3 - Arquitetura
Semana 6-7:  FASE 4 - Qualidade (Testes)
Semana 8-9:  FASE 5 - Escalabilidade
Semana 10:   FASE 6 - Observabilidade
Semana 11:   FASE 7 - DevOps
Semana 12:   FASE 8 - Documentação + Buffer
```

---

**Nota**: Este plano é iterativo. Cada fase pode ser ajustada conforme necessidades específicas do projeto. Priorize sempre segurança e qualidade sobre features adicionais.
