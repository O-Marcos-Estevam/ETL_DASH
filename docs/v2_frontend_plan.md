
# Planejamento: ETL Dashboard V2 (Frontend Profissional)

## 🎯 Objetivo
Reconstruir a interface do usuário (Frontend) com foco em **design profissional**, **ux avançado** e **arquitetura escalável**, mantendo a integração com o Backend Java existente.

## 🏗️ Estrutura Proposta
Devido a restrições de acesso ao sistema de arquivos pai, a sugestão é criar a estrutura V2 dentro do diretório atual ou arquivar a versão antiga.

**Opção A (Recomendada):** Arquivar V1 e Construir V2 in-loco.
- `frontend/` (Novo V2)
- `legacy/frontend_v1/` (Backup da versão atual)
- *Vantagem:* Não duplica Backend/Java/Node (economiza ~500MB). Mantém scripts funcionais.

**Opção B:** Pasta `DEV_ETL_V2` interna.
- `DEV_ETL/DEV_ETL_V2/frontend`
- *Desvantagem:* Caminhos longos e duplicação de arquivos.

---

## 💻 Tech Stack (Profissional)
Utilizaremos as tecnologias mais modernas do mercado (2024/2025):

1.  **Core**: React 18+ com TypeScript (Vite).
2.  **Estilização**: **Tailwind CSS** (Utility-first, rápido e bonito).
3.  **UI Components**: **Shadcn/UI** (Conceito) + **Radix UI** (Acessibilidade).
    *   *Design*: Minimalista, Clean, Dark Mode nativo, Fontes Premium (Inter).
4.  **Icons**: `lucide-react` (Ícones vetoriais modernos).
5.  **State Management**: `Zustand` (Gerenciamento de estado global leve e performático).
6.  **Data Fetching**: `TanStack Query` (React Query) - Para cache, loading states e revalidação automática de dados do backend.
7.  **Charts**: `Recharts` - Gráficos interativos e responsivos para o Dashboard.
8.  **Forms**: `React Hook Form` + `Zod` (Validação de schemas robusta).
9.  **Routing**: `React Router v6`.

---

## 🎨 Design System & Features

### 1. Layout Principal (App Shell)
- **Sidebar Retrátil**: Navegação lateral moderna com ícones e colapso suave.
- **Top Bar**: Breadcrumbs, Seletor de Tema (Light/Dark), Status de Conexão WebSocket.

### 2. Dashboard (Home)
- **KPI Cards**: Cards com totais (Processos, Sucessos, Falhas) com indicadores visuais (setas, cores) e "sparklines".
- **Execution Chart**: Gráfico de área mostrando volume de execuções nas últimas 24h.
- **Recent Activity**: Lista compacta das últimas ações do sistema.

### 3. Monitor de Logs (Live)
- Console visual estilo "Matrix/Terminal" mas com syntax highlighting e filtros.
- WebSocket integration (já existe no backend, será aprimorado no front).

### 4. Configurações (Settings)
- Editor JSON visual ou formulário estruturado para editar `credentials.json` e parâmetros.
- Validação em tempo real (impede salvar config quebrada).

---

## 📅 Plano de Execução

### Fase 1: Setup & Base
1.  Mover `frontend` atual para `legacy/frontend_v1`.
2.  Inicializar novo projeto Vite (`frontend`).
3.  Configurar Tailwind CSS e estrutura de pastas (`src/components`, `src/pages`, `src/hooks`).
4.  Configurar Proxy para Backend (Porta 4001).

### Fase 2: Componentes Core
1.  Criar componentes base (Button, Card, Input, Table) usando Tailwind.
2.  Implementar Layout (Sidebar + Header).
3.  Configurar Roteamento.

### Fase 3: Integração & Dashboard
1.  Conectar com API Java (endpoints existentes).
2.  Criar Dashboard com Gráficos Recharts.
3.  Implementar Monitor de Logs via WebSocket.

### Fase 4: Refinamento
1.  Polimento visual (animações, transições, skeleton screens).
2.  Testes finais.

---

## ❓ Decisão Necessária
Você prefere a **Opção A** (Substituir V1 mantendo backup) ou **Opção B** (Criar subpasta V2)?
*Como agente, recomendo a **Opção A** para manter o projeto limpo e leve.*
