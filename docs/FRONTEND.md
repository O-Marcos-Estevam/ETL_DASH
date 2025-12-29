# Documentacao do Frontend

## Visao Geral

O frontend do ETL Dashboard e uma Single Page Application (SPA) construida com React 19, TypeScript e Vite. Utiliza componentes shadcn/ui (baseados em Radix UI) para uma interface moderna e acessivel.

---

## Stack Tecnologico

| Tecnologia | Versao | Proposito |
|------------|--------|-----------|
| React | 19.2.0 | Framework UI |
| TypeScript | 5.6.x | Type safety |
| Vite | 5.4.x | Bundler/Dev server |
| TailwindCSS | 3.4.x | Estilizacao |
| Radix UI | Varios | Componentes acessiveis |
| React Router | 7.11.x | Roteamento SPA |
| Recharts | 3.6.x | Graficos |
| Lucide React | 0.513.x | Icones |

---

## Estrutura de Pastas

```
frontend/
├── src/
│   ├── App.tsx                 # Componente raiz com rotas
│   ├── main.tsx               # Entry point
│   ├── index.css              # Estilos globais (Tailwind)
│   │
│   ├── components/            # Componentes React
│   │   ├── ui/                # Primitivos (shadcn/ui)
│   │   │   ├── button.tsx
│   │   │   ├── card.tsx
│   │   │   ├── input.tsx
│   │   │   ├── toast.tsx
│   │   │   └── ...
│   │   │
│   │   ├── layout/            # Layout da aplicacao
│   │   │   ├── app-layout.tsx
│   │   │   ├── header.tsx
│   │   │   └── sidebar.tsx
│   │   │
│   │   ├── dashboard/         # Componentes do Dashboard
│   │   │   ├── kpi-card.tsx
│   │   │   ├── execution-chart.tsx
│   │   │   └── recent-activity.tsx
│   │   │
│   │   ├── etl/               # Componentes da pagina ETL
│   │   │   ├── system-card.tsx
│   │   │   ├── systems-grid.tsx
│   │   │   ├── execution-controls.tsx
│   │   │   ├── period-selector.tsx
│   │   │   └── credentials-modal.tsx
│   │   │
│   │   ├── logs/              # Componentes de logs
│   │   │   ├── log-viewer.tsx
│   │   │   ├── log-filter.tsx
│   │   │   └── log-entry-row.tsx
│   │   │
│   │   ├── settings/          # Formularios de configuracao
│   │   │   ├── credentials-form.tsx
│   │   │   ├── paths-form.tsx
│   │   │   ├── funds-form.tsx
│   │   │   └── settings-form.tsx
│   │   │
│   │   ├── portfolio/         # Graficos de portfolio
│   │   │   ├── portfolio-stacked-chart.tsx
│   │   │   └── portfolio-treemap.tsx
│   │   │
│   │   ├── mode-toggle.tsx    # Toggle dark/light mode
│   │   └── theme-provider.tsx # Context de tema
│   │
│   ├── pages/                 # Paginas (rotas)
│   │   ├── dashboard/page.tsx
│   │   ├── etl/page.tsx
│   │   ├── logs/page.tsx
│   │   ├── portfolio/page.tsx
│   │   └── settings/page.tsx
│   │
│   ├── services/              # Comunicacao com backend
│   │   ├── api.ts             # Cliente HTTP REST
│   │   ├── websocket.ts       # Cliente WebSocket
│   │   └── index.ts           # Barrel export
│   │
│   ├── hooks/                 # Custom hooks
│   │   ├── useLocalStorage.ts
│   │   ├── useNotification.ts
│   │   └── index.ts
│   │
│   ├── types/                 # Definicoes TypeScript
│   │   ├── etl.ts             # Tipos ETL
│   │   ├── portfolio.ts       # Tipos Portfolio
│   │   └── index.ts
│   │
│   └── lib/                   # Utilitarios
│       ├── utils.ts           # cn() e helpers
│       ├── constants.ts       # Constantes
│       └── index.ts
│
├── index.html                 # HTML template
├── package.json               # Dependencias
├── vite.config.ts            # Configuracao Vite
├── tailwind.config.js        # Configuracao Tailwind
├── tsconfig.json             # Configuracao TypeScript
└── components.json           # Configuracao shadcn/ui
```

---

## Paginas

### 1. Dashboard (`/`)

**Arquivo:** `pages/dashboard/page.tsx`

Pagina inicial com visao geral do sistema.

**Componentes:**
- `KpiCard` - Cards com metricas (Total Jobs, Success Rate, etc)
- `ExecutionChart` - Grafico de barras de execucoes
- `RecentActivity` - Lista de atividades recentes

> **Nota:** Atualmente usa dados mockados. Precisa integrar com API real.

---

### 2. ETL (`/etl`)

**Arquivo:** `pages/etl/page.tsx`

Pagina principal para execucao de pipelines ETL.

**Componentes:**
- `PeriodSelector` - Seletor de datas inicial/final
- `SystemsGrid` - Grid de cards de sistemas
  - `SystemCard` - Card individual com toggle e opcoes
  - `SystemIcon` - Icone do sistema
- `ExecutionControls` - Botoes Executar/Cancelar
- `CredentialsModal` - Modal de configuracao de credenciais

**Estado:**
```typescript
const [config, setConfig] = useState<ConfiguracaoETL | null>(null)
const [loading, setLoading] = useState(true)
const [isExecuting, setIsExecuting] = useState(false)
const [isConnected, setIsConnected] = useState(false)
const [currentJobId, setCurrentJobId] = useState<number | null>(null)
const [periodo, setPeriodo] = useState<Periodo>({...})
```

**Fluxo de Execucao:**
1. Usuario seleciona sistemas e periodo
2. Clica "Executar"
3. POST `/api/execute` cria job
4. WebSocket recebe logs em tempo real
5. Status atualizado via eventos `status`
6. `job_complete` finaliza execucao

---

### 3. Logs (`/logs`)

**Arquivo:** `pages/logs/page.tsx`

Visualizador de logs em tempo real.

**Componentes:**
- `LogFilter` - Filtros por sistema e nivel
- `LogViewer` - Container scrollavel
  - `LogEntryRow` - Linha individual de log

**Funcionalidades:**
- Auto-scroll (toggleavel)
- Filtro por nivel (DEBUG, INFO, WARNING, ERROR)
- Filtro por sistema
- Pause/Resume de atualizacoes

---

### 4. Portfolio (`/portfolio`)

**Arquivo:** `pages/portfolio/page.tsx`

Visualizacao de dados de portfolio.

**Componentes:**
- `PortfolioStackedChart` - Grafico de barras empilhadas
- `PortfolioTreemap` - Treemap de composicao

> **Nota:** Usa dados mockados. Precisa integracao com backend.

---

### 5. Settings (`/settings`)

**Arquivo:** `pages/settings/page.tsx`

Configuracoes do sistema.

**Componentes (Tabs):**
- `SettingsForm` - Configuracoes gerais
- `CredentialsForm` - Credenciais de sistemas
- `PathsForm` - Caminhos de arquivos
- `FundsForm` - Selecao de fundos

---

## Componentes UI (shadcn/ui)

Componentes reutilizaveis baseados em Radix UI:

| Componente | Arquivo | Descricao |
|------------|---------|-----------|
| Button | `ui/button.tsx` | Botao com variantes |
| Card | `ui/card.tsx` | Container card |
| Input | `ui/input.tsx` | Campo de entrada |
| Label | `ui/label.tsx` | Label para inputs |
| Select | `ui/select.tsx` | Dropdown select |
| Switch | `ui/switch.tsx` | Toggle switch |
| Tabs | `ui/tabs.tsx` | Navegacao por tabs |
| Toast | `ui/toast.tsx` | Notificacoes |
| Toaster | `ui/toaster.tsx` | Container de toasts |
| Tooltip | `ui/tooltip.tsx` | Tooltips |
| Badge | `ui/badge.tsx` | Badges/tags |
| Skeleton | `ui/skeleton.tsx` | Loading placeholder |
| ScrollArea | `ui/scroll-area.tsx` | Area scrollavel |
| Separator | `ui/separator.tsx` | Linha divisoria |
| DropdownMenu | `ui/dropdown-menu.tsx` | Menu dropdown |
| Textarea | `ui/textarea.tsx` | Area de texto |

---

## Services

### API Service (`services/api.ts`)

Cliente HTTP para comunicacao com backend.

```typescript
// Configuracao
const API_BASE = 'http://localhost:4001/api'
const TIMEOUT = 5000

// Funcoes disponiveis
api.getConfig()              // GET /api/config
api.getSistemas()            // GET /api/sistemas
api.toggleSistema(id, ativo) // PATCH /api/sistemas/:id/toggle
api.toggleOption(id, opt, val) // PATCH /api/sistemas/:id/opcao
api.execute(sistemas, periodo) // POST /api/execute
api.cancelJob(jobId)         // POST /api/cancel/:id
api.getJobStatus(jobId)      // GET /api/jobs/:id
api.getCredentials()         // GET /api/credentials
api.saveCredentials(creds)   // POST /api/credentials
api.checkHealth()            // GET /api/health
```

**Tratamento de Erros:**
```typescript
try {
  const data = await api.getConfig()
} catch (error) {
  // error.message contem detalhes
}
```

---

### WebSocket Service (`services/websocket.ts`)

Cliente WebSocket para atualizacoes em tempo real.

```typescript
// Importar servico singleton
import { wsService } from '@/services/websocket'

// Conectar
wsService.connect()

// Ouvir eventos
wsService.on('log', (data) => {
  console.log(`[${data.level}] ${data.message}`)
})

wsService.on('status', (data) => {
  console.log(`Sistema ${data.sistema_id}: ${data.status}`)
})

wsService.on('job_complete', (data) => {
  console.log(`Job ${data.job_id} finalizado: ${data.status}`)
})

// Desconectar
wsService.disconnect()

// Verificar conexao
if (wsService.isConnected()) {
  // ...
}
```

**Reconexao Automatica:**
- Tenta reconectar apos desconexao
- Backoff exponencial (1s, 2s, 4s, ...)
- Maximo 5 tentativas

---

## Hooks

### useLocalStorage

Persistencia em localStorage com tipagem.

```typescript
const [value, setValue] = useLocalStorage<Theme>('theme', 'light')

// value: Theme
// setValue: (newValue: Theme) => void
```

### useNotification

Gerenciamento de notificacoes toast.

```typescript
const { showToast } = useNotification()

showToast({
  title: 'Sucesso',
  description: 'Operacao concluida',
  variant: 'success' // 'success' | 'error' | 'warning' | 'info'
})
```

---

## Tipos

### ETL Types (`types/etl.ts`)

```typescript
// Status de um sistema
type SistemaStatus = 'IDLE' | 'RUNNING' | 'SUCCESS' | 'ERROR' | 'CANCELLED'

// Opcoes de um sistema
interface SistemaOpcoes {
  csv?: boolean
  pdf?: boolean
  excel?: boolean
  base_total?: boolean
}

// Sistema completo
interface Sistema {
  id: string
  nome: string
  descricao: string
  ativo: boolean
  status: SistemaStatus
  opcoes: SistemaOpcoes
  ultima_execucao: string | null
  mensagem: string | null
}

// Periodo de execucao
interface Periodo {
  data_inicial: string  // DD/MM/YYYY
  data_final: string    // DD/MM/YYYY
}

// Configuracao completa
interface ConfiguracaoETL {
  amplis: { reag: Credentials; master: Credentials }
  maps: Credentials
  fidc: Credentials
  jcot: Credentials
  britech: Credentials
  qore: Credentials
  paths: Paths
  sistemas: Sistema[]
}

// Entrada de log
interface LogEntry {
  level: 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR'
  sistema: string | null
  message: string
  timestamp: string
}
```

---

## Estilizacao

### Tailwind CSS

O projeto usa Tailwind CSS com configuracao customizada.

**Cores Customizadas (CSS Variables):**
```css
:root {
  --background: 0 0% 100%;
  --foreground: 240 10% 3.9%;
  --primary: 240 5.9% 10%;
  --primary-foreground: 0 0% 98%;
  --secondary: 240 4.8% 95.9%;
  --muted: 240 4.8% 95.9%;
  --accent: 240 4.8% 95.9%;
  --destructive: 0 84.2% 60.2%;
  --border: 240 5.9% 90%;
  --ring: 240 5.9% 10%;
}

.dark {
  --background: 240 10% 3.9%;
  --foreground: 0 0% 98%;
  /* ... dark mode colors */
}
```

**Utilitario cn():**
```typescript
import { cn } from '@/lib/utils'

// Combina classes condicionalmente
<div className={cn(
  'base-class',
  isActive && 'active-class',
  variant === 'primary' ? 'primary' : 'secondary'
)} />
```

---

## Roteamento

Configurado em `App.tsx`:

```typescript
<BrowserRouter>
  <Routes>
    <Route element={<AppLayout />}>
      <Route path="/" element={<DashboardPage />} />
      <Route path="/etl" element={<EtlPage />} />
      <Route path="/logs" element={<LogsPage />} />
      <Route path="/portfolio" element={<PortfolioPage />} />
      <Route path="/settings" element={<SettingsPage />} />
    </Route>
  </Routes>
</BrowserRouter>
```

**Navegacao:**
- `/` - Dashboard
- `/etl` - Execucao ETL
- `/logs` - Visualizador de logs
- `/portfolio` - Graficos de portfolio
- `/settings` - Configuracoes

---

## Tema (Dark/Light Mode)

Gerenciado por `ThemeProvider`:

```typescript
// main.tsx
<ThemeProvider defaultTheme="light" storageKey="etl-ui-theme">
  <App />
</ThemeProvider>

// Em qualquer componente
import { useTheme } from '@/components/theme-provider'

const { theme, setTheme } = useTheme()
// theme: 'light' | 'dark' | 'system'
```

**Toggle:**
```typescript
<ModeToggle /> // Componente pronto
```

---

## Build e Deploy

### Desenvolvimento

```bash
cd frontend
npm install
npm run dev
```

Servidor em: http://localhost:4000

### Build de Producao

```bash
npm run build
```

Output em: `frontend/dist/`

### Preview Build

```bash
npm run preview
```

---

## Configuracao

### vite.config.ts

```typescript
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 4000,
    host: true,
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          ui: ['@radix-ui/react-dialog', ...],
        }
      }
    }
  }
})
```

### tsconfig.json

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "lib": ["ES2020", "DOM"],
    "module": "ESNext",
    "strict": true,
    "jsx": "react-jsx",
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}
```

---

## Problemas Conhecidos

### 1. Dependencias Nao Utilizadas
- `@tanstack/react-query` instalado mas nao usado
- `zustand` instalado mas nao usado

**Recomendacao:** Implementar ou remover.

### 2. Dados Mockados
- Dashboard usa dados estaticos
- Portfolio usa dados estaticos

**Recomendacao:** Criar endpoints no backend.

### 3. Diretivas Next.js
- `"use client"` em arquivos (nao tem efeito no Vite)

**Recomendacao:** Remover.

### 4. Tipo `any`
- Varios arquivos usam `any`

**Recomendacao:** Definir tipos adequados.

---

## Proximos Passos

1. **Implementar TanStack Query**
   - Caching de dados
   - Revalidacao automatica
   - Estados de loading/error

2. **Implementar Zustand**
   - Estado global de execucao
   - Estado de conexao WebSocket

3. **Adicionar Testes**
   - Vitest para unit tests
   - Testing Library para componentes

4. **Internacionalizacao**
   - Strings em portugues/ingles
   - Biblioteca i18n
