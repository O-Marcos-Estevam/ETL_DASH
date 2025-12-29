# Plano de Melhorias Arquiteturais

## Visao Geral

Este documento detalha as melhorias recomendadas para o ETL Dashboard, organizadas por prioridade e area.

---

## 1. Backend - Autenticacao (Prioridade CRITICA)

### Situacao Atual
API totalmente aberta, sem nenhuma protecao.

### Solucao: JWT Authentication

**Criar novo arquivo:** `backend/core/auth.py`

```python
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
import os

# Configuracoes
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "sua-chave-secreta-mude-em-producao")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8 horas

# Contexto de criptografia
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class User(BaseModel):
    username: str
    disabled: bool = False


class UserInDB(User):
    hashed_password: str


# Banco de usuarios simples (migrar para DB depois)
USERS_DB = {
    "admin": {
        "username": "admin",
        "hashed_password": pwd_context.hash("admin123"),  # MUDAR!
        "disabled": False,
    }
}


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_user(username: str) -> Optional[UserInDB]:
    if username in USERS_DB:
        user_dict = USERS_DB[username]
        return UserInDB(**user_dict)
    return None


def authenticate_user(username: str, password: str) -> Optional[UserInDB]:
    user = get_user(username)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais invalidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = get_user(username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Usuario inativo")
    return current_user
```

**Criar router:** `backend/routers/auth.py`

```python
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from core.auth import (
    Token,
    authenticate_user,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)

router = APIRouter(prefix="/api/auth", tags=["Autenticacao"])


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return {"access_token": access_token, "token_type": "bearer"}
```

**Proteger rotas em:** `backend/routers/credentials.py`

```python
from core.auth import get_current_active_user, User

@router.get("/")
async def get_credentials(current_user: User = Depends(get_current_active_user)):
    # Agora protegido!
    return config_service.get_credentials()
```

**Adicionar dependencias:** `backend/requirements.txt`

```
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
```

---

## 2. Backend - Dependency Injection (Prioridade ALTA)

### Situacao Atual
Singletons manuais com funcoes `get_*_service()`.

### Solucao: FastAPI Depends

**Refatorar:** `backend/services/credentials.py`

```python
from functools import lru_cache
from pathlib import Path
import json


class ConfigService:
    def __init__(self, config_path: Path):
        self.config_path = config_path
        self._cache = None

    def get_credentials(self) -> dict:
        if self._cache is None:
            self._load()
        return self._mask_passwords(self._cache)

    def _load(self):
        if self.config_path.exists():
            with open(self.config_path) as f:
                self._cache = json.load(f)
        else:
            self._cache = {}

    def _mask_passwords(self, data: dict) -> dict:
        # ... implementacao
        pass


@lru_cache()
def get_config_service() -> ConfigService:
    from config import settings
    return ConfigService(settings.CONFIG_DIR / "credentials.json")
```

**Usar em routers:**

```python
from fastapi import Depends
from services.credentials import ConfigService, get_config_service

@router.get("/credentials")
async def get_credentials(
    config_service: ConfigService = Depends(get_config_service)
):
    return config_service.get_credentials()
```

---

## 3. Backend - Estrutura de Pacotes (Prioridade MEDIA)

### Situacao Atual
Hacks com `sys.path.insert()` para imports.

### Solucao: Estrutura de Pacote Python

**Criar:** `backend/pyproject.toml`

```toml
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "etl-dashboard-backend"
version = "2.0.0"
dependencies = [
    "fastapi>=0.110.0",
    "uvicorn>=0.27.1",
    "websockets>=12.0",
    "pydantic>=2.6.3",
    "python-multipart>=0.0.9",
    "python-jose[cryptography]>=3.3.0",
    "passlib[bcrypt]>=1.7.4",
]

[tool.setuptools.packages.find]
where = ["."]
```

**Atualizar imports em todos os arquivos:**

```python
# Antes (com hack)
import sys
sys.path.insert(0, _backend_dir)
from services.credentials import get_config_service

# Depois (correto)
from backend.services.credentials import get_config_service
```

**Instalar em modo desenvolvimento:**

```bash
cd backend
pip install -e .
```

---

## 4. Frontend - TanStack Query (Prioridade ALTA)

### Situacao Atual
`useState` + `useEffect` para cada fetch, sem cache.

### Solucao: Implementar TanStack Query

**Criar:** `frontend/src/lib/query-client.ts`

```typescript
import { QueryClient } from "@tanstack/react-query"

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutos
      gcTime: 1000 * 60 * 30,   // 30 minutos
      retry: 3,
      refetchOnWindowFocus: false,
    },
  },
})
```

**Atualizar:** `frontend/src/main.tsx`

```typescript
import { QueryClientProvider } from "@tanstack/react-query"
import { ReactQueryDevtools } from "@tanstack/react-query-devtools"
import { queryClient } from "@/lib/query-client"

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <ThemeProvider defaultTheme="light" storageKey="etl-ui-theme">
        <App />
      </ThemeProvider>
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  </React.StrictMode>
)
```

**Criar hooks:** `frontend/src/hooks/queries/use-config.ts`

```typescript
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { api } from "@/services/api"
import { ConfiguracaoETL } from "@/types"

export const configKeys = {
  all: ["config"] as const,
  detail: () => [...configKeys.all, "detail"] as const,
}

export function useConfig() {
  return useQuery({
    queryKey: configKeys.detail(),
    queryFn: api.getConfig,
  })
}

export function useSaveCredentials() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: api.saveCredentials,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: configKeys.all })
    },
  })
}
```

**Criar hooks:** `frontend/src/hooks/queries/use-sistemas.ts`

```typescript
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { api } from "@/services/api"

export const sistemasKeys = {
  all: ["sistemas"] as const,
  list: () => [...sistemasKeys.all, "list"] as const,
  detail: (id: string) => [...sistemasKeys.all, id] as const,
}

export function useSistemas() {
  return useQuery({
    queryKey: sistemasKeys.list(),
    queryFn: api.getSistemas,
  })
}

export function useToggleSistema() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, ativo }: { id: string; ativo: boolean }) =>
      api.toggleSistema(id, ativo),
    onMutate: async ({ id, ativo }) => {
      // Cancelar queries em andamento
      await queryClient.cancelQueries({ queryKey: sistemasKeys.list() })

      // Snapshot anterior
      const previousSistemas = queryClient.getQueryData(sistemasKeys.list())

      // Atualizacao otimista
      queryClient.setQueryData(sistemasKeys.list(), (old: any) => ({
        ...old,
        sistemas: old.sistemas.map((s: any) =>
          s.id === id ? { ...s, ativo } : s
        ),
      }))

      return { previousSistemas }
    },
    onError: (err, variables, context) => {
      // Rollback em caso de erro
      if (context?.previousSistemas) {
        queryClient.setQueryData(sistemasKeys.list(), context.previousSistemas)
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: sistemasKeys.list() })
    },
  })
}
```

**Refatorar pagina:** `frontend/src/pages/etl/page.tsx`

```typescript
import { useConfig } from "@/hooks/queries/use-config"
import { useSistemas, useToggleSistema } from "@/hooks/queries/use-sistemas"
import { Skeleton } from "@/components/ui/skeleton"

export default function EtlPage() {
  // Substituir useState + useEffect por hooks
  const { data: config, isLoading, error } = useConfig()
  const { data: sistemasData } = useSistemas()
  const toggleSistema = useToggleSistema()

  if (isLoading) {
    return <Skeleton className="h-96 w-full" />
  }

  if (error) {
    return <div className="text-destructive">Erro ao carregar: {error.message}</div>
  }

  const handleToggle = (id: string, ativo: boolean) => {
    toggleSistema.mutate({ id, ativo })
  }

  return (
    // ... JSX usando config e sistemasData
  )
}
```

---

## 5. Frontend - Zustand para Estado Global (Prioridade ALTA)

### Situacao Atual
Estado de execucao espalhado em props.

### Solucao: Store Zustand

**Criar:** `frontend/src/stores/execution-store.ts`

```typescript
import { create } from "zustand"
import { devtools, persist } from "zustand/middleware"

interface ExecutionState {
  // Estado
  isExecuting: boolean
  currentJobId: number | null
  isConnected: boolean
  logs: LogEntry[]

  // Acoes
  startExecution: (jobId: number) => void
  stopExecution: () => void
  setConnected: (connected: boolean) => void
  addLog: (log: LogEntry) => void
  clearLogs: () => void
}

interface LogEntry {
  level: string
  sistema: string | null
  message: string
  timestamp: string
}

export const useExecutionStore = create<ExecutionState>()(
  devtools(
    persist(
      (set, get) => ({
        // Estado inicial
        isExecuting: false,
        currentJobId: null,
        isConnected: false,
        logs: [],

        // Acoes
        startExecution: (jobId) =>
          set({ isExecuting: true, currentJobId: jobId }),

        stopExecution: () =>
          set({ isExecuting: false, currentJobId: null }),

        setConnected: (connected) =>
          set({ isConnected: connected }),

        addLog: (log) =>
          set((state) => ({
            logs: [...state.logs.slice(-999), log], // Manter ultimos 1000
          })),

        clearLogs: () =>
          set({ logs: [] }),
      }),
      {
        name: "execution-storage",
        partialize: (state) => ({
          // Persistir apenas alguns campos
          logs: state.logs.slice(-100),
        }),
      }
    ),
    { name: "ExecutionStore" }
  )
)
```

**Criar:** `frontend/src/stores/config-store.ts`

```typescript
import { create } from "zustand"
import { Periodo } from "@/types"

interface ConfigState {
  periodo: Periodo
  setPeriodo: (periodo: Periodo) => void
}

const getDefaultPeriodo = (): Periodo => {
  const hoje = new Date()
  const mesAnterior = new Date(hoje)
  mesAnterior.setMonth(mesAnterior.getMonth() - 1)

  return {
    data_inicial: mesAnterior.toLocaleDateString("pt-BR"),
    data_final: hoje.toLocaleDateString("pt-BR"),
  }
}

export const useConfigStore = create<ConfigState>()((set) => ({
  periodo: getDefaultPeriodo(),
  setPeriodo: (periodo) => set({ periodo }),
}))
```

**Usar nos componentes:**

```typescript
import { useExecutionStore } from "@/stores/execution-store"

function ExecutionControls() {
  const { isExecuting, startExecution, stopExecution } = useExecutionStore()

  const handleExecute = async () => {
    const result = await api.execute(sistemas, periodo)
    startExecution(result.job_id)
  }

  const handleCancel = async () => {
    await api.cancelJob(currentJobId)
    stopExecution()
  }

  return (
    <Button onClick={isExecuting ? handleCancel : handleExecute}>
      {isExecuting ? "Cancelar" : "Executar"}
    </Button>
  )
}
```

---

## 6. Python ETL - Classe Base (Prioridade MEDIA)

### Situacao Atual
Codigo duplicado em cada modulo Selenium.

### Solucao: Classe Base Abstrata

**Criar:** `python/modules/base_automation.py`

```python
from abc import ABC, abstractmethod
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import logging
import time
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class BaseAutomation(ABC):
    """Classe base para automacoes Selenium"""

    def __init__(self, config: Dict[str, Any], download_path: Optional[Path] = None):
        self.config = config
        self.download_path = download_path or Path.cwd() / "downloads"
        self.driver: Optional[webdriver.Chrome] = None
        self.wait: Optional[WebDriverWait] = None
        self.timeout = 30

    def setup_driver(self) -> webdriver.Chrome:
        """Configura e retorna ChromeDriver"""
        options = Options()

        # Configuracoes de download
        prefs = {
            "download.default_directory": str(self.download_path),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
        }
        options.add_experimental_option("prefs", prefs)

        # Modo headless (opcional)
        if self.config.get("headless", False):
            options.add_argument("--headless")
            options.add_argument("--disable-gpu")

        # Outras opcoes uteis
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")

        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, self.timeout)

        return self.driver

    def login(self, url: str, username: str, password: str) -> bool:
        """Login generico - sobrescrever para casos especificos"""
        try:
            self.driver.get(url)
            self._fill_login_form(username, password)
            self._submit_login()
            return self._verify_login()
        except Exception as e:
            logger.error(f"Erro no login: {e}")
            return False

    @abstractmethod
    def _fill_login_form(self, username: str, password: str):
        """Preenche formulario de login - implementar por sistema"""
        pass

    @abstractmethod
    def _submit_login(self):
        """Submete formulario de login - implementar por sistema"""
        pass

    @abstractmethod
    def _verify_login(self) -> bool:
        """Verifica se login foi bem sucedido - implementar por sistema"""
        pass

    @abstractmethod
    def execute(self, data_inicial: str = None, data_final: str = None):
        """Executa automacao principal - implementar por sistema"""
        pass

    def wait_for_downloads(self, timeout: int = 60) -> bool:
        """Aguarda downloads serem concluidos"""
        end_time = time.time() + timeout

        while time.time() < end_time:
            downloading = list(self.download_path.glob("*.crdownload"))
            if not downloading:
                return True
            time.sleep(1)

        return False

    def screenshot(self, name: str = "screenshot"):
        """Captura screenshot para debug"""
        if self.driver:
            path = self.download_path / f"{name}_{int(time.time())}.png"
            self.driver.save_screenshot(str(path))
            logger.info(f"Screenshot salvo: {path}")

    def cleanup(self):
        """Limpa recursos"""
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
            self.driver = None

    def __enter__(self):
        self.setup_driver()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.screenshot("error")
        self.cleanup()
        return False


class RetryMixin:
    """Mixin para adicionar retry com backoff"""

    def retry_action(
        self,
        action,
        max_retries: int = 3,
        backoff_factor: float = 2.0,
        exceptions: tuple = (Exception,)
    ):
        """Executa acao com retry e backoff exponencial"""
        last_exception = None

        for attempt in range(max_retries):
            try:
                return action()
            except exceptions as e:
                last_exception = e
                wait_time = backoff_factor ** attempt
                logger.warning(
                    f"Tentativa {attempt + 1}/{max_retries} falhou: {e}. "
                    f"Aguardando {wait_time}s..."
                )
                time.sleep(wait_time)

        raise last_exception
```

**Refatorar modulo:** `python/modules/maps_automation.py`

```python
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from .base_automation import BaseAutomation, RetryMixin
import logging

logger = logging.getLogger(__name__)


class MapsAutomation(BaseAutomation, RetryMixin):
    """Automacao para plataforma MAPS"""

    def _fill_login_form(self, username: str, password: str):
        user_field = self.wait.until(
            EC.presence_of_element_located((By.ID, "username"))
        )
        user_field.clear()
        user_field.send_keys(username)

        pwd_field = self.driver.find_element(By.ID, "password")
        pwd_field.clear()
        pwd_field.send_keys(password)

    def _submit_login(self):
        submit_btn = self.driver.find_element(By.ID, "login-button")
        submit_btn.click()

    def _verify_login(self) -> bool:
        try:
            self.wait.until(
                EC.presence_of_element_located((By.ID, "dashboard"))
            )
            return True
        except:
            return False

    def execute(self, data_inicial: str = None, data_final: str = None):
        """Executa download de relatorios MAPS"""
        creds = self.config.get("maps", {})

        # Login
        if not self.login(
            creds.get("url"),
            creds.get("username"),
            creds.get("password")
        ):
            raise Exception("Falha no login MAPS")

        logger.info("Login MAPS realizado com sucesso")

        # Download ativos
        self.retry_action(lambda: self._download_ativos(data_inicial, data_final))

        # Download passivos
        self.retry_action(lambda: self._download_passivos(data_inicial, data_final))

        # Aguardar downloads
        self.wait_for_downloads()

        logger.info("MAPS concluido com sucesso")

    def _download_ativos(self, data_inicial: str, data_final: str):
        # Implementacao especifica
        pass

    def _download_passivos(self, data_inicial: str, data_final: str):
        # Implementacao especifica
        pass


def executar(config: dict, data_inicial: str = None, data_final: str = None):
    """Funcao de entrada para orquestrador"""
    download_path = config.get("paths", {}).get("maps")

    with MapsAutomation(config, download_path) as automation:
        automation.execute(data_inicial, data_final)
```

---

## 7. Containerizacao com Docker (Prioridade MEDIA)

**Criar:** `Dockerfile.backend`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Dependencias de sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Dependencias Python
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Codigo
COPY backend/ ./backend/
COPY python/ ./python/
COPY config/ ./config/

# Variaveis de ambiente
ENV PYTHONPATH=/app
ENV ETL_HOST=0.0.0.0
ENV ETL_PORT=4001

EXPOSE 4001

CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "4001"]
```

**Criar:** `Dockerfile.frontend`

```dockerfile
# Build stage
FROM node:20-alpine as build

WORKDIR /app

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# Production stage
FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

**Criar:** `docker-compose.yml`

```yaml
version: '3.8'

services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    ports:
      - "4001:4001"
    volumes:
      - ./config:/app/config
      - ./data:/app/backend/data
    environment:
      - ETL_DEBUG=false
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
    restart: unless-stopped

  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    ports:
      - "4000:80"
    depends_on:
      - backend
    restart: unless-stopped

volumes:
  data:
```

---

## 8. Testes Automatizados (Prioridade ALTA)

### Backend - pytest

**Criar:** `backend/tests/conftest.py`

```python
import pytest
from fastapi.testclient import TestClient
from backend.app import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_headers(client):
    response = client.post(
        "/api/auth/login",
        data={"username": "admin", "password": "admin123"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
```

**Criar:** `backend/tests/test_api.py`

```python
def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_sistemas_unauthorized(client):
    response = client.get("/api/sistemas")
    assert response.status_code == 401


def test_sistemas_authorized(client, auth_headers):
    response = client.get("/api/sistemas", headers=auth_headers)
    assert response.status_code == 200
    assert "sistemas" in response.json()
```

### Frontend - Vitest

**Criar:** `frontend/vitest.config.ts`

```typescript
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    globals: true,
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
})
```

**Criar:** `frontend/src/test/setup.ts`

```typescript
import '@testing-library/jest-dom'
import { afterEach } from 'vitest'
import { cleanup } from '@testing-library/react'

afterEach(() => {
  cleanup()
})
```

**Criar:** `frontend/src/components/__tests__/button.test.tsx`

```typescript
import { render, screen, fireEvent } from '@testing-library/react'
import { Button } from '../ui/button'
import { describe, it, expect, vi } from 'vitest'

describe('Button', () => {
  it('renders with text', () => {
    render(<Button>Click me</Button>)
    expect(screen.getByText('Click me')).toBeInTheDocument()
  })

  it('calls onClick when clicked', () => {
    const onClick = vi.fn()
    render(<Button onClick={onClick}>Click</Button>)
    fireEvent.click(screen.getByText('Click'))
    expect(onClick).toHaveBeenCalledTimes(1)
  })

  it('is disabled when disabled prop is true', () => {
    render(<Button disabled>Disabled</Button>)
    expect(screen.getByText('Disabled')).toBeDisabled()
  })
})
```

---

## 9. Monitoramento (Prioridade BAIXA)

### Prometheus + Grafana

**Adicionar ao backend:** `backend/core/metrics.py`

```python
from prometheus_client import Counter, Histogram, generate_latest
from fastapi import Response

# Metricas
REQUEST_COUNT = Counter(
    'etl_http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'etl_http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint']
)

JOB_COUNT = Counter(
    'etl_jobs_total',
    'Total ETL jobs',
    ['sistema', 'status']
)

JOB_DURATION = Histogram(
    'etl_job_duration_seconds',
    'ETL job duration',
    ['sistema']
)


async def metrics_endpoint():
    return Response(
        content=generate_latest(),
        media_type="text/plain"
    )
```

---

## Ordem de Implementacao Recomendada

### Fase 1 - Seguranca (1-2 semanas)
1. Implementar autenticacao JWT
2. Proteger todas as rotas sensiveis
3. Remover credenciais hardcoded
4. Criptografar credentials.json

### Fase 2 - Frontend Moderno (2-3 semanas)
5. Implementar TanStack Query
6. Implementar Zustand stores
7. Refatorar paginas para usar hooks
8. Adicionar error boundaries

### Fase 3 - Qualidade (2-3 semanas)
9. Adicionar testes backend (cobertura 50%)
10. Adicionar testes frontend (cobertura 30%)
11. Configurar CI/CD

### Fase 4 - Infraestrutura (1-2 semanas)
12. Containerizar com Docker
13. Configurar docker-compose para desenvolvimento
14. Documentar processo de deploy

### Fase 5 - Manutencao (Continuo)
15. Refatorar modulos Python com classe base
16. Adicionar logging estruturado
17. Implementar monitoramento

---

## Estimativa de Esforco

| Fase | Esforco | Prioridade |
|------|---------|------------|
| Seguranca | 1-2 semanas | CRITICA |
| Frontend Moderno | 2-3 semanas | ALTA |
| Qualidade | 2-3 semanas | ALTA |
| Infraestrutura | 1-2 semanas | MEDIA |
| Manutencao | Continuo | BAIXA |

**Total estimado:** 6-10 semanas para fases 1-4
