# ETL Dashboard

Sistema de gerenciamento e execução de pipelines ETL.

## Stack

- **Backend:** Python FastAPI + SQLite
- **Frontend:** React + TypeScript + Vite + shadcn/ui
- **WebSocket:** Comunicação em tempo real

## Estrutura

```
DEV_ETL/
├── backend/           # API FastAPI
│   ├── app.py         # Entry point
│   ├── config.py      # Configurações
│   ├── core/          # Database, exceptions, logging
│   ├── models/        # Pydantic models
│   ├── routers/       # Endpoints API
│   └── services/      # Lógica de negócio
│
├── frontend/          # React App
│   ├── src/           # Código fonte
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── pages/
│   │   └── services/
│   ├── package.json
│   └── vite.config.ts
│
├── config/            # Configurações globais
├── docs/              # Documentação
├── tools/             # Runtimes (java, maven, node)
├── python/            # Scripts ETL
├── scripts/           # Scripts auxiliares
│
└── INICIAR.bat        # Launcher
```

## Como Iniciar

### Opção 1: Launcher
```batch
INICIAR.bat
```

### Opção 2: Manual
```batch
# Terminal 1 - Backend
cd backend
python app.py

# Terminal 2 - Frontend
cd frontend
npm run dev
```

## URLs

| Serviço | URL |
|---------|-----|
| Frontend | http://localhost:4000 |
| Backend API | http://localhost:4001 |
| API Docs | http://localhost:4001/docs |
| WebSocket | ws://localhost:4001/ws |

## Endpoints API

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | /api/health | Health check |
| GET | /api/sistemas | Lista sistemas |
| GET | /api/config | Configuração atual |
| POST | /api/execute | Executar pipeline |
| POST | /api/cancel/{id} | Cancelar job |
| GET | /api/jobs | Listar jobs |
| GET | /api/credentials | Credenciais |
| POST | /api/credentials | Salvar credenciais |

## WebSocket

Conecte em `ws://localhost:4001/ws` para receber:
- `log`: Logs em tempo real
- `status`: Status dos sistemas
- `job_complete`: Notificação de conclusão

## Desenvolvimento

```bash
# Frontend
cd frontend
npm install
npm run dev

# Build produção
npm run build
```

## Configuração

Credenciais em: `config/credentials.json`

Variáveis de ambiente (`.env`):
```env
ETL_HOST=0.0.0.0
ETL_PORT=4001
ETL_DEBUG=false
VITE_API_URL=http://localhost:4001/api
VITE_WS_URL=ws://localhost:4001
```
