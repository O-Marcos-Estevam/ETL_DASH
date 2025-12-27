# ETL Dashboard V2

Dashboard moderno para gerenciamento de pipelines ETL.

## Stack Tecnologica

- **Backend**: Python FastAPI + SQLite
- **Frontend**: React + TypeScript + Vite + shadcn/ui
- **WebSocket**: Comunicacao em tempo real para logs

## Estrutura

```
V2/
├── backend/           # FastAPI Backend
│   ├── app.py         # Aplicacao principal
│   ├── database.py    # SQLite para jobs
│   ├── routers/       # Endpoints API
│   ├── services/      # Logica de negocio
│   └── models/        # Modelos Pydantic
├── src/               # Frontend React
│   ├── pages/         # Paginas (ETL, Logs, Settings)
│   ├── components/    # Componentes UI
│   └── services/      # API e WebSocket
├── scripts/           # Scripts de inicializacao
└── INICIAR_V2.bat     # Launcher principal
```

## Como Iniciar

### Opcao 1: Launcher Automatico
```batch
V2\INICIAR_V2.bat
```

### Opcao 2: Manual

**Terminal 1 - Backend:**
```batch
cd V2\backend
python app.py
```

**Terminal 2 - Frontend:**
```batch
cd V2
npm run dev
```

## URLs

- Frontend: http://localhost:4000
- Backend API: http://localhost:4001
- API Docs (Swagger): http://localhost:4001/docs
- WebSocket: ws://localhost:4001/ws

## Endpoints API

| Metodo | Endpoint | Descricao |
|--------|----------|-----------|
| GET | /api/health | Health check |
| GET | /api/sistemas | Lista sistemas |
| GET | /api/config | Configuracao atual |
| POST | /api/execute | Executar pipeline |
| POST | /api/cancel/{id} | Cancelar job |
| GET | /api/jobs | Listar jobs |
| GET | /api/credentials | Credenciais (mascaradas) |
| POST | /api/credentials | Salvar credenciais |

## WebSocket

Conecte em `ws://localhost:4001/ws` para receber:

- `log`: Logs em tempo real
- `status`: Atualizacao de status dos sistemas
- `job_complete`: Notificacao de job finalizado

## Configuracao

Credenciais em: `config/credentials.json`

Estrutura:
- `maps`, `fidc`, `jcot`, `britech`, `qore`: Credenciais por sistema
- `amplis.reag`, `amplis.master`: Credenciais AMPLIS
- `paths`: Diretorios de arquivos
- `[sistema].fundos`: Lista de fundos disponiveis
- `[sistema].usar_todos`: Se true, processa todos os fundos
- `[sistema].fundos_selecionados`: Fundos selecionados manualmente

## Variaveis de Ambiente

Copie `.env.example` para `.env` e configure:

```env
# Backend
ETL_HOST=0.0.0.0
ETL_PORT=4001
ETL_DEBUG=false              # true para reload automatico
ETL_LOG_LEVEL=INFO
ETL_CORS_ORIGINS=http://localhost:4000

# Frontend (Vite)
VITE_API_URL=http://localhost:4001/api
VITE_WS_URL=ws://localhost:4001
```

## Desenvolvimento

```bash
# Instalar dependencias frontend
cd V2
npm install

# Verificar tipos TypeScript
npm run typecheck

# Build producao
npm run build
```

## Arquitetura

```
V2/
├── backend/
│   ├── app.py              # Entry point FastAPI
│   ├── config.py           # Configuracoes centralizadas
│   ├── database.py         # SQLite
│   ├── core/               # Utilities (exceptions, logging)
│   ├── routers/            # Endpoints API
│   ├── services/           # Logica de negocio
│   └── models/             # Pydantic models
├── src/
│   ├── pages/              # Paginas React
│   ├── components/         # UI Components
│   ├── hooks/              # Custom hooks
│   ├── services/           # API/WebSocket
│   ├── lib/                # Utilities + constants
│   └── types/              # TypeScript types
├── scripts/                # Scripts de inicializacao
└── .env.example            # Template de configuracao
```

## Seguranca

- CORS restrito a origens configuradas (nao usa `["*"]`)
- Reload desabilitado em producao (ETL_DEBUG=false)
- Senhas mascaradas na API
- Credenciais em arquivo separado (nao versionado)
