# 📘 Documentação do Projeto ETL Dashboard V2

Bem-vindo à documentação oficial do projeto **ETL Dashboard V2**. Este sistema foi desenvolvido para orquestrar e monitorar a execução de robôs de extração de dados (ETL) para diversos sistemas do mercado financeiro.

---

## 🏗️ 1. Visão Geral e Arquitetura

O projeto segue uma arquitetura moderna dividida em três camadas principais, garantindo desacoplamento e facilidade de manutenção.

### Componentes

1.  **Frontend (Interface do Usuário)**
    *   **Tecnologia**: Vite + React + TypeScript + Tailwind CSS.
    *   **Função**: Prover uma interface amigável para o operador executar rotinas, acompanhar logs em tempo real e gerenciar credenciais.
    *   **Localização**: `/frontend`

2.  **Backend (Servidor de Aplicação)**
    *   **Tecnologia**: Java Spring Boot.
    *   **Função**:
        *   Receber comandos do Frontend (API REST).
        *   Gerenciar a execução de subprocessos Python (`PythonExecutorService`).
        *   Transmitir logs em tempo real via WebSocket.
        *   Persistir configurações (`config_etl.json`).
    *   **Localização**: `/backend` (Código fonte em `/java` para este projeto específico)

3.  **Camada de Execução (Core ETL)**
    *   **Tecnologia**: Python 3.
    *   **Função**: Executar a lógica de negócio real (web scraping, chamadas de API, processamento de dados).
    *   **Entrypoint**: `python/main.py`.
    *   **Módulos**: Scripts individuais em `python/modules/*.py`.
    *   **Configuração**: `config/credentials.json` (credenciais sensíveis e caminhos).

---

## 🚀 2. Guia de Instalação e Execução

### Pré-requisitos
*   **Java JDK 17+** (para o backend).
*   **Node.js 18+** (para o frontend).
*   **Python 3.10+** (para os scripts ETL).
*   **Google Chrome** instalado (para automações Selenium).

### Inicialização Rápida

O projeto conta com scripts `.bat` na pasta `/scripts` para facilitar a execução.

1.  **Iniciar o Backend**:
    *   Execute `scripts/run-backend.bat`.
    *   Isso compilará o projeto Java (se necessário) e subirá o servidor na porta `8080`.

2.  **Iniciar o Frontend**:
    *   Execute `scripts/run-frontend.bat`.
    *   Isso iniciará o servidor de desenvolvimento Vite, geralmente acessível em `http://localhost:4000`.

3.  **Acessar**:
    *   Abra o navegador em `http://localhost:4000`.

---

## 📖 3. Guia do Usuário

### Dashboard Principal
A tela inicial exibe cartões para cada sistema integrado (AMPLIS, MAPS, FIDC, etc.).
*   **Status**: Indica se o sistema está Parado, Rodando, Sucesso ou Erro.
*   **Logs**: O painel à direita mostra o que está acontecendo em tempo real.

### Gerenciamento de Credenciais
Para configurar acessos e parâmetros:
1.  Clique no botão **"🔑 Credenciais"** no canto superior direito.
2.  Uma janela se abrirá com abas organizadas:
    *   **📊 Sistemas**: Usuários e senhas para cada portal (AMPLIS, JCOT, etc.).
    *   **🏢 Fundos**: Seleção granular de quais fundos processar para **FIDC**, **MAPS** e **QORE**.
        *   Use "Usar todos" para processar a lista completa.
        *   Desmarque e selecione individualmente se quiser rodar apenas fundos específicos.
    *   **📁 Pastas**: Caminhos locais onde os arquivos baixados serão salvos.
    *   **📝 JSON**: Editor avançado para visualizar o arquivo bruto.
3.  Clique em **"💾 Salvar"** para persistir as alterações em `config/credentials.json`.

### Executando uma Rotina
1.  **Selecione os sistemas** que deseja rodar marcando os checkboxes nos cartões.
    *   *Dica: Você pode usar "Selecionar Todos".*
2.  (Opcional) Marque **"🧹 Limpar Pastas Antes"** se quiser apagar os arquivos antigos dos diretórios de destino antes do download.
3.  Defina o **Período** (Data Inicial e Final).
4.  Clique em **"▶️ Executar Pipeline"**.

---

## 💻 4. Guia do Desenvolvedor

### Adicionando um Novo Módulo Python

1.  **Crie o script**: Adicione seu script `.py` em `python/modules/`.
2.  **Integre no `main.py`**:
    *   Adicione o sistema na lista de argumentos `choices` do `parser`.
    *   No loop principal de execução, adicione um bloco `elif sistema == 'novo_sistema':`.
    *   Importe seu módulo e chame a função principal, passando as credenciais lidas do dicionário `credentials`.
3.  **Atualize o Backend**:
    *   Edite `backend/src/main/resources/config_etl.json` (ou o arquivo de config externo) para adicionar a entrada do sistema na interface (ID, Nome, Ícone).
4.  **Atualize o Frontend (Opcional)**:
    *   Se precisar de campos de credenciais específicos, edite `frontend/src/main.ts` para renderizar os inputs no modal.

### Estrutura de Arquivos Importante

```
DEV_ETL/
├── backend/                # Código Java
│   └── src/main/java/com/etl/service/PythonExecutorService.java # Orquestrador
├── config/
│   └── credentials.json    # Dados sensíveis (ignorados no git idealmente)
├── frontend/               # Código Web
│   └── src/main.ts         # Lógica da UI
├── python/
│   ├── main.py             # Ponto de entrada
│   └── modules/            # Scripts de automação (amplis, maps, qore...)
└── scripts/                # Facilitadores (.bat)
```

### Notas sobre o `main.py`
O script `python/main.py` é projetado para ser flexível. Ele aceita argumentos via CLI (ex: `--data-inicial`) mas se baseia fortemente no arquivo de configuração para obter a lista de fundos e caminhos complexos.
*   **Argumentos Críticos**: `--config` (caminho do json) e `--sistemas` (lista de módulos a rodar).
*   **Tratamento de Erros**: Use a função `log("ERROR", "SISTEMA", "msg")` do `main.py` para garantir que o erro apareça formatado no dashboard Java.

---
*Gerado automaticamente pel Agentic Coding Assistant em 23/12/2025.*
