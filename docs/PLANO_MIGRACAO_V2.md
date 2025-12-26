# Plano de Migracao Completo para V2

## Visao Geral

**Objetivo:** Migrar do backend Java Spring Boot para FastAPI Python, mantendo o frontend React V2.

**Estimativa Total:** 10-14 dias de trabalho

**Arquitetura Final:**
```
Frontend React (V2/src)
       |
       | REST API + WebSocket
       v
Backend FastAPI (V2/backend)
       |
       | Subprocess
       v
Python ETL Scripts (python/)
```

---

## FASE 1: Completar Backend FastAPI - Endpoints
**Duracao:** 2-3 dias

### 1.1 Criar Router de Sistemas (`V2/backend/routers/sistemas.py`)

```python
# Endpoints a implementar:
GET  /api/sistemas              # Lista todos os sistemas
GET  /api/sistemas/{id}         # Retorna sistema especifico
GET  /api/sistemas/ativos       # Lista apenas sistemas ativos
PATCH /api/sistemas/{id}/toggle # Ativa/desativa sistema
PATCH /api/sistemas/{id}/opcao  # Atualiza opcao do sistema
```

**Tarefas:**
- [ ] Criar arquivo `routers/sistemas.py`
- [ ] Implementar modelo `Sistema` em `models/sistema.py`
- [ ] Implementar `SistemaService` em `services/sistema.py`
- [ ] Persistir estado dos sistemas em `config/sistemas_state.json`
- [ ] Registrar router em `app.py`

### 1.2 Criar Router de Credenciais (`V2/backend/routers/credentials.py`)

```python
# Endpoints a implementar:
GET  /api/credentials     # Retorna credenciais (sem senhas expostas)
POST /api/credentials     # Salva credenciais
```

**Tarefas:**
- [ ] Criar arquivo `routers/credentials.py`
- [ ] Implementar leitura/escrita de `config/credentials.json`
- [ ] Mascarar senhas no GET (retornar apenas estrutura)
- [ ] Validar estrutura no POST

### 1.3 Completar Router de Execucao (`V2/backend/routers/execution.py`)

```python
# Endpoints a completar/criar:
POST /api/execute           # Executar pipeline (COMPLETAR)
POST /api/execute/{id}      # Executar sistema especifico (CRIAR)
POST /api/cancel/{id}       # Cancelar execucao (CRIAR)
GET  /api/jobs              # Listar jobs (CRIAR)
GET  /api/jobs/{id}         # Status do job (JA EXISTE)
```

**Tarefas:**
- [ ] Implementar execucao individual por sistema
- [ ] Implementar cancelamento de job
- [ ] Adicionar endpoint de listagem de jobs
- [ ] Integrar com background worker

### 1.4 Estrutura Final de Arquivos Backend

```
V2/backend/
├── app.py                    # FastAPI app principal
├── database.py               # SQLite conexao
├── models/
│   ├── __init__.py
│   ├── sistema.py            # CRIAR
│   ├── job.py                # CRIAR
│   └── config.py             # CRIAR
├── routers/
│   ├── __init__.py
│   ├── config.py             # EXISTE - melhorar
│   ├── sistemas.py           # CRIAR
│   ├── credentials.py        # CRIAR
│   └── execution.py          # EXISTE - completar
├── services/
│   ├── __init__.py
│   ├── config_service.py     # CRIAR
│   ├── sistema_service.py    # CRIAR
│   ├── execution_service.py  # CRIAR
│   ├── executor.py           # EXISTE - integrar
│   └── state.py              # EXISTE
└── worker.py                 # EXISTE - completar
```

---

## FASE 2: Implementar Worker/Queue de Execucao
**Duracao:** 2 dias

### 2.1 Problema Atual
O endpoint `/api/execute` cria job no banco mas NINGUEM processa.
Jobs ficam em "pending" eternamente.

### 2.2 Solucao: Background Worker com Threading

**Tarefas:**
- [ ] Implementar `BackgroundWorker` que roda em thread separada
- [ ] Poll do banco a cada 2 segundos por jobs "pending"
- [ ] Processar job chamando `ETLExecutor`
- [ ] Atualizar status no banco (running -> success/error)
- [ ] Broadcast de logs via WebSocket

### 2.3 Codigo do Worker (`V2/backend/worker.py`)

```python
# Estrutura a implementar:
class BackgroundWorker:
    def __init__(self, db, websocket_manager):
        self.running = True

    async def start(self):
        while self.running:
            job = self.get_pending_job()
            if job:
                await self.process_job(job)
            await asyncio.sleep(2)

    async def process_job(self, job):
        # 1. Marcar como "running"
        # 2. Chamar ETLExecutor
        # 3. Capturar logs e enviar via WebSocket
        # 4. Marcar como "success" ou "error"
```

### 2.4 Integracao com ETLExecutor

```python
# V2/backend/services/executor.py - completar:
class ETLExecutor:
    async def execute(self, sistemas, opcoes, on_log_callback):
        # Montar comando: python main.py --sistemas X --data-inicial Y
        # Executar subprocess
        # Capturar stdout linha a linha
        # Parsear formato [LEVEL] [SYSTEM] Message
        # Chamar on_log_callback para cada linha
```

---

## FASE 3: Integracao WebSocket Completa
**Duracao:** 1-2 dias

### 3.1 Problema Atual
- Backend tem WebSocket mas so envia logs basicos
- Frontend usa HTTP polling ao inves de WebSocket
- Status updates nao sao enviados

### 3.2 Mensagens WebSocket a Implementar

```typescript
// Log Entry
{
  "type": "log",
  "payload": {
    "job_id": 123,
    "level": "INFO",
    "sistema": "MAPS",
    "mensagem": "Iniciando download...",
    "timestamp": "2025-01-15T10:30:00Z"
  }
}

// Status Update
{
  "type": "status",
  "payload": {
    "job_id": 123,
    "sistema_id": "maps",
    "status": "RUNNING",
    "progresso": 45,
    "mensagem": "Processando arquivo 3/7"
  }
}

// Job Complete
{
  "type": "job_complete",
  "payload": {
    "job_id": 123,
    "status": "SUCCESS",
    "duracao_segundos": 245
  }
}
```

### 3.3 Tarefas Backend

- [ ] Implementar `broadcast_status()` no ConnectionManager
- [ ] Enviar status update quando sistema inicia/termina
- [ ] Enviar progresso estimado baseado em logs
- [ ] Enviar notificacao de job completo

### 3.4 Tarefas Frontend

- [ ] Remover polling HTTP em `LogsPage`
- [ ] Usar `WebSocketService.onLog()` para logs em tempo real
- [ ] Usar `WebSocketService.onStatusUpdate()` para status
- [ ] Atualizar cards de sistema com status em tempo real

---

## FASE 4: Completar Frontend - Forms e Validacao
**Duracao:** 2 dias

### 4.1 Credentials Form (`V2/src/components/settings/credentials-form.tsx`)

**Estado Atual:** Estrutura de tabs existe, mas forms sao stubs

**Tarefas:**
- [ ] Implementar form para cada sistema (AMPLIS, MAPS, FIDC, etc)
- [ ] Campos: URL, username, password (com show/hide)
- [ ] Validacao com Zod schema
- [ ] Feedback de sucesso/erro com Toast
- [ ] Botao de testar conexao (opcional)

### 4.2 Paths Form (`V2/src/components/settings/paths-form.tsx`)

**Tarefas:**
- [ ] Form para configurar caminhos de download
- [ ] Campos: CSV path, PDF path, Excel path
- [ ] Validacao de caminhos validos
- [ ] Botao de browse (se possivel)

### 4.3 Funds Form (`V2/src/components/settings/funds-form.tsx`)

**Tarefas:**
- [ ] Lista de fundos por sistema
- [ ] Checkboxes para ativar/desativar fundos
- [ ] Busca/filtro de fundos
- [ ] Salvar selecao

### 4.4 Validacao Zod

```typescript
// V2/src/lib/validations/credentials.ts
import { z } from "zod";

export const credentialsSchema = z.object({
  amplis: z.object({
    reag: z.object({
      url: z.string().url(),
      username: z.string().min(1),
      password: z.string().min(1),
    }),
    master: z.object({
      url: z.string().url(),
      username: z.string().min(1),
      password: z.string().min(1),
    }),
  }),
  maps: z.object({
    url: z.string().url(),
    username: z.string().min(1),
    password: z.string().min(1),
  }),
  // ... outros sistemas
});
```

---

## FASE 5: Integracao de Dados Reais
**Duracao:** 2 dias

### 5.1 Dashboard com Dados Reais

**Estado Atual:** KPIs e graficos com dados mock

**Tarefas:**
- [ ] Criar endpoint `GET /api/stats` no backend
- [ ] Retornar: execucoes hoje, taxa sucesso, tempo medio, etc
- [ ] Integrar `DashboardPage` com dados reais
- [ ] Implementar grafico de execucoes historicas

### 5.2 Portfolio com Dados Reais

**Estado Atual:** Completamente mock

**Tarefas:**
- [ ] Criar endpoint `GET /api/portfolio` no backend
- [ ] Ler dados de fundos do credentials.json
- [ ] Integrar charts com dados reais
- [ ] Implementar tabela de holdings

### 5.3 Historico de Execucoes

**Tarefas:**
- [ ] Criar endpoint `GET /api/jobs/history`
- [ ] Retornar ultimas N execucoes com status
- [ ] Mostrar no Dashboard em "Recent Activity"
- [ ] Permitir re-executar job anterior

---

## FASE 6: Testes, Polish e Deploy
**Duracao:** 2 dias

### 6.1 Testes

**Tarefas:**
- [ ] Testes unitarios para services do backend
- [ ] Testes de integracao para endpoints
- [ ] Teste E2E: executar pipeline completo
- [ ] Teste de WebSocket connection/reconnection

### 6.2 Polish

**Tarefas:**
- [ ] Loading states em todas as operacoes async
- [ ] Error boundaries em componentes React
- [ ] Mensagens de erro amigaveis
- [ ] Animacoes de transicao
- [ ] Responsividade mobile

### 6.3 Seguranca

**Tarefas:**
- [ ] Remover credentials.json do git history
- [ ] Usar variaveis de ambiente para paths sensiveis
- [ ] Implementar rate limiting
- [ ] Validar todos os inputs

### 6.4 Deploy

**Tarefas:**
- [ ] Script de build de producao
- [ ] Configurar como servico Windows
- [ ] Documentar processo de deploy
- [ ] Criar script de backup de config

---

## Checklist Geral de Arquivos a Criar/Modificar

### Backend (CRIAR)
- [ ] `V2/backend/models/__init__.py`
- [ ] `V2/backend/models/sistema.py`
- [ ] `V2/backend/models/job.py`
- [ ] `V2/backend/models/config.py`
- [ ] `V2/backend/routers/sistemas.py`
- [ ] `V2/backend/routers/credentials.py`
- [ ] `V2/backend/services/config_service.py`
- [ ] `V2/backend/services/sistema_service.py`
- [ ] `V2/backend/services/execution_service.py`

### Backend (MODIFICAR)
- [ ] `V2/backend/app.py` - registrar novos routers
- [ ] `V2/backend/routers/config.py` - limpar logica
- [ ] `V2/backend/routers/execution.py` - completar endpoints
- [ ] `V2/backend/services/executor.py` - integrar com worker
- [ ] `V2/backend/worker.py` - implementar loop de processamento

### Frontend (MODIFICAR)
- [ ] `V2/src/services/api.ts` - adicionar novos endpoints
- [ ] `V2/src/services/websocket.ts` - completar handlers
- [ ] `V2/src/pages/logs/page.tsx` - usar WebSocket
- [ ] `V2/src/pages/dashboard/page.tsx` - dados reais
- [ ] `V2/src/pages/portfolio/page.tsx` - dados reais
- [ ] `V2/src/components/settings/credentials-form.tsx` - completar
- [ ] `V2/src/components/settings/paths-form.tsx` - completar
- [ ] `V2/src/components/settings/funds-form.tsx` - completar

### Frontend (CRIAR)
- [ ] `V2/src/lib/validations/credentials.ts`
- [ ] `V2/src/lib/validations/settings.ts`
- [ ] `V2/src/hooks/useWebSocket.ts`
- [ ] `V2/src/hooks/useJobStatus.ts`

---

## Ordem de Execucao Recomendada

```
Semana 1:
├── Dia 1-2: FASE 1 - Endpoints FastAPI
├── Dia 3-4: FASE 2 - Worker Queue
└── Dia 5: FASE 3 - WebSocket

Semana 2:
├── Dia 1-2: FASE 4 - Frontend Forms
├── Dia 3: FASE 5 - Dados Reais
└── Dia 4-5: FASE 6 - Testes e Deploy
```

---

## Comandos Uteis

```bash
# Rodar backend V2
cd V2/backend
python -m uvicorn app:app --reload --port 4001

# Rodar frontend V2
cd V2
npm run dev

# Testar endpoint
curl http://localhost:4001/api/health

# Testar WebSocket
wscat -c ws://localhost:4001/ws
```

---

## Decisoes Arquiteturais

1. **Banco de Dados:** SQLite (ja implementado) - suficiente para uso local
2. **Queue:** Thread-based worker (simples, sem dependencias extras)
3. **WebSocket:** Nativo FastAPI (sem STOMP, JSON puro)
4. **State Management Frontend:** Zustand (ja configurado)
5. **Forms:** React Hook Form + Zod (ja configurado)

---

## Riscos e Mitigacoes

| Risco | Probabilidade | Impacto | Mitigacao |
|-------|--------------|---------|-----------|
| Worker trava | Media | Alto | Implementar timeout e restart |
| WebSocket desconecta | Alta | Medio | Auto-reconnect ja implementado |
| Credenciais invalidas | Media | Alto | Validar antes de executar |
| Processo Python falha | Media | Alto | Capturar stderr e logar |
| Paths nao existem | Alta | Alto | Validar paths no startup |

---

## Proximos Passos

1. **Escolher por onde comecar:** Recomendo FASE 1 (endpoints)
2. **Criar branch:** `git checkout -b feature/v2-migration`
3. **Implementar incrementalmente:** Um endpoint por vez
4. **Testar frequentemente:** Cada endpoint antes de avancar

Quer que eu comece a implementar alguma fase especifica?
