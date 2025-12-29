# Guia do Desenvolvedor - ETL Dashboard

## Introducao

Este guia e destinado a desenvolvedores que precisam manter, modificar ou estender o ETL Dashboard. Cobre setup de ambiente, arquitetura do codigo, padroes utilizados e boas praticas.

---

## Requisitos de Ambiente

### Software Necessario

| Software | Versao Minima | Verificar |
|----------|---------------|-----------|
| Python | 3.9+ | `python --version` |
| Node.js | 18+ | `node --version` |
| npm | 9+ | `npm --version` |
| Chrome | Ultima | Para Selenium |
| Git | 2.x | `git --version` |

### Extensoes VSCode Recomendadas

```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "dbaeumer.vscode-eslint",
    "esbenp.prettier-vscode",
    "bradlc.vscode-tailwindcss",
    "dsznajder.es7-react-js-snippets"
  ]
}
```

---

## Setup do Ambiente

### 1. Clonar Repositorio

```bash
git clone https://github.com/O-Marcos-Estevam/ETL_DASH.git
cd ETL_DASH
```

### 2. Setup Backend

```bash
cd backend

# Criar ambiente virtual (recomendado)
python -m venv venv

# Ativar ambiente (Windows)
venv\Scripts\activate

# Ativar ambiente (Linux/Mac)
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### 3. Setup Frontend

```bash
cd frontend

# Instalar dependencias
npm install
```

### 4. Configurar Credenciais

```bash
# Copiar template
cp config/credentials.example.json config/credentials.json

# Editar com suas credenciais
notepad config/credentials.json
```

### 5. Iniciar em Desenvolvimento

```bash
# Terminal 1 - Backend
cd backend
python app.py

# Terminal 2 - Frontend
cd frontend
npm run dev
```

---

## Estrutura do Projeto

```
DEV_ETL/
├── backend/                 # API FastAPI
│   ├── app.py              # Entry point
│   ├── config.py           # Configuracoes
│   ├── core/               # Infraestrutura
│   │   ├── database.py     # SQLite operations
│   │   ├── exceptions.py   # Custom exceptions
│   │   └── logging.py      # Logging setup
│   ├── models/             # Pydantic models
│   │   ├── sistema.py      # Sistema, SistemaStatus
│   │   ├── config.py       # ConfiguracaoETL
│   │   └── job.py          # Job, JobStatus
│   ├── routers/            # API endpoints
│   │   ├── config.py       # /api/config
│   │   ├── credentials.py  # /api/credentials
│   │   ├── execution.py    # /api/execute
│   │   └── sistemas.py     # /api/sistemas
│   ├── services/           # Business logic
│   │   ├── credentials.py  # ConfigService
│   │   ├── sistemas.py     # SistemaService
│   │   ├── executor.py     # ETLExecutor
│   │   ├── worker.py       # BackgroundWorker
│   │   └── state.py        # Shared state
│   ├── data/               # SQLite database
│   └── logs/               # Log files
│
├── frontend/               # React + Vite
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── pages/          # Page components
│   │   ├── services/       # API/WebSocket
│   │   ├── hooks/          # Custom hooks
│   │   ├── types/          # TypeScript types
│   │   └── lib/            # Utilities
│   ├── package.json
│   └── vite.config.ts
│
├── python/                 # ETL Scripts
│   ├── main.py            # Orchestrator
│   └── modules/           # Per-system modules
│
├── config/                # Global config
│   └── credentials.json
│
└── docs/                  # Documentation
```

---

## Backend - Detalhes Tecnicos

### Arquitetura

O backend segue uma arquitetura em camadas:

```
┌─────────────────────────────────────┐
│           Routers (API)             │  <- HTTP endpoints
├─────────────────────────────────────┤
│           Services                  │  <- Business logic
├─────────────────────────────────────┤
│           Core                      │  <- Infrastructure
├─────────────────────────────────────┤
│           Models                    │  <- Data structures
└─────────────────────────────────────┘
```

### Adicionar Novo Endpoint

1. **Criar/editar router** em `backend/routers/`:

```python
# backend/routers/novo_router.py
from fastapi import APIRouter

router = APIRouter(prefix="/api/novo", tags=["Novo"])

@router.get("/")
async def listar_itens():
    return {"items": []}

@router.post("/")
async def criar_item(data: dict):
    return {"status": "created"}
```

2. **Registrar em app.py**:

```python
from routers import novo_router

app.include_router(novo_router.router)
```

### Adicionar Novo Modelo

```python
# backend/models/novo_modelo.py
from pydantic import BaseModel
from typing import Optional
from enum import Enum

class NovoStatus(str, Enum):
    ATIVO = "ATIVO"
    INATIVO = "INATIVO"

class NovoModelo(BaseModel):
    id: str
    nome: str
    status: NovoStatus
    descricao: Optional[str] = None

    class Config:
        use_enum_values = True
```

### Adicionar Novo Service

```python
# backend/services/novo_service.py
from typing import Optional

class NovoService:
    _instance: Optional["NovoService"] = None

    def __init__(self):
        self._data = {}

    @classmethod
    def get_instance(cls) -> "NovoService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def get_data(self):
        return self._data

    def set_data(self, key: str, value: any):
        self._data[key] = value

# Singleton accessor
def get_novo_service() -> NovoService:
    return NovoService.get_instance()
```

### Database Operations

```python
# Usando core/database.py
from core.database import get_db_connection

def custom_query():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM jobs WHERE status = ?", ("pending",))
        return cursor.fetchall()
```

### WebSocket Broadcasting

```python
# Enviar mensagem para todos os clientes
from services.state import get_ws_manager

async def broadcast_update(data: dict):
    ws_manager = get_ws_manager()
    if ws_manager:
        await ws_manager.broadcast({
            "type": "custom_event",
            "data": data
        })
```

---

## Frontend - Detalhes Tecnicos

### Criar Novo Componente

```typescript
// frontend/src/components/novo/meu-componente.tsx
import { cn } from "@/lib/utils"

interface MeuComponenteProps {
  titulo: string
  ativo?: boolean
  onClick?: () => void
}

export function MeuComponente({
  titulo,
  ativo = false,
  onClick
}: MeuComponenteProps) {
  return (
    <div
      className={cn(
        "p-4 rounded-lg border",
        ativo ? "border-primary bg-primary/10" : "border-muted"
      )}
      onClick={onClick}
    >
      <h3 className="font-semibold">{titulo}</h3>
    </div>
  )
}

// Exportar em index.ts
// frontend/src/components/novo/index.ts
export * from "./meu-componente"
```

### Criar Nova Pagina

```typescript
// frontend/src/pages/nova/page.tsx
import { useState, useEffect } from "react"
import { Card } from "@/components/ui/card"
import { api } from "@/services/api"

export default function NovaPagina() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await api.getConfig()
        setData(response)
      } catch (error) {
        console.error("Erro:", error)
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [])

  if (loading) return <div>Carregando...</div>

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Nova Pagina</h1>
      <Card className="p-4">
        <pre>{JSON.stringify(data, null, 2)}</pre>
      </Card>
    </div>
  )
}
```

Registrar rota em `App.tsx`:

```typescript
import NovaPagina from "@/pages/nova/page"

// Dentro de Routes
<Route path="/nova" element={<NovaPagina />} />
```

### Adicionar ao Sidebar

```typescript
// frontend/src/components/layout/sidebar.tsx
const menuItems = [
  // ... existentes
  {
    title: "Nova Pagina",
    href: "/nova",
    icon: IconeNovo,
  },
]
```

### Criar Custom Hook

```typescript
// frontend/src/hooks/useCustomHook.ts
import { useState, useEffect, useCallback } from "react"

export function useCustomHook<T>(fetcher: () => Promise<T>) {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  const refetch = useCallback(async () => {
    setLoading(true)
    try {
      const result = await fetcher()
      setData(result)
      setError(null)
    } catch (e) {
      setError(e as Error)
    } finally {
      setLoading(false)
    }
  }, [fetcher])

  useEffect(() => {
    refetch()
  }, [refetch])

  return { data, loading, error, refetch }
}
```

### Adicionar Tipo TypeScript

```typescript
// frontend/src/types/novo.ts
export interface NovoItem {
  id: string
  nome: string
  ativo: boolean
  criadoEm: string
}

export type NovoStatus = "pendente" | "processando" | "concluido" | "erro"

// Exportar em index.ts
export * from "./novo"
```

---

## Python ETL - Detalhes Tecnicos

### Adicionar Novo Sistema

1. **Criar modulo** em `python/modules/`:

```python
# python/modules/novo_sistema.py
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import logging

logger = logging.getLogger(__name__)

def setup_driver(download_path: str) -> webdriver.Chrome:
    """Configura Chrome WebDriver"""
    options = webdriver.ChromeOptions()
    prefs = {
        "download.default_directory": download_path,
        "download.prompt_for_download": False,
    }
    options.add_experimental_option("prefs", prefs)
    return webdriver.Chrome(options=options)

def login(driver: webdriver.Chrome, url: str, user: str, pwd: str):
    """Realiza login no sistema"""
    driver.get(url)

    wait = WebDriverWait(driver, 10)

    # Encontrar campos
    user_field = wait.until(
        EC.presence_of_element_located((By.ID, "username"))
    )
    pwd_field = driver.find_element(By.ID, "password")

    # Preencher e submeter
    user_field.send_keys(user)
    pwd_field.send_keys(pwd)
    driver.find_element(By.ID, "login-btn").click()

    # Aguardar login
    time.sleep(2)
    logger.info("Login realizado com sucesso")

def download_relatorios(driver: webdriver.Chrome, data_inicial: str, data_final: str):
    """Baixa relatorios do sistema"""
    # Implementar logica de download
    pass

def executar(config: dict, data_inicial: str = None, data_final: str = None):
    """Funcao principal de execucao"""
    logger.info("Iniciando novo_sistema...")

    creds = config.get("novo_sistema", {})
    paths = config.get("paths", {})

    driver = setup_driver(paths.get("download", "."))

    try:
        login(
            driver,
            creds.get("url"),
            creds.get("username"),
            creds.get("password")
        )

        download_relatorios(driver, data_inicial, data_final)

        logger.info("novo_sistema concluido com sucesso!")

    except Exception as e:
        logger.error(f"Erro em novo_sistema: {e}")
        raise

    finally:
        driver.quit()
```

2. **Registrar em main.py**:

```python
# python/main.py
from modules import novo_sistema

# Adicionar no dicionario de sistemas
SISTEMAS = {
    # ... existentes
    "novo_sistema": novo_sistema.executar,
}

# Adicionar nos argumentos
parser.add_argument(
    '--sistemas',
    choices=[..., "novo_sistema"],
    ...
)
```

3. **Adicionar metadata no backend**:

```python
# backend/models/sistema.py
SISTEMAS_METADATA = {
    # ... existentes
    "novo_sistema": {
        "id": "novo_sistema",
        "nome": "Novo Sistema",
        "descricao": "Descricao do novo sistema",
        "opcoes": {
            "pdf": True,
            "excel": True,
        }
    }
}
```

4. **Adicionar credenciais template**:

```json
// config/credentials.json
{
  "novo_sistema": {
    "url": "https://novo-sistema.com",
    "username": "",
    "password": ""
  }
}
```

---

## Padroes de Codigo

### Python

```python
# Imports organizados
import os                          # stdlib primeiro
import sys
from pathlib import Path

import pandas as pd                # terceiros depois
from selenium import webdriver

from core.database import get_db   # locais por ultimo

# Docstrings
def funcao(param1: str, param2: int = 10) -> dict:
    """
    Descricao breve da funcao.

    Args:
        param1: Descricao do param1
        param2: Descricao do param2 (default: 10)

    Returns:
        Dicionario com resultados

    Raises:
        ValueError: Se param1 estiver vazio
    """
    pass

# Logging ao inves de print
import logging
logger = logging.getLogger(__name__)

logger.debug("Detalhes tecnicos")
logger.info("Informacao normal")
logger.warning("Aviso importante")
logger.error("Erro ocorreu")
```

### TypeScript/React

```typescript
// Imports organizados
import { useState, useEffect } from "react"      // React primeiro
import { Card } from "@/components/ui/card"       // Componentes UI
import { api } from "@/services/api"              // Services
import { Sistema } from "@/types"                 // Types
import { cn } from "@/lib/utils"                  // Utils

// Interface antes do componente
interface MeuComponenteProps {
  titulo: string
  dados: Sistema[]
  onSelect?: (id: string) => void
}

// Componente funcional com tipos
export function MeuComponente({
  titulo,
  dados,
  onSelect
}: MeuComponenteProps) {
  // Hooks no topo
  const [selected, setSelected] = useState<string | null>(null)

  // Effects depois
  useEffect(() => {
    // ...
  }, [])

  // Handlers
  const handleClick = (id: string) => {
    setSelected(id)
    onSelect?.(id)
  }

  // Render
  return (
    <div className="space-y-4">
      {/* JSX */}
    </div>
  )
}
```

---

## Testes

### Backend (pytest)

```bash
# Instalar dependencias de teste
pip install pytest pytest-asyncio httpx

# Rodar testes
pytest tests/
```

```python
# tests/test_api.py
import pytest
from httpx import AsyncClient
from backend.app import app

@pytest.mark.asyncio
async def test_health():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
```

### Frontend (Vitest)

```bash
# Instalar dependencias
npm install -D vitest @testing-library/react @testing-library/jest-dom

# Rodar testes
npm test
```

```typescript
// src/components/__tests__/button.test.tsx
import { render, screen } from "@testing-library/react"
import { Button } from "../ui/button"

test("renders button with text", () => {
  render(<Button>Click me</Button>)
  expect(screen.getByText("Click me")).toBeInTheDocument()
})
```

---

## Debug

### Backend

```python
# Ativar debug mode
# backend/config.py
DEBUG = True

# Usar debugger
import pdb; pdb.set_trace()

# Ou com breakpoint() (Python 3.7+)
breakpoint()
```

### Frontend

```typescript
// Console
console.log("Debug:", data)

// React DevTools
// Instalar extensao no Chrome

// Debugger statement
debugger;
```

### Selenium

```python
# Screenshot em caso de erro
try:
    # codigo
except Exception as e:
    driver.save_screenshot("error.png")
    raise

# Pausar para inspecionar
import time
time.sleep(300)  # 5 minutos para inspecionar
```

---

## Deploy

### Build de Producao

```bash
# Frontend
cd frontend
npm run build
# Output: frontend/dist/

# Backend nao precisa build (Python interpretado)
```

### Executar em Producao

```bash
# Backend com Uvicorn
cd backend
uvicorn app:app --host 0.0.0.0 --port 4001 --workers 4

# Frontend - servir arquivos estaticos
# Opcao 1: Nginx
# Opcao 2: Servir pelo FastAPI (ver app.py)
```

### Variaveis de Ambiente

```bash
# .env
ETL_HOST=0.0.0.0
ETL_PORT=4001
ETL_DEBUG=false
ETL_LOG_LEVEL=INFO
ETL_CORS_ORIGINS=http://localhost:4000,http://producao.com
```

---

## Troubleshooting Comum

### ImportError no Python

```bash
# Verificar se esta no ambiente virtual
which python

# Reinstalar dependencias
pip install -r requirements.txt --force-reinstall
```

### CORS Error no Frontend

```python
# backend/app.py - verificar origens permitidas
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4000"],  # Adicionar seu dominio
    ...
)
```

### WebSocket nao conecta

```typescript
// Verificar URL
const WS_URL = "ws://localhost:4001/ws"

// Verificar se backend esta rodando
fetch("http://localhost:4001/api/health")
```

### Selenium nao encontra elemento

```python
# Aumentar timeout
wait = WebDriverWait(driver, 30)  # 30 segundos

# Usar diferentes estrategias
By.ID, By.CLASS_NAME, By.CSS_SELECTOR, By.XPATH

# Esperar elemento visivel
EC.visibility_of_element_located((By.ID, "elemento"))
```

---

## Recursos Adicionais

### Documentacao Oficial

- [FastAPI](https://fastapi.tiangolo.com/)
- [React](https://react.dev/)
- [Vite](https://vitejs.dev/)
- [TailwindCSS](https://tailwindcss.com/)
- [shadcn/ui](https://ui.shadcn.com/)
- [Selenium Python](https://selenium-python.readthedocs.io/)

### Ferramentas Uteis

- [Postman](https://www.postman.com/) - Testar APIs
- [React DevTools](https://react.dev/learn/react-developer-tools)
- [Chrome DevTools](https://developer.chrome.com/docs/devtools/)

---

## Contato e Suporte

Para duvidas sobre o codigo:
1. Verificar esta documentacao
2. Consultar docs dos frameworks
3. Abrir issue no repositorio
