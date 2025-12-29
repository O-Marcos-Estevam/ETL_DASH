# Guia do Usuario - ETL Dashboard

## O que e este sistema?

O **ETL Dashboard** e um programa que automatiza a coleta de dados de varios sistemas financeiros. Em vez de voce entrar manualmente em cada plataforma (AMPLIS, MAPS, FIDC, etc.), baixar arquivos e organiza-los, o sistema faz tudo isso automaticamente.

### O que significa ETL?

**ETL** e uma sigla em ingles que significa:

- **E**xtract (Extrair): Pegar dados de algum lugar
- **T**ransform (Transformar): Organizar e processar esses dados
- **L**oad (Carregar): Salvar os dados no lugar certo

**Exemplo pratico:** O sistema entra no site do MAPS, faz login com sua senha, baixa os relatorios do dia, separa os arquivos por tipo (PDF, Excel) e salva nas pastas corretas. Tudo automaticamente!

---

## Como iniciar o sistema

### Passo 1: Abrir o programa

1. Navegue ate a pasta do sistema (DEV_ETL)
2. De um **duplo clique** no arquivo `INICIAR.bat`
3. Duas janelas pretas (terminal) vao abrir - isso e normal!
4. Aguarde ate aparecer as mensagens de "Backend iniciado" e "Frontend iniciado"

### Passo 2: Acessar a interface

1. Abra seu navegador (Chrome, Edge, Firefox)
2. Digite na barra de endereco: `http://localhost:4000`
3. Pressione Enter
4. A tela do ETL Dashboard vai aparecer

> **Dica:** Voce pode deixar essa pagina salva nos favoritos para facilitar o acesso.

---

## Conhecendo a interface

### Menu lateral (Sidebar)

No lado esquerdo da tela, voce encontra o menu com as paginas:

| Icone | Pagina | O que faz |
|-------|--------|-----------|
| Casa | Dashboard | Visao geral do sistema |
| Engrenagem | ETL | Executar downloads |
| Lista | Logs | Ver o que esta acontecendo |
| Grafico | Portfolio | Graficos de dados |
| Configuracao | Settings | Configurar senhas e pastas |

### Cabecalho (Header)

No topo da tela voce encontra:
- Nome da pagina atual
- Botao de tema (sol/lua) para mudar entre modo claro e escuro

---

## Pagina ETL - Executando Downloads

Esta e a pagina principal onde voce executa a coleta de dados.

### Entendendo os cards de sistemas

Cada sistema aparece como um "cartao" (card) na tela:

```
┌─────────────────────────────────────┐
│  [Icone]  MAPS                      │
│  MAPS - Ativos e Passivos           │
│                                     │
│  [Toggle Ativo/Inativo]             │
│                                     │
│  Opcoes:                            │
│  [x] PDF  [x] Excel                 │
│                                     │
│  Status: Aguardando                 │
└─────────────────────────────────────┘
```

**O que cada parte significa:**

- **Toggle Ativo/Inativo**: Liga ou desliga o sistema para execucao
- **Opcoes (PDF, Excel, CSV)**: Escolha quais tipos de arquivo baixar
- **Status**: Mostra se esta aguardando, executando ou se deu erro

### Sistemas disponiveis

| Sistema | O que baixa |
|---------|-------------|
| AMPLIS REAG | Carteiras, cotas e aplicacoes da conta REAG |
| AMPLIS Master | Carteiras, cotas e aplicacoes da conta Master |
| MAPS | Ativos, passivos e rentabilidade |
| FIDC | Relatorios de estoque FIDC |
| JCOT | Posicoes de cotistas |
| Britech | Dados financeiros |
| QORE | Carteiras em PDF e Excel |
| Trustee | Script externo |

### Como executar uma coleta

1. **Selecione o periodo:**
   - No topo da pagina, escolha a data inicial e final
   - Se deixar em branco, usa as datas padrao

2. **Ative os sistemas desejados:**
   - Clique no toggle de cada sistema que deseja executar
   - Sistemas desativados (cinza) serao ignorados

3. **Escolha as opcoes:**
   - Marque quais tipos de arquivo deseja (PDF, Excel, CSV)

4. **Clique em "Executar":**
   - O botao verde no final da pagina
   - O sistema vai iniciar a coleta

5. **Acompanhe o progresso:**
   - Os status dos cards vao mudar para "Executando"
   - Voce pode ver os detalhes na pagina de Logs

### Botoes de acao

| Botao | Cor | Funcao |
|-------|-----|--------|
| Ativar Todos | Azul | Liga todos os sistemas de uma vez |
| Desativar Todos | Cinza | Desliga todos os sistemas |
| Executar | Verde | Inicia a coleta de dados |
| Cancelar | Vermelho | Para a execucao (aparece durante execucao) |

---

## Pagina de Logs - Acompanhando a Execucao

Aqui voce ve em tempo real o que o sistema esta fazendo.

### Tipos de mensagens

As mensagens tem cores diferentes conforme a importancia:

| Cor | Tipo | Significado |
|-----|------|-------------|
| Cinza | DEBUG | Detalhes tecnicos (pode ignorar) |
| Azul | INFO | Informacoes normais |
| Amarelo | WARNING | Avisos (algo pode estar errado) |
| Vermelho | ERROR | Erro! Algo deu errado |

### Filtros

No topo da pagina de logs voce pode:
- **Filtrar por sistema**: Ver logs apenas de um sistema especifico
- **Filtrar por nivel**: Ver apenas erros, por exemplo
- **Pausar/Continuar**: Para de atualizar para ler com calma

### Exemplo de log

```
10:30:15 [INFO] [MAPS] Iniciando login...
10:30:18 [INFO] [MAPS] Login realizado com sucesso
10:30:20 [INFO] [MAPS] Navegando para relatorios...
10:30:25 [INFO] [MAPS] Baixando arquivo: Carteira_15012024.xlsx
10:30:45 [INFO] [MAPS] Download concluido!
10:30:46 [INFO] [MAPS] Movendo arquivos para pasta destino...
10:30:48 [INFO] [MAPS] Processo finalizado com sucesso!
```

---

## Pagina de Configuracoes (Settings)

Aqui voce configura senhas e caminhos de arquivos.

### Aba Credenciais

Configure as senhas de cada sistema:

1. Selecione o sistema no dropdown
2. Preencha:
   - **URL**: Endereco do site (normalmente ja vem preenchido)
   - **Usuario**: Seu login
   - **Senha**: Sua senha
3. Clique em "Salvar"

> **Importante:** As senhas sao salvas de forma segura e nao aparecem na tela depois de salvas (aparecem como ********).

### Aba Caminhos

Configure onde os arquivos serao salvos:

| Campo | Descricao |
|-------|-----------|
| CSV | Pasta para arquivos CSV |
| PDF | Pasta para arquivos PDF |
| MAPS | Pasta especifica para dados MAPS |
| FIDC | Pasta para relatorios FIDC |
| JCOT | Pasta para arquivos JCOT |
| Britech | Pasta para dados Britech |
| QORE Excel | Pasta para Excel do QORE |

**Exemplo de caminho:**
```
C:\Dados\Fundos\CSV
```

### Aba Fundos

Selecione quais fundos devem ser processados:
- Marque "Usar todos os fundos" para processar todos
- Ou selecione manualmente os fundos desejados

---

## Resolucao de Problemas

### O sistema nao inicia

**Sintomas:** A janela preta fecha imediatamente ou da erro.

**Solucoes:**
1. Verifique se o Python esta instalado
2. Verifique se o Node.js esta instalado
3. Tente executar como administrador (botao direito > Executar como admin)

### Erro de login em algum sistema

**Sintomas:** Log mostra "Erro de login" ou "Credenciais invalidas".

**Solucoes:**
1. Va em Settings > Credenciais
2. Verifique se usuario e senha estao corretos
3. Teste o login manualmente no site para confirmar
4. Verifique se sua senha nao expirou

### Download nao funciona

**Sintomas:** O sistema faz login mas nao baixa arquivos.

**Solucoes:**
1. Verifique se as pastas de destino existem
2. Verifique se voce tem permissao de escrita nas pastas
3. Verifique se o Chrome esta instalado

### Arquivos baixados estao vazios

**Sintomas:** Os arquivos sao criados mas estao vazios.

**Solucoes:**
1. Verifique se o periodo selecionado tem dados
2. Tente baixar manualmente no site para comparar
3. Verifique os logs para mensagens de erro

### Pagina nao abre no navegador

**Sintomas:** Erro "Nao foi possivel acessar este site".

**Solucoes:**
1. Verifique se as janelas pretas (terminal) estao abertas
2. Aguarde alguns segundos e tente novamente
3. Tente outro navegador
4. Verifique se a porta 4000 nao esta bloqueada

---

## Dicas Uteis

### Atalhos de produtividade

- **Ativar varios sistemas:** Use "Ativar Todos" e depois desative so o que nao precisa
- **Ver erros rapidamente:** Na pagina de Logs, filtre por "ERROR"
- **Tema escuro:** Clique no icone de lua para nao cansar a vista

### Boas praticas

1. **Execute fora do horario comercial:** Os sites podem estar mais lentos durante o dia
2. **Verifique os logs apos execucao:** Mesmo que apareca "sucesso", confira se tudo foi baixado
3. **Mantenha as senhas atualizadas:** Quando trocar senha em algum sistema, atualize aqui tambem
4. **Nao feche as janelas pretas:** Isso para o sistema

### O que fazer se algo der errado

1. **Nao entre em panico!** Os dados originais nos sites nao sao afetados
2. **Verifique os logs** para entender o que aconteceu
3. **Tente executar novamente** apenas o sistema que falhou
4. **Se persistir**, entre em contato com o suporte tecnico

---

## Perguntas Frequentes

### Posso usar o computador enquanto o ETL roda?

**Sim**, mas com cuidados:
- Nao mexa nas janelas do Chrome que o sistema abrir
- Evite abrir muitos programas pesados
- Nao mova ou renomeie as pastas de destino durante execucao

### Quanto tempo demora a execucao?

Depende dos sistemas selecionados:
- AMPLIS: 2-5 minutos
- MAPS: 5-15 minutos (depende da quantidade de fundos)
- FIDC: 3-10 minutos
- QORE: 10-30 minutos (muitos arquivos)

### Posso executar mais de uma vez no mesmo dia?

**Sim!** O sistema sobrescreve arquivos com mesmo nome. Util se algum download falhou.

### Os dados sao enviados para algum lugar?

**Nao.** Todos os dados ficam apenas no seu computador, nas pastas configuradas. O sistema nao envia nada para a internet (apenas acessa os sites para baixar).

### Preciso de internet?

**Sim.** O sistema precisa acessar os sites das plataformas financeiras.

---

## Glossario

| Termo | Significado |
|-------|-------------|
| Backend | Parte do sistema que processa dados (voce nao ve) |
| Frontend | Parte visual do sistema (o que voce ve no navegador) |
| API | Como o frontend conversa com o backend |
| WebSocket | Tecnologia para atualizacoes em tempo real |
| Job | Uma execucao de coleta de dados |
| Pipeline | Sequencia de passos que o sistema executa |
| Log | Registro do que o sistema esta fazendo |
| Selenium | Ferramenta que controla o navegador automaticamente |
| Toggle | Botao de liga/desliga |
| CSV | Arquivo de dados (abre no Excel) |
| JSON | Formato de configuracao (arquivo de texto especial) |

---

## Suporte

Se voce encontrar problemas que nao consegue resolver:

1. Anote a mensagem de erro exata
2. Tire um print da tela de logs
3. Anote qual sistema estava executando
4. Entre em contato com a equipe de TI

---

*Ultima atualizacao: Dezembro 2024*
