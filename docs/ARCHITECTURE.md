# Arquitetura do Sistema ETL Dashboard

## Visao Geral

O ETL Dashboard e um sistema completo de gerenciamento e execucao de pipelines ETL (Extract, Transform, Load) para automacao de coleta de dados de plataformas financeiras.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ETL DASHBOARD - ARQUITETURA                        │
└─────────────────────────────────────────────────────────────────────────────┘

                              ┌─────────────┐
                              │   Usuario   │
                              │  (Browser)  │
                              └──────┬──────┘
                                     │
                    ┌────────────────┴────────────────┐
                    │                                  │
                    ▼                                  ▼
           ┌───────────────┐                  ┌───────────────┐
           │   Frontend    │                  │   WebSocket   │
           │  React/Vite   │                  │  (Real-time)  │
           │  :4000        │                  │               │
           └───────┬───────┘                  └───────┬───────┘
                   │                                  │
                   │  HTTP REST                       │ WS
                   │                                  │
                   └────────────────┬─────────────────┘
                                    │
                                    ▼
                           ┌───────────────┐
                           │   Backend     │
                           │   FastAPI     │
                           │   :4001       │
                           └───────┬───────┘
                                   │
                   ┌───────────────┼───────────────┐
                   │               │               │
                   ▼               ▼               ▼
          ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
          │   SQLite    │ │  Config     │ │  Python     │
          │  (Jobs DB)  │ │   JSON      │ │  Scripts    │
          └─────────────┘ └─────────────┘ └──────┬──────┘
                                                 │
                                                 ▼
                                    ┌─────────────────────┐
                                    │  Plataformas ETL    │
                                    │  (AMPLIS, MAPS,     │
                                    │   FIDC, QORE, etc)  │
                                    └─────────────────────┘
```

---

## Stack Tecnologico

### Backend (Python)
| Componente | Tecnologia | Versao | Proposito |
|------------|------------|--------|-----------|
| Framework Web | FastAPI | 0.110.0 | API REST assincrona |
| Servidor ASGI | Uvicorn | 0.27.1 | Servidor HTTP/WebSocket |
| Validacao | Pydantic | 2.6.3 | Modelos de dados |
| Banco de Dados | SQLite | Built-in | Fila de jobs |
| WebSocket | websockets | 12.0 | Comunicacao real-time |

### Frontend (TypeScript)
| Componente | Tecnologia | Versao | Proposito |
|------------|------------|--------|-----------|
| Framework | React | 19.2.0 | Interface de usuario |
| Bundler | Vite | 5.4.x | Build e dev server |
| Linguagem | TypeScript | 5.6.x | Type safety |
| Estilizacao | TailwindCSS | 3.4.x | CSS utilitario |
| Componentes | shadcn/ui | - | UI primitives |
| Graficos | Recharts | 3.6.x | Visualizacao de dados |
| Roteamento | React Router | 7.11.x | SPA routing |

### Scripts ETL (Python)
| Componente | Tecnologia | Proposito |
|------------|------------|-----------|
| Automacao Web | Selenium | Browser automation |
| Processamento | Pandas | Manipulacao de dados |
| Excel | OpenPyXL | Leitura/escrita Excel |
| PDF | PyMuPDF | Extracao de texto PDF |
| Banco Access | pyodbc | Conexao ODBC |

---

## Camadas da Arquitetura

### 1. Camada de Apresentacao (Frontend)

```
frontend/src/
├── pages/              # Paginas principais (5)
│   ├── dashboard/      # Metricas e KPIs
│   ├── etl/            # Execucao de pipelines
│   ├── logs/           # Visualizacao de logs
│   ├── portfolio/      # Graficos de portfolio
│   └── settings/       # Configuracoes
│
├── components/         # Componentes React
│   ├── ui/             # Primitivos (Button, Card, etc)
│   ├── layout/         # AppLayout, Sidebar, Header
│   ├── dashboard/      # KpiCard, Charts
│   ├── etl/            # SystemCard, Controls
│   ├── logs/           # LogViewer, LogFilter
│   └── settings/       # Forms de configuracao
│
├── services/           # Comunicacao com backend
│   ├── api.ts          # Chamadas HTTP REST
│   └── websocket.ts    # Cliente WebSocket
│
├── hooks/              # Custom React hooks
├── types/              # Definicoes TypeScript
└── lib/                # Utilitarios
```

**Responsabilidades:**
- Renderizacao da interface do usuario
- Gerenciamento de estado local
- Comunicacao com API REST
- Atualizacoes em tempo real via WebSocket

---

### 2. Camada de API (Backend)

```
backend/
├── app.py              # Entry point FastAPI
├── config.py           # Configuracoes centralizadas
│
├── routers/            # Endpoints da API
│   ├── config.py       # GET/POST /api/config
│   ├── credentials.py  # GET/POST /api/credentials
│   ├── execution.py    # POST /api/execute, /api/cancel
│   └── sistemas.py     # GET/PATCH /api/sistemas
│
├── services/           # Logica de negocio
│   ├── credentials.py  # Gerenciamento de credenciais
│   ├── sistemas.py     # Estado dos sistemas
│   ├── executor.py     # Execucao de subprocessos
│   ├── worker.py       # Processamento de fila
│   └── state.py        # Estado compartilhado
│
├── models/             # Modelos Pydantic
│   ├── sistema.py      # Sistema, SistemaStatus
│   ├── config.py       # ConfiguracaoETL, Periodo
│   └── job.py          # Job, JobStatus, JobParams
│
└── core/               # Infraestrutura
    ├── database.py     # Operacoes SQLite
    ├── exceptions.py   # Hierarquia de excecoes
    └── logging.py      # Configuracao de logs
```

**Responsabilidades:**
- Exposicao de endpoints REST
- Validacao de requisicoes
- Gerenciamento de jobs
- Comunicacao WebSocket
- Execucao de scripts Python

---

### 3. Camada de Execucao (Python ETL)

```
python/
├── main.py             # Orquestrador principal
│
└── modules/            # Modulos por sistema
    ├── amplis_V02.py           # AMPLIS (REAG/Master)
    ├── amplis_functions.py     # Funcoes auxiliares
    ├── FIDC_ESTOQUE_V02.py     # FIDC
    ├── Jcot_V02.py             # JCOT
    ├── query_britech_V02.py    # Britech
    ├── automacao_qore_v5.py    # QORE
    ├── maps_downloads.py       # MAPS download
    ├── maps_consolidado.py     # MAPS consolidado
    ├── maps_save_excel_folders.py  # MAPS Excel
    ├── maps_upload_access.py   # Upload Access
    └── save_pdfs.py            # Organizacao PDFs
```

**Responsabilidades:**
- Automacao de navegadores (Selenium)
- Extracao de dados de plataformas
- Transformacao de arquivos
- Carga em banco de dados Access

---

## Fluxo de Dados

### Fluxo de Execucao de Job

```
┌───────────────────────────────────────────────────────────────────────────┐
│                         FLUXO DE EXECUCAO DE JOB                          │
└───────────────────────────────────────────────────────────────────────────┘

  Frontend              Backend                SQLite              Python
     │                     │                      │                   │
     │ POST /api/execute   │                      │                   │
     │────────────────────>│                      │                   │
     │                     │                      │                   │
     │                     │  INSERT job          │                   │
     │                     │     (pending)        │                   │
     │                     │─────────────────────>│                   │
     │                     │                      │                   │
     │   {job_id, status}  │                      │                   │
     │<────────────────────│                      │                   │
     │                     │                      │                   │
     │                     │                      │                   │
     │                     │    BackgroundWorker polls               │
     │                     │         (2s interval)                    │
     │                     │                      │                   │
     │                     │  SELECT pending      │                   │
     │                     │<─────────────────────│                   │
     │                     │                      │                   │
     │                     │  UPDATE running      │                   │
     │                     │─────────────────────>│                   │
     │                     │                      │                   │
     │                     │  ETLExecutor.execute()                   │
     │                     │──────────────────────────────────────────>
     │                     │                      │                   │
     │                     │                      │  subprocess       │
     │                     │                      │  python main.py   │
     │                     │                      │                   │
     │   WS: log           │                      │  stdout/stderr    │
     │<════════════════════════════════════════════════════════════════
     │                     │                      │                   │
     │   WS: log           │                      │       ...         │
     │<════════════════════════════════════════════════════════════════
     │                     │                      │                   │
     │                     │                      │  exit code        │
     │                     │<──────────────────────────────────────────
     │                     │                      │                   │
     │                     │  UPDATE completed    │                   │
     │                     │─────────────────────>│                   │
     │                     │                      │                   │
     │  WS: job_complete   │                      │                   │
     │<════════════════════│                      │                   │
```

### Fluxo de Configuracao

```
┌───────────────────────────────────────────────────────────────────────────┐
│                         FLUXO DE CONFIGURACAO                             │
└───────────────────────────────────────────────────────────────────────────┘

  Settings Page          API                ConfigService           Files
       │                  │                      │                    │
       │ GET /api/config  │                      │                    │
       │─────────────────>│                      │                    │
       │                  │  get_credentials()   │                    │
       │                  │─────────────────────>│                    │
       │                  │                      │ read credentials   │
       │                  │                      │   .json            │
       │                  │                      │───────────────────>│
       │                  │                      │      data          │
       │                  │                      │<───────────────────│
       │                  │    credentials       │                    │
       │                  │    (masked)          │                    │
       │                  │<─────────────────────│                    │
       │                  │                      │                    │
       │  config + sistemas (merged)             │                    │
       │<─────────────────│                      │                    │
       │                  │                      │                    │
       │                  │                      │                    │
       │ POST /api/credentials                   │                    │
       │─────────────────>│                      │                    │
       │                  │  save_credentials()  │                    │
       │                  │─────────────────────>│                    │
       │                  │                      │ merge & write      │
       │                  │                      │───────────────────>│
       │                  │      success         │                    │
       │                  │<─────────────────────│                    │
       │      {success}   │                      │                    │
       │<─────────────────│                      │                    │
```

---

## Sistemas ETL Suportados

| Sistema | Plataforma | Tipo de Dado | Formatos |
|---------|------------|--------------|----------|
| **AMPLIS REAG** | AMPLIS | Carteira, Cotas, Aplicacoes | CSV, PDF |
| **AMPLIS Master** | AMPLIS | Carteira, Cotas, Aplicacoes | CSV, PDF |
| **MAPS** | MAPS Cloud | Ativos, Passivos, Rentabilidade | XLSX, PDF |
| **FIDC** | FIDC Portal | Estoque | CSV |
| **JCOT** | JCOT | Posicoes Cotistas | XLSX |
| **Britech** | Britech | Dados Financeiros | XLSX |
| **QORE** | QORE Dashboard | Carteiras | PDF, XLSX |
| **Trustee** | Script Externo | - | BAT |

---

## Modelo de Dados

### Job (Fila de Execucao)

```sql
CREATE TABLE jobs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    status      TEXT NOT NULL,           -- pending, running, completed, error, cancelled
    sistemas    TEXT NOT NULL,           -- JSON array de sistemas
    params      TEXT,                    -- JSON com parametros
    logs        TEXT,                    -- Logs acumulados
    created_at  TEXT NOT NULL,           -- ISO timestamp
    started_at  TEXT,                    -- ISO timestamp
    finished_at TEXT,                    -- ISO timestamp
    error       TEXT                     -- Mensagem de erro
);
```

### Sistema (Estado em Memoria)

```python
class Sistema:
    id: str              # Ex: "amplis_reag"
    nome: str            # Ex: "AMPLIS REAG"
    descricao: str       # Descricao do sistema
    ativo: bool          # Se esta habilitado
    status: SistemaStatus  # IDLE, RUNNING, SUCCESS, ERROR
    opcoes: {            # Opcoes por sistema
        csv: bool,
        pdf: bool,
        excel: bool,
        base_total: bool
    }
    ultima_execucao: str # ISO timestamp
    mensagem: str        # Ultima mensagem
```

### Credenciais (JSON)

```json
{
  "amplis": {
    "reag": { "username": "", "password": "", "url": "" },
    "master": { "username": "", "password": "", "url": "" }
  },
  "maps": { "url": "", "username": "", "password": "" },
  "fidc": { "url": "", "username": "", "password": "" },
  "jcot": { "url": "", "username": "", "password": "" },
  "britech": { "url": "", "username": "", "password": "" },
  "qore": { "url": "", "username": "", "password": "" },
  "paths": {
    "csv": "caminho/para/csv",
    "pdf": "caminho/para/pdf",
    "maps": "caminho/para/maps",
    ...
  }
}
```

---

## Comunicacao WebSocket

### Tipos de Mensagens

| Tipo | Direcao | Descricao |
|------|---------|-----------|
| `log` | Server -> Client | Log em tempo real |
| `status` | Server -> Client | Atualizacao de status do sistema |
| `job_complete` | Server -> Client | Notificacao de job finalizado |

### Formato das Mensagens

```json
// log
{
  "type": "log",
  "data": {
    "level": "INFO",
    "sistema": "maps",
    "message": "Iniciando download...",
    "timestamp": "2024-01-15T10:30:00"
  }
}

// status
{
  "type": "status",
  "data": {
    "sistema_id": "maps",
    "status": "RUNNING",
    "mensagem": "Processando..."
  }
}

// job_complete
{
  "type": "job_complete",
  "data": {
    "job_id": 123,
    "status": "completed",
    "sistemas": ["maps", "fidc"]
  }
}
```

---

## Seguranca

### Problemas Identificados

| Severidade | Problema | Localizacao |
|------------|----------|-------------|
| **ALTA** | Sem autenticacao na API | Todos os endpoints |
| **ALTA** | Credenciais em texto plano | credentials.json |
| **ALTA** | Credenciais hardcoded | maps_consolidado.py |
| **MEDIA** | CORS permissivo | app.py |
| **MEDIA** | Logs podem expor dados | executor.py |

### Recomendacoes

1. **Implementar autenticacao** (OAuth2/JWT)
2. **Criptografar credenciais** em repouso
3. **Remover credenciais hardcoded** do codigo
4. **Restringir CORS** para origens especificas
5. **Sanitizar logs** antes de exibicao

---

## Escalabilidade

### Limitacoes Atuais

- SQLite: Single-writer (nao suporta alta concorrencia)
- Worker: Um job por vez (fila sequencial)
- WebSocket: Conexoes em memoria (nao distribuido)

### Evolucao Possivel

1. **Banco de Dados**: Migrar para PostgreSQL
2. **Fila**: Usar Redis/RabbitMQ para jobs distribuidos
3. **Worker**: Implementar workers paralelos (Celery)
4. **WebSocket**: Usar Redis PubSub para escalar

---

## Dependencias Externas

### Servicos Obrigatorios
- Chrome/Chromium (para Selenium)
- Python 3.x com pip
- Node.js 18+ com npm

### Servicos Opcionais
- Microsoft Access (para upload de dados)
- Conexao ODBC configurada

---

## Estrutura de Pastas Final

```
DEV_ETL/
├── backend/            # API FastAPI
│   ├── app.py
│   ├── config.py
│   ├── core/
│   ├── data/           # SQLite database
│   ├── logs/           # Log files
│   ├── models/
│   ├── routers/
│   └── services/
│
├── frontend/           # React App
│   ├── src/
│   ├── dist/           # Build de producao
│   ├── package.json
│   └── vite.config.ts
│
├── python/             # Scripts ETL
│   ├── main.py
│   └── modules/
│
├── config/             # Configuracoes globais
│   └── credentials.json
│
├── docs/               # Documentacao
├── tools/              # Runtimes (java, maven, node)
├── scripts/            # Scripts auxiliares
│
├── INICIAR.bat         # Launcher principal
├── README.md
└── .gitignore
```

---

## Proximos Passos Recomendados

1. **Curto Prazo**
   - Implementar autenticacao basica
   - Adicionar testes unitarios
   - Remover credenciais hardcoded

2. **Medio Prazo**
   - Migrar estado para TanStack Query (frontend)
   - Implementar retry com backoff exponencial
   - Adicionar health checks detalhados

3. **Longo Prazo**
   - Containerizar com Docker
   - Implementar CI/CD
   - Dashboard de metricas (Prometheus/Grafana)
