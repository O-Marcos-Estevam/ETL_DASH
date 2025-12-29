# Documentacao da API REST

## Visao Geral

A API do ETL Dashboard e construida com FastAPI e fornece endpoints para gerenciamento de sistemas ETL, execucao de pipelines e configuracoes.

**Base URL:** `http://localhost:4001/api`

**Documentacao Interativa:** `http://localhost:4001/docs` (Swagger UI)

---

## Autenticacao

> **AVISO:** Atualmente a API nao possui autenticacao. Todos os endpoints sao publicos.
> Recomenda-se implementar OAuth2/JWT antes de expor em rede.

---

## Endpoints

### Health Check

#### `GET /api/health`

Verifica se o servidor esta funcionando.

**Resposta:**
```json
{
  "status": "ok",
  "timestamp": "2024-01-15T10:30:00.000000"
}
```

---

### Sistemas

#### `GET /api/sistemas`

Lista todos os sistemas ETL disponiveis.

**Resposta:**
```json
{
  "sistemas": [
    {
      "id": "amplis_reag",
      "nome": "AMPLIS REAG",
      "descricao": "AMPLIS conta REAG - Carteira, Cotas e AR",
      "ativo": true,
      "status": "IDLE",
      "opcoes": {
        "csv": true,
        "pdf": true
      },
      "ultima_execucao": null,
      "mensagem": null
    },
    {
      "id": "maps",
      "nome": "MAPS",
      "descricao": "MAPS - Ativos e Passivos",
      "ativo": true,
      "status": "SUCCESS",
      "opcoes": {
        "pdf": true,
        "excel": true
      },
      "ultima_execucao": "2024-01-15T09:00:00",
      "mensagem": "Concluido com sucesso"
    }
    // ... outros sistemas
  ]
}
```

---

#### `GET /api/sistemas/ativos`

Lista apenas os sistemas ativos (habilitados).

**Resposta:** Mesmo formato de `/api/sistemas`, filtrado por `ativo: true`.

---

#### `GET /api/sistemas/{sistema_id}`

Retorna detalhes de um sistema especifico.

**Parametros:**
| Nome | Tipo | Descricao |
|------|------|-----------|
| `sistema_id` | string | ID do sistema (ex: `amplis_reag`, `maps`) |

**Resposta:**
```json
{
  "id": "maps",
  "nome": "MAPS",
  "descricao": "MAPS - Ativos e Passivos",
  "ativo": true,
  "status": "IDLE",
  "opcoes": {
    "pdf": true,
    "excel": true
  },
  "ultima_execucao": "2024-01-15T09:00:00",
  "mensagem": null
}
```

**Erros:**
| Codigo | Descricao |
|--------|-----------|
| 404 | Sistema nao encontrado |

---

#### `PATCH /api/sistemas/{sistema_id}/toggle`

Ativa ou desativa um sistema.

**Parametros:**
| Nome | Tipo | Descricao |
|------|------|-----------|
| `sistema_id` | string | ID do sistema |

**Body:**
```json
{
  "ativo": true
}
```

**Resposta:**
```json
{
  "id": "maps",
  "ativo": true,
  "status": "IDLE"
}
```

---

#### `PATCH /api/sistemas/{sistema_id}/opcao`

Atualiza uma opcao especifica do sistema.

**Parametros:**
| Nome | Tipo | Descricao |
|------|------|-----------|
| `sistema_id` | string | ID do sistema |

**Body:**
```json
{
  "opcao": "pdf",
  "valor": false
}
```

**Resposta:**
```json
{
  "id": "maps",
  "opcao": "pdf",
  "valor": false
}
```

---

### Execucao

#### `POST /api/execute`

Executa pipeline ETL para multiplos sistemas.

**Body:**
```json
{
  "sistemas": ["amplis_reag", "maps", "fidc"],
  "data_inicial": "01/01/2024",
  "data_final": "15/01/2024"
}
```

| Campo | Tipo | Obrigatorio | Descricao |
|-------|------|-------------|-----------|
| `sistemas` | array | Sim | Lista de IDs de sistemas |
| `data_inicial` | string | Nao | Data inicial (DD/MM/YYYY) |
| `data_final` | string | Nao | Data final (DD/MM/YYYY) |

**Resposta (Sucesso):**
```json
{
  "status": "queued",
  "message": "Job adicionado a fila",
  "job_id": 123
}
```

**Resposta (Job ja em execucao):**
```json
{
  "status": "error",
  "message": "Ja existe um job em execucao (ID: 122)",
  "job_id": 122
}
```

---

#### `POST /api/execute/{sistema_id}`

Executa pipeline para um unico sistema.

**Parametros:**
| Nome | Tipo | Descricao |
|------|------|-----------|
| `sistema_id` | string | ID do sistema |

**Body:**
```json
{
  "data_inicial": "01/01/2024",
  "data_final": "15/01/2024"
}
```

**Resposta:** Mesmo formato de `/api/execute`.

---

#### `POST /api/cancel/{job_id}`

Cancela um job em execucao.

**Parametros:**
| Nome | Tipo | Descricao |
|------|------|-----------|
| `job_id` | integer | ID do job |

**Resposta (Sucesso):**
```json
{
  "status": "cancelled",
  "message": "Job 123 cancelado com sucesso"
}
```

**Resposta (Job nao encontrado):**
```json
{
  "status": "error",
  "message": "Job nao encontrado ou nao esta em execucao"
}
```

---

#### `GET /api/jobs`

Lista todos os jobs com paginacao.

**Query Parameters:**
| Nome | Tipo | Default | Descricao |
|------|------|---------|-----------|
| `limit` | integer | 50 | Numero maximo de resultados |
| `offset` | integer | 0 | Pular N primeiros resultados |
| `status` | string | - | Filtrar por status |

**Resposta:**
```json
{
  "jobs": [
    {
      "id": 123,
      "status": "completed",
      "sistemas": ["maps", "fidc"],
      "params": {
        "data_inicial": "01/01/2024",
        "data_final": "15/01/2024"
      },
      "created_at": "2024-01-15T10:00:00",
      "started_at": "2024-01-15T10:00:05",
      "finished_at": "2024-01-15T10:15:30",
      "error": null
    }
  ],
  "total": 1,
  "limit": 50,
  "offset": 0
}
```

---

#### `GET /api/jobs/{job_id}`

Retorna detalhes de um job especifico.

**Parametros:**
| Nome | Tipo | Descricao |
|------|------|-----------|
| `job_id` | integer | ID do job |

**Resposta:**
```json
{
  "id": 123,
  "status": "completed",
  "sistemas": ["maps", "fidc"],
  "params": {
    "data_inicial": "01/01/2024",
    "data_final": "15/01/2024"
  },
  "logs": "[INFO] [MAPS] Iniciando...\n[INFO] [MAPS] Concluido\n",
  "created_at": "2024-01-15T10:00:00",
  "started_at": "2024-01-15T10:00:05",
  "finished_at": "2024-01-15T10:15:30",
  "error": null
}
```

---

### Configuracao

#### `GET /api/config`

Retorna configuracao completa (credenciais mascaradas + sistemas).

**Resposta:**
```json
{
  "amplis": {
    "reag": {
      "username": "usuario",
      "password": "********",
      "url": "https://amplis.example.com"
    },
    "master": {
      "username": "usuario",
      "password": "********",
      "url": "https://amplis.example.com"
    }
  },
  "maps": {
    "username": "usuario",
    "password": "********",
    "url": "https://maps.example.com"
  },
  "paths": {
    "csv": "C:\\dados\\csv",
    "pdf": "C:\\dados\\pdf",
    "maps": "C:\\dados\\maps"
  },
  "sistemas": { /* igual a GET /api/sistemas */ }
}
```

> **Nota:** Senhas sao sempre retornadas como `********` por seguranca.

---

#### `POST /api/config`

Atualiza configuracao.

**Body:**
```json
{
  "amplis": {
    "reag": {
      "username": "novo_usuario",
      "password": "nova_senha",
      "url": "https://amplis.example.com"
    }
  }
}
```

> **Nota:** Campos com `********` ou nao enviados mantem o valor atual.

**Resposta:**
```json
{
  "status": "success",
  "message": "Configuracao salva com sucesso"
}
```

---

#### `GET /api/config/paths`

Retorna apenas os caminhos de arquivos.

**Resposta:**
```json
{
  "paths": {
    "csv": "C:\\dados\\csv",
    "pdf": "C:\\dados\\pdf",
    "maps": "C:\\dados\\maps",
    "fidc": "C:\\dados\\fidc",
    "jcot": "C:\\dados\\jcot",
    "britech": "C:\\dados\\britech",
    "qore_excel": "C:\\dados\\qore",
    "bd_xlsx": "C:\\dados\\bd.xlsx",
    "selenium_temp": "C:\\temp\\selenium"
  }
}
```

---

### Credenciais

#### `GET /api/credentials`

Retorna credenciais (senhas mascaradas).

**Resposta:**
```json
{
  "amplis": {
    "reag": {
      "username": "usuario",
      "password": "********",
      "url": "https://..."
    }
  },
  "maps": { /* ... */ },
  "fidc": { /* ... */ },
  "jcot": { /* ... */ },
  "britech": { /* ... */ },
  "qore": { /* ... */ }
}
```

---

#### `POST /api/credentials`

Salva credenciais.

**Body:**
```json
{
  "amplis": {
    "reag": {
      "username": "usuario",
      "password": "senha_real",
      "url": "https://..."
    }
  }
}
```

**Resposta:**
```json
{
  "status": "success",
  "message": "Credenciais salvas com sucesso"
}
```

---

#### `GET /api/credentials/{system_id}`

Retorna credenciais de um sistema especifico.

**Parametros:**
| Nome | Tipo | Descricao |
|------|------|-----------|
| `system_id` | string | ID do sistema |

**Resposta:**
```json
{
  "username": "usuario",
  "password": "********",
  "url": "https://..."
}
```

---

#### `GET /api/fundos`

Retorna configuracao de fundos por sistema.

**Resposta:**
```json
{
  "maps": {
    "fundos_selecionados": ["Fundo A", "Fundo B"],
    "usar_todos": false
  },
  "fidc": {
    "fundos_selecionados": ["FIDC X", "FIDC Y"],
    "usar_todos": true
  }
}
```

---

## WebSocket

### Conexao

**URL:** `ws://localhost:4001/ws`

### Eventos Recebidos

#### `log`

Logs em tempo real durante execucao.

```json
{
  "type": "log",
  "data": {
    "level": "INFO",
    "sistema": "maps",
    "message": "Download concluido: arquivo.xlsx",
    "timestamp": "2024-01-15T10:30:00"
  }
}
```

| Campo | Tipo | Descricao |
|-------|------|-----------|
| `level` | string | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `sistema` | string | ID do sistema ou `null` |
| `message` | string | Mensagem do log |
| `timestamp` | string | ISO timestamp |

---

#### `status`

Atualizacao de status de um sistema.

```json
{
  "type": "status",
  "data": {
    "sistema_id": "maps",
    "status": "RUNNING",
    "mensagem": "Processando arquivos..."
  }
}
```

| Campo | Tipo | Valores |
|-------|------|---------|
| `status` | string | `IDLE`, `RUNNING`, `SUCCESS`, `ERROR`, `CANCELLED` |

---

#### `job_complete`

Notificacao de job finalizado.

```json
{
  "type": "job_complete",
  "data": {
    "job_id": 123,
    "status": "completed",
    "sistemas": ["maps", "fidc"],
    "duration": 930
  }
}
```

| Campo | Tipo | Descricao |
|-------|------|-----------|
| `status` | string | `completed`, `error`, `cancelled` |
| `duration` | integer | Duracao em segundos |

---

## Codigos de Erro

| Codigo HTTP | Descricao |
|-------------|-----------|
| 200 | Sucesso |
| 400 | Requisicao invalida |
| 404 | Recurso nao encontrado |
| 408 | Timeout |
| 422 | Erro de validacao |
| 500 | Erro interno do servidor |

### Formato de Erro

```json
{
  "detail": "Mensagem de erro descritiva"
}
```

---

## Exemplos de Uso

### cURL

```bash
# Health check
curl http://localhost:4001/api/health

# Listar sistemas
curl http://localhost:4001/api/sistemas

# Executar pipeline
curl -X POST http://localhost:4001/api/execute \
  -H "Content-Type: application/json" \
  -d '{"sistemas": ["maps", "fidc"], "data_final": "15/01/2024"}'

# Cancelar job
curl -X POST http://localhost:4001/api/cancel/123

# Obter configuracao
curl http://localhost:4001/api/config
```

### JavaScript/Fetch

```javascript
// Executar pipeline
const response = await fetch('http://localhost:4001/api/execute', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    sistemas: ['maps', 'fidc'],
    data_inicial: '01/01/2024',
    data_final: '15/01/2024'
  })
});
const result = await response.json();
console.log(result.job_id);

// WebSocket
const ws = new WebSocket('ws://localhost:4001/ws');
ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  if (msg.type === 'log') {
    console.log(`[${msg.data.level}] ${msg.data.message}`);
  }
};
```

### Python

```python
import requests

# Executar pipeline
response = requests.post(
    'http://localhost:4001/api/execute',
    json={
        'sistemas': ['maps', 'fidc'],
        'data_inicial': '01/01/2024',
        'data_final': '15/01/2024'
    }
)
job_id = response.json()['job_id']
print(f'Job iniciado: {job_id}')

# Verificar status
job = requests.get(f'http://localhost:4001/api/jobs/{job_id}').json()
print(f'Status: {job["status"]}')
```

---

## Rate Limits

Atualmente nao ha rate limiting implementado. Para producao, recomenda-se:

- 100 requisicoes/minuto por IP
- 10 execucoes simultaneas maximo
- Timeout de 1 hora para jobs

---

## Versionamento

A API atual nao possui versionamento. Versoes futuras usarao prefixo:

- `/api/v1/...` - Versao atual
- `/api/v2/...` - Versao futura

---

## Swagger/OpenAPI

Documentacao interativa disponivel em:

- **Swagger UI:** http://localhost:4001/docs
- **ReDoc:** http://localhost:4001/redoc
- **OpenAPI JSON:** http://localhost:4001/openapi.json
