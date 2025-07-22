#!/bin/bash

# Script de Deploy/Atualização do FinanceiroMax
# Para uso após instalação inicial

set -e

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log() { echo -e "${GREEN}[$(date +'%H:%M:%S')] $1${NC}"; }
warn() { echo -e "${YELLOW}[AVISO] $1${NC}"; }
error() { echo -e "${RED}[ERRO] $1${NC}"; exit 1; }

# Configurações
APP_DIR="/opt/financeiro-max"
APP_USER="financeiro"
SERVICE_NAME="financeiro-max"

echo "=== FinanceiroMax - Deploy/Atualização ==="

# Verificar se está rodando como usuário correto
if [[ "$USER" == "root" ]]; then
    error "Não execute como root. Use: sudo -u $APP_USER $0"
fi

# Verificar se a aplicação existe
if [[ ! -d "$APP_DIR" ]]; then
    error "Aplicação não encontrada em $APP_DIR. Execute primeiro o install.sh"
fi

cd "$APP_DIR"

# Fazer backup antes da atualização
log "Criando backup..."
BACKUP_DIR="/tmp/financeiro-backup-$(date +%Y%m%d_%H%M%S)"
cp -r "$APP_DIR" "$BACKUP_DIR"
log "Backup criado em: $BACKUP_DIR"

# Parar serviço
log "Parando serviço..."
sudo systemctl stop "$SERVICE_NAME" || warn "Serviço já estava parado"

# Detectar arquivo de requirements
REQUIREMENTS_FILE="requirements.txt"
if [[ -f requirements.production.txt ]]; then
    REQUIREMENTS_FILE="requirements.production.txt"
fi

# Atualizar dependências se requirements mudou
if [[ $REQUIREMENTS_FILE -nt venv/pyvenv.cfg ]] || [[ ! -f venv/pyvenv.cfg ]]; then
    log "Atualizando dependências Python..."
    venv/bin/pip install --upgrade pip
    venv/bin/pip install -r $REQUIREMENTS_FILE
fi

# Executar migrações se necessário
log "Verificando migrações do banco..."
venv/bin/python -c "
from app import app, db
import sys
try:
    with app.app_context():
        # Verificar se tabelas existem e criar se necessário
        db.create_all()
        print('Banco verificado/atualizado com sucesso')
except Exception as e:
    print(f'Erro no banco: {e}')
    sys.exit(1)
"

# Verificar configurações
log "Verificando configurações..."
if [[ ! -f .env ]]; then
    warn "Arquivo .env não encontrado. Copiando exemplo..."
    cp .env.example .env
    warn "Configure o arquivo .env antes de continuar!"
fi

# Coletar arquivos estáticos (se necessário)
if [[ -d static ]]; then
    log "Coletando arquivos estáticos..."
    find static -name "*.pyc" -delete
    find static -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
fi

# Verificar permissões
log "Verificando permissões..."
sudo chown -R "$APP_USER:$APP_USER" "$APP_DIR"
chmod -R 755 static/uploads/ 2>/dev/null || true

# Testar configuração
log "Testando configuração..."
timeout 10 venv/bin/python -c "
from app import app
from models import User
with app.app_context():
    count = User.query.count()
    print(f'Usuários cadastrados: {count}')
" || error "Falha no teste de configuração"

# Reiniciar serviços
log "Reiniciando serviços..."
sudo systemctl start "$SERVICE_NAME"
sudo systemctl reload nginx

# Aguardar inicialização
sleep 5

# Verificar se está rodando
if sudo systemctl is-active --quiet "$SERVICE_NAME"; then
    log "✓ Serviço iniciado com sucesso!"
    
    # Teste de conectividade
    PORT=$(grep "^PORT=" .env 2>/dev/null | cut -d'=' -f2 || echo "5000")
    if curl -s "http://localhost:$PORT/health" >/dev/null; then
        log "✓ Aplicação respondendo corretamente!"
    else
        warn "Aplicação pode estar com problemas de conectividade"
    fi
else
    error "Falha ao iniciar o serviço!"
fi

# Mostrar status
echo
echo "=== STATUS DOS SERVIÇOS ==="
sudo systemctl status "$SERVICE_NAME" --no-pager -l
echo

log "Deploy concluído com sucesso! 🚀"
log "Backup disponível em: $BACKUP_DIR"

# Limpeza de backups antigos (manter últimos 5)
BACKUP_COUNT=$(ls -1 /tmp/financeiro-backup-* 2>/dev/null | wc -l)
if [[ "$BACKUP_COUNT" -gt 5 ]]; then
    log "Removendo backups antigos..."
    ls -t /tmp/financeiro-backup-* | tail -n +6 | xargs rm -rf
fi

echo "Acesse: http://$(hostname -I | awk '{print $1}'):$PORT"