# Correção de Erro na Execução de Scripts ETL

## 🐛 Problema Identificado

Erro ao executar scripts ETL via backend:
```
ERROR [SISTEMA] Erro na execucao:
```

O erro ocorria imediatamente após iniciar a execução, sem mensagem de erro detalhada.

---

## 🔍 Causas Identificadas

### 1. **Formato de Data Incompatível** 🔴 CRÍTICO
**Problema:** O frontend envia datas no formato ISO (`2025-12-19`), mas o `main.py` espera formato brasileiro (`DD/MM/YYYY`).

**Evidência:**
- Comando executado: `--data-inicial 2025-12-19`
- `main.py` linha 302: `datetime.strptime(args.data_inicial, "%d/%m/%Y")`

**Impacto:** Causava `ValueError` ao tentar fazer parse da data.

---

### 2. **Falta de Tratamento de Erros Detalhado** 🟡 IMPORTANTE
**Problema:** Erros ocorrendo antes do processo iniciar não eram capturados adequadamente.

**Impacto:** Mensagens de erro genéricas sem detalhes.

---

### 3. **Stderr Não Capturado Separadamente** 🟡 IMPORTANTE
**Problema:** Stderr era redirecionado para stdout, dificultando diagnóstico de erros Python.

**Impacto:** Erros importantes não eram visíveis nos logs.

---

## ✅ Correções Aplicadas

### 1. **Conversão Automática de Formato de Data**

Adicionado método `_convert_date_format()` no `ETLExecutor`:

```python
def _convert_date_format(self, date_str: str) -> str:
    """
    Converte data de formato ISO (YYYY-MM-DD) para DD/MM/YYYY
    ou mantém o formato se já estiver no formato correto
    """
    # Tenta converter de ISO para DD/MM/YYYY
    # Suporta múltiplos formatos de entrada
    # Se não conseguir, retorna original para main.py tratar
```

**Arquivo:** `backend/services/executor.py`

**Resultado:** Datas são automaticamente convertidas do formato ISO para o formato esperado pelo `main.py`.

---

### 2. **Melhor Tratamento de Erros com Traceback**

```python
except Exception as e:
    error_msg = f"Erro na execucao: {str(e)}\nTraceback: {traceback.format_exc()}"
    logger.error(error_msg)
    await self._send_log(log_callback, "ERROR", "SISTEMA",
                         f"Erro na execucao: {str(e)}")
```

**Resultado:** Erros agora incluem traceback completo para diagnóstico.

---

### 3. **Verificação de Existência do Script**

```python
# Verificar se o script existe
if not os.path.exists(self.main_script):
    error_msg = f"Script nao encontrado: {self.main_script}"
    logger.error(error_msg)
    await self._send_log(log_callback, "ERROR", "SISTEMA", error_msg)
    return False
```

**Resultado:** Erro claro se o script não existir.

---

### 4. **Captura Separada de Stderr**

**Antes:**
```python
stderr=asyncio.subprocess.STDOUT,  # Redirecionado para stdout
```

**Depois:**
```python
stderr=asyncio.subprocess.PIPE,  # Capturado separadamente

# Leitura simultânea de stdout e stderr
async def read_stderr():
    # Loga stderr como erro separadamente
```

**Resultado:** Erros Python aparecem claramente nos logs.

---

### 5. **Leitura Simultânea de Stdout e Stderr**

```python
async def _stream_output(self, log_callback: Callable):
    """Processa output do processo linha a linha"""
    # Lê stdout e stderr simultaneamente com asyncio.gather
    tasks = [
        asyncio.create_task(read_stdout()),
        asyncio.create_task(read_stderr())
    ]
    await asyncio.gather(*tasks, return_exceptions=True)
```

**Resultado:** Melhor captura de todos os outputs do processo.

---

## 📋 Arquivos Modificados

- `backend/services/executor.py`
  - Adicionado `_convert_date_format()` método
  - Melhorado tratamento de erros
  - Separação de stderr
  - Leitura simultânea de stdout/stderr
  - Verificação de existência do script

---

## ✅ Resultados Esperados

### Antes
```
ERROR [SISTEMA] Erro na execucao:
```

### Depois
```
ERROR [SISTEMA] Erro ao iniciar processo: ...
ERROR [STDERR] ValueError: time data '2025-12-19' does not match format '%d/%m/%Y'
```

Ou se o problema for corrigido:
```
INFO [SISTEMA] Iniciando execucao: ...
INFO [QORE] Iniciando execução
```

---

## 🧪 Testes Recomendados

1. **Teste com data ISO:**
   - Enviar: `data_inicial: "2025-12-19"`
   - Verificar se é convertida para: `"19/12/2025"`

2. **Teste com data já no formato correto:**
   - Enviar: `data_inicial: "19/12/2025"`
   - Verificar se é mantida como está

3. **Teste com script inexistente:**
   - Mover `main.py` temporariamente
   - Verificar se erro é reportado claramente

4. **Teste com erro Python:**
   - Introduzir erro sintático no `main.py`
   - Verificar se stderr é capturado

---

## 🚀 Próximos Passos

1. Testar execução com a correção aplicada
2. Verificar logs para confirmar formato de data correto
3. Validar que erros são reportados adequadamente

---

**Data da Correção:** Dezembro 2024  
**Status:** ✅ CORREÇÕES APLICADAS

