# ETL Dashboard V2

Sistema de gerenciamento de downloads ETL desenvolvido com TypeScript e Java Spring Boot.

## Tecnologias

### Backend
- **Java 17**
- **Spring Boot 3.2**
- **WebSocket (STOMP)**
- **Selenium WebDriver**
- **Apache POI**
- **Lombok**

### Frontend
- **TypeScript 5.3**
- **Vite**
- **SockJS + STOMP**
- **CSS3 com variaveis**

## Estrutura do Projeto

```
DEV_ETL/
├── backend/                    # API Java Spring Boot
│   ├── src/main/java/com/etl/
│   │   ├── config/            # Configuracoes (CORS, WebSocket)
│   │   ├── controller/        # REST Controllers
│   │   ├── model/             # Modelos de dados
│   │   ├── service/           # Logica de negocio
│   │   └── automation/        # Selenium automations
│   ├── src/main/resources/
│   │   └── application.yml    # Configuracoes
│   └── pom.xml                # Dependencias Maven
│
├── frontend/                   # Interface TypeScript
│   ├── src/
│   │   ├── components/        # Componentes UI
│   │   ├── services/          # API e WebSocket
│   │   ├── types/             # TypeScript types
│   │   └── styles/            # CSS
│   ├── index.html
│   ├── package.json
│   └── tsconfig.json
│
└── scripts/                    # Scripts de build/run
    ├── build.bat
    ├── run-backend.bat
    ├── run-frontend.bat
    └── run-dev.bat
```

## Pre-requisitos

- **Java JDK 17+**
- **Maven 3.8+**
- **Node.js 18+**
- **npm 9+**

## Instalacao

1. **Build completo:**
   ```bash
   cd scripts
   build.bat
   ```

2. **Instalar dependencias separadamente:**
   ```bash
   # Backend
   cd backend
   mvn clean install

   # Frontend
   cd frontend
   npm install
   ```

## Execucao

### Modo Desenvolvimento (recomendado)
```bash
cd scripts
run-dev.bat
```
Isso inicia backend e frontend simultaneamente.

### Separadamente
```bash
# Terminal 1 - Backend
cd scripts
run-backend.bat

# Terminal 2 - Frontend
cd scripts
run-frontend.bat
```

## URLs

- **Frontend:** http://localhost:5173
- **Backend API:** http://localhost:8080
- **WebSocket:** ws://localhost:8080/ws

## API Endpoints

| Metodo | Endpoint | Descricao |
|--------|----------|-----------|
| GET | /api/config | Obter configuracao |
| POST | /api/config | Salvar configuracao |
| GET | /api/sistemas | Listar sistemas |
| GET | /api/sistemas/ativos | Listar sistemas ativos |
| PATCH | /api/sistemas/{id}/toggle | Ativar/desativar sistema |
| PATCH | /api/sistemas/{id}/opcao | Atualizar opcao |
| POST | /api/execute | Executar pipeline |
| POST | /api/execute/{id} | Executar sistema especifico |
| POST | /api/cancel/{id} | Cancelar execucao |
| GET | /api/health | Health check |

## WebSocket Topics

| Topic | Descricao |
|-------|-----------|
| /topic/logs | Logs em tempo real |
| /topic/status/{id} | Status de execucao por sistema |

## Sistemas Suportados

1. **AMPLIS REAG** - Download CSV/PDF
2. **AMPLIS MASTER** - Download CSV/PDF
3. **MAPS** - Download consolidado
4. **FIDC ESTOQUE** - Estoque FIDC
5. **JCOT** - Cotacoes
6. **BRITECH** - Base de dados
7. **QORE** - PDF/Excel/XML
8. **TRUSTEE** - Em desenvolvimento

## Autor

NS Capital - 2024
