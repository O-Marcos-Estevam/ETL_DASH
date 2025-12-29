# Solução: Porta 4001 Já em Uso

## 🐛 Problema

Erro ao iniciar o backend:
```
ERROR: [Errno 10048] error while attempting to bind on address ('0.0.0.0', 4001): 
normalmente é permitida apenas uma utilização de cada endereço de soquete
```

Isso indica que a porta 4001 já está sendo usada por outro processo (provavelmente uma instância anterior do backend que não foi encerrada corretamente).

---

## ✅ Soluções

### Solução 1: Encerrar Processos na Porta (RECOMENDADO)

Execute o script criado para encerrar processos na porta 4001:

```bash
scripts\kill_python_backend.bat
```

Este script:
- Identifica processos usando a porta 4001
- Encerra esses processos automaticamente
- Verifica se a porta ficou livre

---

### Solução 2: Encerrar Manualmente

1. **Identificar processos:**
```bash
netstat -ano | findstr :4001
```

2. **Encerrar processo específico:**
```bash
taskkill /F /PID <PID_DO_PROCESSO>
```

3. **Ou encerrar todos processos Python:**
```bash
taskkill /F /IM python.exe
```
⚠️ **ATENÇÃO:** Isso encerra TODOS os processos Python em execução.

---

### Solução 3: Usar Outra Porta

Configure uma porta diferente via variável de ambiente:

**Windows (CMD):**
```cmd
set ETL_PORT=4002
python app.py
```

**Windows (PowerShell):**
```powershell
$env:ETL_PORT=4002
python app.py
```

**Linux/Mac:**
```bash
ETL_PORT=4002 python app.py
```

**Lembre-se:** Se mudar a porta do backend, também precisa atualizar o frontend para conectar na nova porta.

---

### Solução 4: Melhoria Aplicada - Verificação Automática

O código agora verifica se a porta está disponível antes de iniciar e exibe uma mensagem útil:

```python
def check_port_available(host: str, port: int) -> bool:
    """Verifica se a porta esta disponivel tentando fazer bind"""
    # Tenta fazer bind na porta
    # Se conseguir, porta esta livre
    # Se nao conseguir, porta ja esta em uso
```

**Arquivo:** `backend/app.py`

**Comportamento:**
- Se porta estiver ocupada: Exibe mensagem de erro e instruções
- Se porta estiver livre: Inicia normalmente

---

## 📋 Arquivos Criados/Modificados

1. **`scripts/kill_python_backend.bat`** - Script para encerrar processos na porta 4001
2. **`scripts/find_port_process.bat`** - Script para identificar processos na porta
3. **`backend/app.py`** - Adicionada verificação de porta antes de iniciar

---

## 🔍 Como Prevenir

### Boas Práticas:

1. **Sempre encerre o backend corretamente:**
   - Use `Ctrl+C` no terminal
   - Não feche o terminal sem encerrar o processo

2. **Use scripts de inicialização:**
   - Use `scripts/start-backend.bat` ou similar
   - Isso garante que processos anteriores sejam encerrados

3. **Verifique processos antes de iniciar:**
   ```bash
   netstat -ano | findstr :4001
   ```

---

## 🚀 Próximos Passos

1. Execute `scripts\kill_python_backend.bat` para limpar processos antigos
2. Tente iniciar o backend novamente: `python app.py`
3. Se ainda houver problemas, use outra porta temporariamente

---

**Status:** ✅ Verificação de porta implementada  
**Scripts:** ✅ Scripts auxiliares criados

