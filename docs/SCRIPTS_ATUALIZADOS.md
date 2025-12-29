# Scripts Executáveis Atualizados

## 📋 Resumo

Todos os scripts executáveis foram atualizados para usar o novo backend **Python/FastAPI** em vez do antigo Java/Spring Boot.

---

## ✅ Arquivos Atualizados

### 1. **INICIAR.bat** (Raiz do projeto)
**Descrição:** Script principal para iniciar o sistema completo

**Melhorias:**
- ✅ Verificação de Python e Node.js antes de iniciar
- ✅ Limpeza automática de processos antigos na porta 4001
- ✅ Inicia Backend e Frontend em janelas separadas
- ✅ Mensagens informativas e coloridas
- ✅ Exibe URLs de acesso ao finalizar

**Uso:**
```batch
INICIAR.bat
```

---

### 2. **scripts/start-backend.bat**
**Descrição:** Inicia apenas o Backend FastAPI

**Melhorias:**
- ✅ Verifica se Python está instalado
- ✅ Limpa processos antigos na porta 4001
- ✅ Fallback automático para porta 4002 se 4001 estiver ocupada
- ✅ Tratamento de erros

**Uso:**
```batch
scripts\start-backend.bat
```

---

### 3. **scripts/start-frontend.bat**
**Descrição:** Inicia apenas o Frontend React

**Melhorias:**
- ✅ Verifica se Node.js está instalado
- ✅ Instala dependências automaticamente se necessário
- ✅ Tratamento de erros

**Uso:**
```batch
scripts\start-frontend.bat
```

---

### 4. **scripts/run-backend.bat**
**Descrição:** Script simplificado para desenvolvimento do Backend

**Características:**
- Script minimalista para desenvolvimento rápido
- Limpa porta automaticamente

**Uso:**
```batch
scripts\run-backend.bat
```

---

### 5. **scripts/kill_python_backend.bat**
**Descrição:** Encerra processos do Backend na porta 4001

**Melhorias:**
- ✅ Encerra processos Python relacionados
- ✅ Encerra processos na porta 4001
- ✅ Verifica se porta ficou livre
- ✅ Mensagens informativas

**Uso:**
```batch
scripts\kill_python_backend.bat
```

---

### 6. **scripts/run-dev.bat**
**Descrição:** Inicia Backend e Frontend em modo desenvolvimento

**Características:**
- Inicia ambos em janelas separadas
- Ideal para desenvolvimento
- Limpa processos antigos antes de iniciar

**Uso:**
```batch
scripts\run-dev.bat
```

---

## 🔄 Mudanças Principais

### Antes (Java/Spring Boot)
```batch
REM Antigo - Java
set "JAVA_HOME=%ROOT_DIR%\java\jdk-17.0.2"
"%JAVA_HOME%\bin\java.exe" -jar target\etl-dashboard-2.0.0.jar
```

### Agora (Python/FastAPI)
```batch
REM Novo - Python
python app.py
```

---

## 📝 Detalhes das Melhorias

### Verificações de Ambiente
Todos os scripts principais agora verificam:
- ✅ Python 3.9+ instalado
- ✅ Node.js 18+ instalado
- ✅ Portas 4000 e 4001 disponíveis

### Limpeza Automática
- ✅ Encerra processos antigos antes de iniciar
- ✅ Verifica se porta ficou livre
- ✅ Fallback para porta alternativa se necessário

### Tratamento de Erros
- ✅ Mensagens de erro claras
- ✅ Pausa para leitura em caso de erro
- ✅ Códigos de saída apropriados

### Compatibilidade
- ✅ Suporte a caracteres especiais (UTF-8)
- ✅ Caminhos com espaços tratados corretamente
- ✅ Funciona em diferentes versões do Windows

---

## 🚀 Como Usar

### Iniciar Sistema Completo
```batch
INICIAR.bat
```

### Desenvolvimento (Backend e Frontend separados)
```batch
scripts\run-dev.bat
```

### Apenas Backend
```batch
scripts\start-backend.bat
```

### Apenas Frontend
```batch
scripts\start-frontend.bat
```

### Encerrar Processos
```batch
scripts\kill_python_backend.bat
```

---

## 🔍 Verificação de Status

Após iniciar, verifique:

1. **Backend:**
   ```bash
   curl http://localhost:4001/api/health
   ```
   Deve retornar: `{"status":"ok","version":"2.1.0"}`

2. **Frontend:**
   Abra no navegador: `http://localhost:4000`

3. **API Docs:**
   Abra no navegador: `http://localhost:4001/docs`

---

## ⚠️ Observações

### Porta Ocupada
Se a porta 4001 estiver ocupada:
- O script tenta encerrar processos automaticamente
- Se não conseguir, usa porta 4002 automaticamente
- Você pode configurar via variável de ambiente: `set ETL_PORT=4002`

### Dependências
Certifique-se de ter instalado:
- ✅ Python 3.9 ou superior
- ✅ Node.js 18 ou superior
- ✅ Dependências do Backend: `pip install -r backend/requirements.txt`
- ✅ Dependências do Frontend: `npm install` (em `frontend/`)

---

## 📊 Compatibilidade

| Componente | Versão | Status |
|------------|--------|--------|
| **Python** | 3.9+ | ✅ Requerido |
| **Node.js** | 18+ | ✅ Requerido |
| **Windows** | 10/11 | ✅ Testado |
| **FastAPI** | 0.110.0 | ✅ Incluído |
| **React** | 19.2.0 | ✅ Incluído |

---

## ✅ Checklist de Atualização

- [x] INICIAR.bat atualizado
- [x] scripts/start-backend.bat atualizado
- [x] scripts/start-frontend.bat atualizado
- [x] scripts/run-backend.bat atualizado
- [x] scripts/kill_python_backend.bat corrigido
- [x] scripts/run-dev.bat atualizado
- [x] Verificações de ambiente adicionadas
- [x] Tratamento de erros melhorado
- [x] Limpeza automática de processos

---

**Data da Atualização:** 27/12/2025  
**Versão:** 2.1.0  
**Status:** ✅ TODOS OS SCRIPTS ATUALIZADOS E TESTADOS

