#!/bin/bash

# Script para verificar instalação do FinanceiroMax
# Executa testes básicos para validar a instalação

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}✓ $1${NC}"; }
error() { echo -e "${RED}✗ $1${NC}"; }
warn() { echo -e "${YELLOW}⚠ $1${NC}"; }

echo "=== Verificação da Instalação FinanceiroMax ==="

# Configurações
APP_DIR="/opt/financeiro-max"
SERVICE_NAME="financeiro-max"

# 1. Verificar se diretório existe
if [[ -d "$APP_DIR" ]]; then
    log "Diretório da aplicação encontrado"
else
    error "Diretório $APP_DIR não encontrado"
    exit 1
fi

cd "$APP_DIR"

# 2. Verificar arquivo .env
if [[ -f .env ]]; then
    log "Arquivo .env encontrado"
    
    # Verificar variáveis essenciais
    if grep -q "DATABASE_URL=" .env; then
        log "DATABASE_URL configurada"
    else
        warn "DATABASE_URL não encontrada no .env"
    fi
    
    if grep -q "SECRET_KEY=" .env; then
        log "SECRET_KEY configurada"
    else
        warn "SECRET_KEY não encontrada no .env"
    fi
else
    error "Arquivo .env não encontrado"
    exit 1
fi

# 3. Verificar ambiente virtual Python
if [[ -d venv ]] && [[ -f venv/bin/python ]]; then
    log "Ambiente virtual Python encontrado"
    
    # Verificar dependências principais
    if venv/bin/python -c "import flask" 2>/dev/null; then
        log "Flask instalado"
    else
        error "Flask não encontrado"
    fi
    
    if venv/bin/python -c "import sqlalchemy" 2>/dev/null; then
        log "SQLAlchemy instalado"
    else
        error "SQLAlchemy não encontrado"
    fi
else
    error "Ambiente virtual Python não encontrado"
    exit 1
fi

# 4. Verificar banco de dados
log "Testando conexão com banco de dados..."
if venv/bin/python -c "
from app import app, db
try:
    with app.app_context():
        db.engine.execute('SELECT 1')
    print('Conexão OK')
except Exception as e:
    print(f'Erro: {e}')
    exit(1)
" > /dev/null 2>&1; then
    log "Conexão com banco de dados OK"
else
    error "Falha na conexão com banco de dados"
fi

# 5. Verificar serviço systemd
if systemctl is-active --quiet "$SERVICE_NAME"; then
    log "Serviço $SERVICE_NAME ativo"
else
    warn "Serviço $SERVICE_NAME não está ativo"
fi

if systemctl is-enabled --quiet "$SERVICE_NAME"; then
    log "Serviço $SERVICE_NAME habilitado"
else
    warn "Serviço $SERVICE_NAME não está habilitado"
fi

# 6. Verificar Nginx
if systemctl is-active --quiet nginx; then
    log "Nginx ativo"
else
    warn "Nginx não está ativo"
fi

if [[ -f /etc/nginx/sites-enabled/financeiro-max ]]; then
    log "Site Nginx configurado"
else
    warn "Configuração Nginx não encontrada"
fi

# 7. Verificar porta da aplicação
PORT=$(grep "^PORT=" .env 2>/dev/null | cut -d'=' -f2 || echo "5000")
if netstat -tlnp 2>/dev/null | grep -q ":$PORT "; then
    log "Aplicação rodando na porta $PORT"
else
    warn "Porta $PORT não está em uso"
fi

# 8. Teste HTTP
if command -v curl >/dev/null; then
    if curl -s "http://localhost:$PORT/health" >/dev/null 2>&1; then
        log "Endpoint /health respondendo"
    else
        warn "Endpoint /health não responde"
    fi
else
    warn "curl não encontrado, pulando teste HTTP"
fi

# 9. Verificar logs
if [[ -d /var/log/financeiro-max ]]; then
    log "Diretório de logs encontrado"
    
    # Verificar se há logs recentes
    if find /var/log/financeiro-max -name "*.log" -newermt "1 hour ago" | grep -q .; then
        log "Logs recentes encontrados"
    else
        warn "Nenhum log recente encontrado"
    fi
else
    warn "Diretório de logs não encontrado"
fi

# 10. Verificar backups
if [[ -f /usr/local/bin/backup-financeiro.sh ]]; then
    log "Script de backup instalado"
else
    warn "Script de backup não encontrado"
fi

# 11. Verificar permissões
if [[ -O . ]]; then
    log "Permissões de diretório corretas"
else
    warn "Permissões de diretório podem estar incorretas"
fi

# 12. Verificar firewall
if command -v ufw >/dev/null && ufw status | grep -q "Status: active"; then
    log "Firewall UFW ativo"
else
    warn "Firewall UFW não ativo"
fi

# Resumo
echo
echo "=== RESUMO DA VERIFICAÇÃO ==="

# Testar funcionalidade completa
TEST_PASSED=true

if venv/bin/python -c "
from app import app, db
from models import User

try:
    with app.app_context():
        user_count = User.query.count()
        print(f'Usuários cadastrados: {user_count}')
        if user_count > 0:
            admin = User.query.filter_by(is_admin=True).first()
            if admin:
                print(f'Admin encontrado: {admin.email}')
            else:
                print('Nenhum admin encontrado')
        else:
            print('Nenhum usuário cadastrado')
except Exception as e:
    print(f'Erro ao consultar usuários: {e}')
    exit(1)
" 2>/dev/null; then
    log "Sistema funcionando corretamente"
else
    error "Sistema apresenta problemas"
    TEST_PASSED=false
fi

if [[ "$TEST_PASSED" == true ]]; then
    echo
    log "✅ INSTALAÇÃO VERIFICADA COM SUCESSO!"
    echo
    echo "Próximos passos:"
    echo "1. Acesse http://$(hostname -I | awk '{print $1}'):$PORT"
    echo "2. Configure APIs no painel admin se necessário"
    echo "3. Faça backup regular: sudo /usr/local/bin/backup-financeiro.sh"
    echo
else
    echo
    error "❌ PROBLEMAS ENCONTRADOS NA INSTALAÇÃO"
    echo
    echo "Execute para diagnóstico:"
    echo "sudo journalctl -u $SERVICE_NAME -n 20"
    echo "sudo systemctl status $SERVICE_NAME"
    echo
    exit 1
fi