# Guia de Deployment - ETL Dashboard

Este guia explica como fazer deploy do ETL Dashboard em um VPS com AAPanel e Apache.

**Dominio configurado:** `bolaoamericano.com.br`

---

## Requisitos

### Servidor (VPS)
- Ubuntu 22.04 LTS (recomendado)
- Minimo 2GB RAM
- Minimo 2 vCPU
- 20GB de armazenamento

### Software
- AAPanel (painel de controle)
- Apache 2.4
- Docker e Docker Compose
- Git

---

## Passo 1: Preparar o VPS

### 1.1 Instalar AAPanel
```bash
# Conectar via SSH
ssh root@IP_DO_SEU_VPS

# Instalar AAPanel
wget -O install.sh https://www.aapanel.com/script/install_7.0_en.sh && bash install.sh aapanel
```

Apos a instalacao, anote:
- URL do painel (ex: http://IP:8888/xxxxxx)
- Usuario e senha

### 1.2 Instalar componentes no AAPanel

1. Acesse o painel AAPanel
2. Va em **App Store**
3. Instale:
   - Apache 2.4
   - Docker Manager
   - (Opcional) PM2 Manager

### 1.3 Habilitar modulos Apache
```bash
a2enmod proxy proxy_http proxy_wstunnel rewrite headers ssl
systemctl restart apache2
```

---

## Passo 2: Configurar DNS

No painel do seu registrador de dominio (Registro.br, Cloudflare, etc):

| Tipo | Nome | Valor |
|------|------|-------|
| A | @ | IP_DO_VPS |
| A | www | IP_DO_VPS |

Aguarde a propagacao DNS (pode levar ate 24h, geralmente minutos).

---

## Passo 3: Clonar o Projeto

```bash
# Criar diretorio
cd /www/wwwroot/

# Clonar repositorio
git clone https://github.com/SEU_USUARIO/SEU_REPO.git bolaoamericano.com.br

# Entrar no diretorio
cd bolaoamericano.com.br
```

---

## Passo 4: Configurar Variaveis de Ambiente

### 4.1 Gerar chaves seguras (execute localmente primeiro)
```bash
python scripts/generate_key.py
```

### 4.2 Criar arquivo .env no servidor
```bash
nano .env
```

Conteudo:
```env
# Server
ETL_HOST=0.0.0.0
ETL_PORT=4001
ETL_DEBUG=false
ETL_LOG_LEVEL=INFO

# Security (TROQUE PELAS CHAVES GERADAS!)
JWT_SECRET_KEY=sua_chave_jwt_segura_aqui_min_32_chars
ETL_MASTER_KEY=sua_chave_master_gerada_pelo_script

# Auth
AUTH_REQUIRED=true

# CORS
ETL_CORS_ORIGINS=https://bolaoamericano.com.br,https://www.bolaoamericano.com.br

# Frontend
VITE_API_URL=https://bolaoamericano.com.br/api
```

---

## Passo 5: Subir os Containers

```bash
# Build e start
docker compose up -d --build

# Verificar status
docker compose ps

# Ver logs
docker compose logs -f
```

---

## Passo 6: Configurar Site no AAPanel

### 6.1 Adicionar Site
1. AAPanel > **Website** > **Add site**
2. Preencha:
   - Domain: `bolaoamericano.com.br`
   - Webserver: Apache
   - Root directory: `/www/wwwroot/bolaoamericano.com.br/web`
3. Clique em **Submit**

### 6.2 Configurar Apache VirtualHost
1. AAPanel > **Website** > clique no site > **Config**
2. Substitua TODO o conteudo pelo arquivo `deploy/apache-vhost.conf`
3. Clique em **Save**
4. Reinicie Apache: `systemctl restart apache2`

### 6.3 Ativar SSL/HTTPS
1. AAPanel > **Website** > clique no site > **SSL**
2. Selecione **Let's Encrypt**
3. Marque `bolaoamericano.com.br` e `www.bolaoamericano.com.br`
4. Clique em **Apply**
5. Ative **Force HTTPS**

---

## Passo 7: Configuracao Final

### 7.1 Copiar .htaccess
```bash
cp deploy/.htaccess /www/wwwroot/bolaoamericano.com.br/web/
```

### 7.2 Criar usuario admin
```bash
cd /www/wwwroot/bolaoamericano.com.br
docker compose exec backend python scripts/create_admin.py --username admin --password SuaSenhaSegura123!
```

### 7.3 Testar
1. Acesse https://bolaoamericano.com.br
2. Faca login com as credenciais criadas
3. Teste as funcionalidades do ETL

---

## Comandos Uteis

### Docker
```bash
# Ver status dos containers
docker compose ps

# Ver logs em tempo real
docker compose logs -f

# Reiniciar containers
docker compose restart

# Parar containers
docker compose down

# Reconstruir e iniciar
docker compose up -d --build
```

### Atualizacao
```bash
cd /www/wwwroot/bolaoamericano.com.br

# Baixar atualizacoes
git pull

# Reconstruir containers
docker compose up -d --build
```

### Backup
```bash
# Backup dos dados
cp -r /www/wwwroot/bolaoamericano.com.br/data /backup/etl-$(date +%Y%m%d)

# Backup do banco SQLite
docker compose exec backend cp /app/data/tasks.db /app/data/tasks.db.backup
```

---

## Troubleshooting

### 502 Bad Gateway
**Causa:** Backend nao esta rodando

**Solucao:**
```bash
docker compose ps
docker compose logs backend
docker compose restart backend
```

### WebSocket nao conecta
**Causa:** Modulos Apache nao habilitados ou config incorreta

**Solucao:**
```bash
a2enmod proxy_wstunnel
systemctl restart apache2
```

### Certificado SSL invalido
**Causa:** Let's Encrypt expirou

**Solucao:**
1. AAPanel > Website > SSL > Renew

### Login falha
**Causa:** JWT_SECRET_KEY invalida ou usuario nao existe

**Solucao:**
```bash
# Verificar .env
cat .env | grep JWT

# Recriar usuario
docker compose exec backend python scripts/create_admin.py --username admin --password NovaSenha123!
```

### Pagina em branco
**Causa:** Frontend nao foi buildado ou .htaccess ausente

**Solucao:**
```bash
# Verificar se web/ existe
ls -la /www/wwwroot/bolaoamericano.com.br/web/

# Copiar htaccess
cp deploy/.htaccess /www/wwwroot/bolaoamericano.com.br/web/
```

---

## Monitoramento

### UptimeRobot (gratuito)
1. Crie conta em https://uptimerobot.com
2. Adicione monitor HTTP(s) para `https://bolaoamericano.com.br/api/health`
3. Configure alertas por email/Telegram

### Logs
```bash
# Logs do Apache
tail -f /www/wwwlogs/bolaoamericano.com.br-error.log
tail -f /www/wwwlogs/bolaoamericano.com.br-access.log

# Logs do Backend
docker compose logs -f backend
```

---

## Seguranca

### Firewall
Configure no AAPanel > Security > Firewall:
- Porta 80 (HTTP): Aberta
- Porta 443 (HTTPS): Aberta
- Porta 8888 (AAPanel): Restrita ao seu IP
- Porta 4001 (Backend): Fechada externamente (apenas localhost)

### Backups Automaticos
Configure no AAPanel > Cron > Add Task:
```bash
# Diario as 3h
0 3 * * * tar -czf /backup/etl-$(date +\%Y\%m\%d).tar.gz /www/wwwroot/bolaoamericano.com.br/data
```

---

## Custos Estimados

| Item | Custo |
|------|-------|
| VPS 2GB RAM | R$ 25-50/mes |
| Dominio .com.br | R$ 40/ano |
| SSL (Let's Encrypt) | Gratuito |
| AAPanel | Gratuito |

**Total:** ~R$ 30-55/mes
