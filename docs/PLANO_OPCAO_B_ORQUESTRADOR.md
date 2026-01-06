# 🚀 Plano Opção B: Integração com Orquestrador Profissional

> **Objetivo**: Manter seu frontend React customizado + usar scheduler/executor de um orquestrador battle-tested

---

## 📊 Comparativo de Orquestradores

### Matriz de Decisão

| Critério | Airflow | Prefect | Dagster | **Recomendado** |
|----------|---------|---------|---------|-----------------|
| **Curva de aprendizado** | Alta | Baixa | Média | Prefect |
| **Deploy simples** | Não (muitos componentes) | Sim (server único) | Médio | Prefect |
| **API REST nativa** | Sim (experimental) | Sim (excelente) | Sim | Prefect |
| **Python-native** | Decorators | Decorators | Assets | Prefect |
| **WebSocket/streaming** | Não | Não nativo | Não | Nenhum* |
| **Comunidade** | Enorme | Grande | Crescendo | Airflow |
| **Self-hosted gratuito** | Sim | Sim | Sim | Todos |
| **Retry/backfill** | Excelente | Excelente | Excelente | Todos |
| **UI própria** | Sim (substitui seu frontend) | Sim | Sim | - |
| **Selenium workers** | Possível | Fácil | Possível | Prefect |

### ⭐ Recomendação: **Prefect 2.x**

**Por quê Prefect?**
1. **API REST completa** - Fácil integrar com seu frontend
2. **Deploy simples** - Um server, sem Celery/Redis/Flower
3. **Python puro** - Seus módulos viram tasks com 1 decorator
4. **Logs streaming** - API para buscar logs em tempo real
5. **Gratuito self-hosted** - Prefect Server (não Cloud)

---

## 🏗️ Arquitetura Proposta

```
┌─────────────────────────────────────────────────────────────────────┐
│                        SEU SISTEMA (mantém)                         │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────┐  │
│  │   React      │    │   FastAPI    │    │   PostgreSQL         │  │
│  │   Frontend   │◄──►│   Gateway    │◄──►│   (seu banco)        │  │
│  │   (mantém)   │    │   (novo)     │    │   usuários/config    │  │
│  └──────────────┘    └──────┬───────┘    └──────────────────────┘  │
│                              │                                       │
│                              │ REST API                              │
│                              ▼                                       │
├─────────────────────────────────────────────────────────────────────┤
│                      PREFECT (novo)                                  │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────┐  │
│  │   Prefect    │    │   Prefect    │    │   PostgreSQL         │  │
│  │   Server     │◄──►│   Agent      │    │   (Prefect DB)       │  │
│  │   (API)      │    │   (executor) │    │                      │  │
│  └──────────────┘    └──────┬───────┘    └──────────────────────┘  │
│                              │                                       │
│                              │ Executa                               │
│                              ▼                                       │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    SEUS FLOWS (migrados)                      │   │
│  ├──────────────────────────────────────────────────────────────┤   │
│  │  @flow amplis_flow    │  @flow maps_flow    │  @flow fidc_flow│   │
│  │  @flow britech_flow   │  @flow qore_flow    │  @flow jcot_flow│   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 📁 Estrutura de Diretórios Proposta

```
ETL_DASH/
├── frontend/                    # ✅ MANTÉM (seu React)
│   ├── src/
│   │   ├── pages/
│   │   │   ├── etl/            # Modificar para chamar Gateway
│   │   │   └── logs/           # Buscar logs via Gateway
│   │   └── services/
│   │       └── api.ts          # Atualizar endpoints
│
├── gateway/                     # 🆕 NOVO (FastAPI intermediário)
│   ├── app.py                  # API Gateway
│   ├── routers/
│   │   ├── flows.py            # Trigger flows no Prefect
│   │   ├── runs.py             # Status das execuções
│   │   └── logs.py             # Streaming de logs
│   └── services/
│       └── prefect_client.py   # Cliente para API Prefect
│
├── flows/                       # 🆕 NOVO (Prefect Flows)
│   ├── __init__.py
│   ├── amplis_flow.py
│   ├── maps_flow.py
│   ├── fidc_flow.py
│   ├── britech_flow.py
│   ├── qore_flow.py
│   ├── jcot_flow.py
│   └── tasks/                  # Tasks reutilizáveis
│       ├── selenium_tasks.py
│       ├── file_tasks.py
│       └── notification_tasks.py
│
├── python/                      # ✅ MANTÉM (módulos existentes)
│   └── modules/                # Reutilizados pelos flows
│
├── prefect/                     # 🆕 NOVO (config Prefect)
│   ├── docker-compose.yml      # Prefect Server + Agent
│   └── prefect.yaml            # Configuração
│
└── docker-compose.yml          # Atualizado com todos serviços
```

---

## 🔄 Migração dos Módulos Python para Prefect

### Antes (seu código atual)
```python
# python/main.py - Execução sequencial
def run_amplis(credentials, data_inicial, data_final, ...):
    from amplis_V02 import run_amplis as amplis_run
    amplis_run(username, password, url, ...)
```

### Depois (Prefect Flow)
```python
# flows/amplis_flow.py
from prefect import flow, task, get_run_logger
from prefect.tasks import task_input_hash
from datetime import timedelta
import sys
sys.path.insert(0, '../python/modules')

@task(
    retries=3,
    retry_delay_seconds=60,
    cache_key_fn=task_input_hash,
    cache_expiration=timedelta(hours=1)
)
def download_amplis_csv(username: str, password: str, url: str,
                        data_inicial: str, data_final: str, csv_path: str):
    """Task para download de CSV do AMPLIS"""
    logger = get_run_logger()
    logger.info(f"Iniciando download AMPLIS CSV: {data_inicial} - {data_final}")

    from amplis_V02 import run_reag_process_csv
    run_reag_process_csv(
        custom_inical_date=data_inicial,
        custom_final_date=data_final,
        USERNAME_REAG=username,
        PASSWORD_REAG=password,
        url_reag=url,
        csv_path=csv_path
    )
    logger.info("Download CSV concluído")
    return csv_path

@task(retries=2, retry_delay_seconds=30)
def download_amplis_pdf(username: str, password: str, url: str,
                        data_inicial: str, data_final: str, pdf_path: str):
    """Task para download de PDF do AMPLIS"""
    logger = get_run_logger()
    logger.info(f"Iniciando download AMPLIS PDF")

    from amplis_V02 import run_reag_process_pdf
    run_reag_process_pdf(
        custom_inical_date=data_inicial,
        custom_final_date=data_final,
        USERNAME_REAG=username,
        PASSWORD_REAG=password,
        url_reag=url,
        pdf_path=pdf_path
    )
    return pdf_path

@flow(name="AMPLIS ETL", description="Download de dados AMPLIS (CSV e PDF)")
def amplis_flow(
    tipo: str = "reag",
    data_inicial: str = None,
    data_final: str = None,
    baixar_csv: bool = True,
    baixar_pdf: bool = True,
    credentials: dict = None
):
    """
    Flow principal do AMPLIS

    Pode ser executado via:
    - API REST do Prefect
    - Seu frontend via Gateway
    - Schedule automático
    """
    logger = get_run_logger()
    logger.info(f"Executando AMPLIS {tipo}: {data_inicial} até {data_final}")

    creds = credentials["amplis"][tipo]
    paths = credentials["paths"]

    results = []

    # Executa tasks em paralelo se ambos habilitados
    if baixar_csv:
        csv_result = download_amplis_csv(
            username=creds["username"],
            password=creds["password"],
            url=creds["url"],
            data_inicial=data_inicial,
            data_final=data_final,
            csv_path=paths["csv"]
        )
        results.append(("csv", csv_result))

    if baixar_pdf:
        pdf_result = download_amplis_pdf(
            username=creds["username"],
            password=creds["password"],
            url=creds["url"],
            data_inicial=data_inicial,
            data_final=data_final,
            pdf_path=paths["pdf"]
        )
        results.append(("pdf", pdf_result))

    logger.info(f"AMPLIS {tipo} concluído: {len(results)} downloads")
    return results

# Registro para deployment
if __name__ == "__main__":
    amplis_flow.serve(name="amplis-deployment")
```

---

## 🌐 Gateway API (Ponte Frontend ↔ Prefect)

```python
# gateway/app.py
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import httpx
from datetime import datetime

app = FastAPI(title="ETL Gateway", version="2.0")

# CORS para seu frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

PREFECT_API_URL = "http://localhost:4200/api"

# ============ MODELOS ============

class ExecutionRequest(BaseModel):
    sistemas: List[str]
    data_inicial: str
    data_final: str
    options: Optional[dict] = {}

class FlowRun(BaseModel):
    id: str
    name: str
    state: str
    created: datetime
    updated: datetime

# ============ ROTAS ============

@app.post("/api/execute")
async def execute_systems(request: ExecutionRequest):
    """
    Endpoint compatível com seu frontend atual
    Traduz para chamadas ao Prefect
    """
    flow_runs = []

    # Mapeia sistemas para flows do Prefect
    flow_mapping = {
        "amplis_reag": "amplis-flow",
        "amplis_master": "amplis-flow",
        "maps": "maps-flow",
        "fidc": "fidc-flow",
        "britech": "britech-flow",
        "qore": "qore-flow",
        "jcot": "jcot-flow",
    }

    async with httpx.AsyncClient() as client:
        for sistema in request.sistemas:
            flow_name = flow_mapping.get(sistema)
            if not flow_name:
                continue

            # Cria deployment run no Prefect
            response = await client.post(
                f"{PREFECT_API_URL}/deployments/{flow_name}/create_flow_run",
                json={
                    "parameters": {
                        "data_inicial": request.data_inicial,
                        "data_final": request.data_final,
                        "tipo": "reag" if "reag" in sistema else "master",
                        **request.options
                    }
                }
            )

            if response.status_code == 201:
                run_data = response.json()
                flow_runs.append({
                    "sistema": sistema,
                    "run_id": run_data["id"],
                    "status": "scheduled"
                })

    return {"job_id": flow_runs[0]["run_id"] if flow_runs else None, "runs": flow_runs}

@app.get("/api/runs/{run_id}")
async def get_run_status(run_id: str):
    """Busca status de uma execução"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{PREFECT_API_URL}/flow_runs/{run_id}")
        if response.status_code != 200:
            raise HTTPException(status_code=404, detail="Run not found")

        data = response.json()
        return {
            "id": data["id"],
            "name": data["name"],
            "state": data["state"]["type"],  # PENDING, RUNNING, COMPLETED, FAILED
            "state_message": data["state"].get("message"),
            "created": data["created"],
            "updated": data["updated"],
            "start_time": data.get("start_time"),
            "end_time": data.get("end_time"),
        }

@app.get("/api/runs/{run_id}/logs")
async def get_run_logs(run_id: str, offset: int = 0, limit: int = 100):
    """Busca logs de uma execução (para substituir WebSocket)"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{PREFECT_API_URL}/logs/filter",
            json={
                "logs": {
                    "flow_run_id": {"any_": [run_id]}
                },
                "offset": offset,
                "limit": limit,
                "sort": "TIMESTAMP_ASC"
            }
        )

        if response.status_code != 200:
            return {"logs": []}

        logs = response.json()
        return {
            "logs": [
                {
                    "timestamp": log["timestamp"],
                    "level": log["level"],
                    "message": log["message"],
                    "task_name": log.get("task_run_name")
                }
                for log in logs
            ]
        }

@app.get("/api/runs")
async def list_runs(limit: int = 20, state: Optional[str] = None):
    """Lista execuções recentes"""
    async with httpx.AsyncClient() as client:
        filters = {"limit": limit, "sort": "CREATED_DESC"}
        if state:
            filters["flow_runs"] = {"state": {"type": {"any_": [state]}}}

        response = await client.post(
            f"{PREFECT_API_URL}/flow_runs/filter",
            json=filters
        )
        return response.json()

@app.post("/api/runs/{run_id}/cancel")
async def cancel_run(run_id: str):
    """Cancela uma execução em andamento"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{PREFECT_API_URL}/flow_runs/{run_id}/set_state",
            json={"state": {"type": "CANCELLED"}}
        )
        return {"success": response.status_code == 200}

# Health check
@app.get("/health")
async def health():
    return {"status": "ok", "prefect_url": PREFECT_API_URL}
```

---

## 🐳 Docker Compose Completo

```yaml
# docker-compose.yml
version: '3.8'

services:
  # ============ SEU FRONTEND (mantém) ============
  frontend:
    build: ./frontend
    ports:
      - "4000:80"
    environment:
      - VITE_API_URL=http://localhost:4001
    depends_on:
      - gateway

  # ============ GATEWAY (novo) ============
  gateway:
    build: ./gateway
    ports:
      - "4001:8000"
    environment:
      - PREFECT_API_URL=http://prefect-server:4200/api
      - DATABASE_URL=postgresql://etl:etl@postgres:5432/etl
    depends_on:
      - prefect-server
      - postgres

  # ============ PREFECT SERVER ============
  prefect-server:
    image: prefecthq/prefect:2-python3.11
    command: prefect server start --host 0.0.0.0
    ports:
      - "4200:4200"  # UI do Prefect (opcional, você tem seu frontend)
    environment:
      - PREFECT_SERVER_API_HOST=0.0.0.0
      - PREFECT_API_DATABASE_CONNECTION_URL=postgresql+asyncpg://prefect:prefect@postgres-prefect:5432/prefect
    depends_on:
      - postgres-prefect
    volumes:
      - prefect-data:/root/.prefect

  # ============ PREFECT AGENT (executor) ============
  prefect-agent:
    build:
      context: .
      dockerfile: Dockerfile.agent
    command: prefect agent start -q default
    environment:
      - PREFECT_API_URL=http://prefect-server:4200/api
    depends_on:
      - prefect-server
    volumes:
      - ./flows:/app/flows
      - ./python/modules:/app/modules
      - ./config:/app/config
      - /tmp/selenium:/tmp/selenium  # Para Selenium downloads

  # ============ DATABASES ============
  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=etl
      - POSTGRES_PASSWORD=etl
      - POSTGRES_DB=etl
    volumes:
      - postgres-data:/var/lib/postgresql/data

  postgres-prefect:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=prefect
      - POSTGRES_PASSWORD=prefect
      - POSTGRES_DB=prefect
    volumes:
      - postgres-prefect-data:/var/lib/postgresql/data

  # ============ SELENIUM GRID (para seus scrapers) ============
  selenium-hub:
    image: selenium/hub:4.15
    ports:
      - "4444:4444"

  chrome-node:
    image: selenium/node-chrome:4.15
    shm_size: 2gb
    environment:
      - SE_EVENT_BUS_HOST=selenium-hub
      - SE_EVENT_BUS_PUBLISH_PORT=4442
      - SE_EVENT_BUS_SUBSCRIBE_PORT=4443
      - SE_NODE_MAX_SESSIONS=4
    depends_on:
      - selenium-hub
    volumes:
      - /tmp/selenium:/home/seluser/Downloads

volumes:
  prefect-data:
  postgres-data:
  postgres-prefect-data:
```

---

## 📝 Dockerfile do Agent

```dockerfile
# Dockerfile.agent
FROM prefecthq/prefect:2-python3.11

WORKDIR /app

# Dependências do seu projeto
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Selenium + Chrome
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Seus flows
COPY flows/ /app/flows/
COPY python/modules/ /app/modules/

# Registra flows
ENV PYTHONPATH=/app:/app/modules

CMD ["prefect", "agent", "start", "-q", "default"]
```

---

## 📊 Modificações no Frontend

### Mudanças Mínimas Necessárias

```typescript
// frontend/src/services/api.ts

// ANTES: Chamava seu backend diretamente
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:4001';

// DEPOIS: Mesmo endpoint, Gateway traduz para Prefect
// Não muda nada! O Gateway é compatível

export async function executeETL(params: ExecutionParams) {
  // Esta chamada continua funcionando
  const response = await fetch(`${API_BASE}/api/execute`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params)
  });
  return response.json();
}

// NOVO: Polling de logs (substitui WebSocket)
export async function pollLogs(runId: string, offset: number = 0) {
  const response = await fetch(
    `${API_BASE}/api/runs/${runId}/logs?offset=${offset}`
  );
  return response.json();
}

// NOVO: Status da execução
export async function getRunStatus(runId: string) {
  const response = await fetch(`${API_BASE}/api/runs/${runId}`);
  return response.json();
}
```

### Hook para Logs (substitui WebSocket)

```typescript
// frontend/src/hooks/useFlowLogs.ts
import { useState, useEffect, useCallback } from 'react';
import { pollLogs, getRunStatus } from '../services/api';

interface Log {
  timestamp: string;
  level: string;
  message: string;
  task_name?: string;
}

export function useFlowLogs(runId: string | null) {
  const [logs, setLogs] = useState<Log[]>([]);
  const [status, setStatus] = useState<string>('PENDING');
  const [isComplete, setIsComplete] = useState(false);

  const fetchLogs = useCallback(async () => {
    if (!runId) return;

    try {
      // Busca status
      const statusData = await getRunStatus(runId);
      setStatus(statusData.state);

      if (['COMPLETED', 'FAILED', 'CANCELLED'].includes(statusData.state)) {
        setIsComplete(true);
      }

      // Busca novos logs
      const logsData = await pollLogs(runId, logs.length);
      if (logsData.logs.length > 0) {
        setLogs(prev => [...prev, ...logsData.logs]);
      }
    } catch (error) {
      console.error('Error fetching logs:', error);
    }
  }, [runId, logs.length]);

  useEffect(() => {
    if (!runId || isComplete) return;

    // Poll a cada 2 segundos enquanto não terminar
    const interval = setInterval(fetchLogs, 2000);
    fetchLogs(); // Primeira chamada imediata

    return () => clearInterval(interval);
  }, [runId, isComplete, fetchLogs]);

  return { logs, status, isComplete };
}
```

---

## 📅 Fases de Implementação

### FASE 1: Setup Básico (Base)
```
□ Instalar Prefect Server (docker-compose)
□ Criar Gateway FastAPI básico
□ Testar conexão Frontend → Gateway → Prefect
□ Migrar 1 flow simples (britech - mais simples)
```

**Resultado**: Sistema híbrido funcionando com 1 módulo

### FASE 2: Migração dos Flows
```
□ Migrar amplis_flow (CSV + PDF)
□ Migrar maps_flow
□ Migrar fidc_flow
□ Migrar qore_flow
□ Migrar jcot_flow
□ Configurar Selenium Grid
```

**Resultado**: Todos os módulos no Prefect

### FASE 3: Frontend Integration
```
□ Implementar useFlowLogs hook
□ Atualizar página ETL para polling
□ Atualizar página Logs
□ Remover WebSocket do frontend
□ Testes E2E
```

**Resultado**: Frontend integrado com Prefect

### FASE 4: Produção
```
□ Configurar schedules automáticos
□ Setup Selenium Grid para produção
□ Configurar alertas (Slack/Email)
□ Documentação de operação
□ Backup PostgreSQL
```

**Resultado**: Sistema em produção

---

## 🔄 O Que Você MANTÉM vs SUBSTITUI

### ✅ MANTÉM (seu código)
| Componente | Motivo |
|------------|--------|
| Frontend React | Seu diferencial, UI customizada |
| Módulos Python (`amplis_V02.py`, etc) | Core do negócio |
| Criptografia de credenciais | Já funciona bem |
| Autenticação JWT | Pode manter no Gateway |

### 🔄 SUBSTITUI (pelo Prefect)
| Componente Atual | Substituto | Benefício |
|------------------|------------|-----------|
| `worker.py` (polling) | Prefect Agent | Retry automático, observabilidade |
| `executor.py` (subprocess) | Prefect Tasks | Paralelismo, logging estruturado |
| SQLite jobs | PostgreSQL Prefect | Escalável, histórico completo |
| WebSocket logs | API polling | Mais simples, stateless |
| Schedule manual | Prefect Schedules | Cron nativo, timezone |

### ❌ REMOVE (não precisa mais)
| Componente | Por quê |
|------------|---------|
| `backend/services/worker.py` | Prefect Agent faz isso |
| `backend/services/pool.py` | Prefect Agent é melhor |
| `backend/routers/execution.py` | Gateway substitui |
| `backend/core/database.py` (parte jobs) | Prefect DB |

---

## 💰 Custo vs Benefício

### Investimento
| Item | Esforço |
|------|---------|
| Setup Prefect | Baixo (docker-compose) |
| Gateway API | Médio (1 arquivo) |
| Migrar flows | Médio (7 flows) |
| Adaptar frontend | Baixo (polling vs WS) |
| **TOTAL** | **Médio** |

### Ganhos
| Benefício | Valor |
|-----------|-------|
| Retry automático com backoff | Alto |
| UI de monitoramento (Prefect) | Alto |
| Histórico completo de execuções | Alto |
| Logs estruturados e pesquisáveis | Alto |
| Schedules com timezone | Médio |
| Paralelismo nativo | Alto |
| Comunidade e suporte | Alto |
| **Não reinventar a roda** | **Inestimável** |

---

## 🎯 Decisão Final

```
┌─────────────────────────────────────────────────────────────────┐
│                    RECOMENDAÇÃO FINAL                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ✅ Use PREFECT 2.x como orquestrador                         │
│                                                                 │
│   ✅ Mantenha seu frontend React (seu diferencial)             │
│                                                                 │
│   ✅ Crie um Gateway simples para traduzir chamadas            │
│                                                                 │
│   ✅ Migre módulos Python como @task/@flow                     │
│                                                                 │
│   ✅ Use Selenium Grid para escalabilidade dos scrapers        │
│                                                                 │
│   Resultado: Sistema "profissional" com ~40% do esforço        │
│              de construir do zero                               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📚 Próximos Passos

1. **Quer que eu implemente a Fase 1?**
   - Setup docker-compose com Prefect
   - Gateway básico
   - Primeiro flow migrado

2. **Ou prefere explorar Airflow/Dagster?**
   - Posso criar plano similar para eles

3. **Ou quer primeiro testar Prefect localmente?**
   - `pip install prefect`
   - `prefect server start`
   - Testar API manualmente
