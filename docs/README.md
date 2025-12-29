# ETL Dashboard

Sistema de gerenciamento e execucao de pipelines ETL para automacao de coleta de dados de plataformas financeiras.

## Stack

- **Backend:** Python FastAPI + SQLite
- **Frontend:** React 19 + TypeScript + Vite + shadcn/ui
- **WebSocket:** Comunicacao em tempo real
- **Automacao:** Selenium WebDriver

## Documentacao

| Documento | Descricao | Publico |
|-----------|-----------|---------|
| [Guia do Usuario](docs/GUIA_USUARIO.md) | Como usar o sistema | Usuarios finais |
| [Arquitetura](docs/ARCHITECTURE.md) | Visao tecnica do sistema | Desenvolvedores |
| [API](docs/API.md) | Documentacao dos endpoints | Desenvolvedores |
| [Frontend](docs/FRONTEND.md) | Estrutura React/TypeScript | Desenvolvedores |
| [Desenvolvedor](docs/DEVELOPER.md) | Guia de contribuicao | Desenvolvedores |
| [Analise Critica](docs/ANALISE_CRITICA.md) | Problemas e recomendacoes | Tech Leads |

## Estrutura

```
DEV_ETL/
├── backend/           # API FastAPI
│   ├── app.py         # Entry point
│   ├── config.py      # Configuracoes
│   ├── core/          # Database, exceptions, logging
│   ├── models/        # Pydantic models
│   ├── routers/       # Endpoints API
│   └── services/      # Logica de negocio
│
├── frontend/          # React App
│   ├── src/           # Codigo fonte
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── pages/
│   │   └── services/
│   ├── package.json
│   └── vite.config.ts
│
├── python/            # Scripts ETL
│   ├── main.py        # Orquestrador
│   └── modules/       # Modulos por sistema
│
├── config/            # Configuracoes globais
├── docs/              # Documentacao completa
├── tools/             # Runtimes (java, maven, node)
├── scripts/           # Scripts auxiliares
│
├── INICIAR.bat        # Launcher principal
└── README.md          # Este arquivo
```

## Como Iniciar

### Opcao 1: Launcher (Recomendado)
```batch
INICIAR.bat
```

### Opcao 2: Manual
```batch
# Terminal 1 - Backend
cd backend
python app.py

# Terminal 2 - Frontend
cd frontend
npm run dev
```

## URLs

| Servico | URL |
|---------|-----|
| Frontend | http://localhost:4000 |
| Backend API | http://localhost:4001 |
| API Docs (Swagger) | http://localhost:4001/docs |
| WebSocket | ws://localhost:4001/ws |

## Sistemas ETL Suportados

| Sistema | Descricao | Formatos |
|---------|-----------|----------|
| AMPLIS REAG | Carteiras, cotas, aplicacoes | CSV, PDF |
| AMPLIS Master | Carteiras, cotas, aplicacoes | CSV, PDF |
| MAPS | Ativos, passivos, rentabilidade | XLSX, PDF |
| FIDC | Relatorios de estoque | CSV |
| JCOT | Posicoes de cotistas | XLSX |
| Britech | Dados financeiros | XLSX |
| QORE | Carteiras | PDF, XLSX |
| Trustee | Script externo | BAT |

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

Documentacao completa: [docs/API.md](docs/API.md)

## WebSocket

Conecte em `ws://localhost:4001/ws` para receber:
- `log`: Logs em tempo real
- `status`: Status dos sistemas
- `job_complete`: Notificacao de conclusao

## Desenvolvimento

### Requisitos
- Python 3.9+
- Node.js 18+
- Chrome (para Selenium)

### Setup
```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend
cd frontend
npm install
```

### Build Producao
```bash
cd frontend
npm run build
```

Guia completo: [docs/DEVELOPER.md](docs/DEVELOPER.md)

## Configuracao

Credenciais em: `config/credentials.json`

Variaveis de ambiente (`.env`):
```env
ETL_HOST=0.0.0.0
ETL_PORT=4001
ETL_DEBUG=false
VITE_API_URL=http://localhost:4001/api
VITE_WS_URL=ws://localhost:4001
```

## Avisos de Seguranca

> **IMPORTANTE:** Este sistema atualmente nao possui autenticacao.
> Nao expor em redes publicas sem implementar seguranca adequada.
> Consulte [docs/ANALISE_CRITICA.md](docs/ANALISE_CRITICA.md) para detalhes.

## Licenca

Uso interno - BLOKO/REAG
