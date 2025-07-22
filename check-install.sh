#!/bin/bash

# FinanceiroMax - Script de Verificação e Diagnóstico
# Versão: 1.0 - Diagnóstico completo da instalação
# Repositório: https://github.com/Joelferreira98/GestorFin

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERRO] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[AVISO] $1${NC}"
}

info() {
    echo -e "${BLUE}[INFO] $1${NC}"
}

# Verificar se é root
if [[ $EUID -ne 0 ]]; then
    error "Este script deve ser executado como root (use sudo)"
    exit 1
fi

APP_DIR="/opt/financeiro"
APP_USER="financeiro"
DB_NAME="financeiro"
DB_USER="financeiro"
APP_PORT=5004

log "=== DIAGNÓSTICO DA INSTALAÇÃO FINANCEIRO MAX ==="

# 1. Verificar estrutura de diretórios
log "1. Verificando estrutura de diretórios..."
if [[ -d "$APP_DIR" ]]; then
    info "✓ Diretório da aplicação existe: $APP_DIR"
    ls -la "$APP_DIR" | head -10
else
    error "✗ Diretório da aplicação não existe: $APP_DIR"
fi

if [[ -d "/var/log/financeiro-max" ]]; then
    info "✓ Diretório de logs existe"
else
    warn "✗ Diretório de logs não existe"
fi

# 2. Verificar usuário do sistema
log "2. Verificando usuário do sistema..."
if id "$APP_USER" &>/dev/null; then
    info "✓ Usuário $APP_USER existe"
    id "$APP_USER"
else
    error "✗ Usuário $APP_USER não existe"
fi

# 3. Verificar ambiente Python
log "3. Verificando ambiente Python..."
if [[ -f "$APP_DIR/venv/bin/python" ]]; then
    info "✓ Ambiente virtual existe"
    sudo -u "$APP_USER" "$APP_DIR/venv/bin/python" --version
else
    error "✗ Ambiente virtual não existe"
fi

if [[ -f "$APP_DIR/main.py" ]]; then
    info "✓ Arquivo main.py existe"
else
    error "✗ Arquivo main.py não encontrado"
fi

if [[ -f "$APP_DIR/.env" ]]; then
    info "✓ Arquivo .env existe"
    echo "Configurações principais:"
    grep -E "^(DATABASE_URL|HOST|PORT)" "$APP_DIR/.env" || true
else
    error "✗ Arquivo .env não encontrado"
fi

# 4. Verificar banco MySQL
log "4. Verificando banco MySQL..."
if command -v mysql &>/dev/null; then
    info "✓ MySQL instalado"
    systemctl is-active mysql &>/dev/null && info "✓ MySQL ativo" || warn "✗ MySQL inativo"
    
    # Testar conexão
    if mysql -u "$DB_USER" -p"FinanceiroMax2025!" -e "USE $DB_NAME; SELECT 1;" &>/dev/null; then
        info "✓ Conexão com banco de dados OK"
    else
        error "✗ Falha na conexão com banco de dados"
    fi
else
    error "✗ MySQL não instalado"
fi

# 5. Verificar serviço systemd
log "5. Verificando serviço systemd..."
if [[ -f "/etc/systemd/system/financeiro.service" ]]; then
    info "✓ Arquivo de serviço existe"
    
    systemctl daemon-reload
    
    if systemctl is-enabled financeiro &>/dev/null; then
        info "✓ Serviço habilitado"
    else
        warn "✗ Serviço não habilitado"
    fi
    
    if systemctl is-active financeiro &>/dev/null; then
        info "✓ Serviço ativo"
    else
        error "✗ Serviço inativo"
        echo "Status do serviço:"
        systemctl status financeiro --no-pager -l || true
        echo
        echo "Últimos logs:"
        journalctl -u financeiro -n 10 --no-pager || true
    fi
else
    error "✗ Arquivo de serviço não existe"
fi

# 6. Verificar Nginx
log "6. Verificando Nginx..."
if command -v nginx &>/dev/null; then
    info "✓ Nginx instalado"
    
    # Testar configuração
    if nginx -t &>/dev/null; then
        info "✓ Configuração Nginx OK"
    else
        error "✗ Erro na configuração Nginx"
        nginx -t 2>&1 || true
    fi
    
    if systemctl is-active nginx &>/dev/null; then
        info "✓ Nginx ativo"
    else
        error "✗ Nginx inativo"
        systemctl status nginx --no-pager || true
    fi
    
    # Verificar configuração do site
    if [[ -f "/etc/nginx/sites-available/financeiro" ]]; then
        info "✓ Configuração do site existe"
    else
        error "✗ Configuração do site não existe"
    fi
    
    if [[ -L "/etc/nginx/sites-enabled/financeiro" ]]; then
        info "✓ Site habilitado"
    else
        error "✗ Site não habilitado"
    fi
else
    error "✗ Nginx não instalado"
fi

# 7. Testar conectividade
log "7. Testando conectividade..."

# Testar se a aplicação responde na porta
if curl -s http://localhost:$APP_PORT >/dev/null 2>&1; then
    info "✓ Aplicação respondendo na porta $APP_PORT"
else
    warn "✗ Aplicação não responde na porta $APP_PORT"
fi

# Testar via Nginx
if curl -s http://localhost:80 >/dev/null 2>&1; then
    info "✓ Nginx respondendo na porta 80"
else
    warn "✗ Nginx não responde na porta 80"
fi

# 8. Verificar dependências Python
log "8. Verificando dependências Python..."
if [[ -f "$APP_DIR/venv/bin/pip" ]]; then
    echo "Principais dependências instaladas:"
    sudo -u "$APP_USER" "$APP_DIR/venv/bin/pip" list | grep -E "(Flask|SQLAlchemy|gunicorn)" || true
else
    error "✗ pip não encontrado no ambiente virtual"
fi

# 9. Verificar logs
log "9. Verificando logs recentes..."
if [[ -f "/var/log/financeiro-max/app.log" ]]; then
    info "Últimas 5 linhas do log da aplicação:"
    tail -5 "/var/log/financeiro-max/app.log" 2>/dev/null || true
else
    warn "Log da aplicação não encontrado"
fi

# 10. Resumo e sugestões
log "10. Resumo e Sugestões de Correção..."
echo
echo "=== SUGESTÕES DE CORREÇÃO ==="

# Verificar problemas comuns
PROBLEMS_FOUND=0

if ! systemctl is-active financeiro &>/dev/null; then
    echo "🔧 Para corrigir serviço inativo:"
    echo "   sudo systemctl start financeiro"
    echo "   sudo journalctl -u financeiro -f"
    PROBLEMS_FOUND=1
fi

if ! systemctl is-active nginx &>/dev/null; then
    echo "🔧 Para corrigir Nginx inativo:"
    echo "   sudo systemctl start nginx"
    echo "   sudo nginx -t"
    PROBLEMS_FOUND=1
fi

if ! curl -s http://localhost:$APP_PORT >/dev/null 2>&1; then
    echo "🔧 Para corrigir aplicação não respondendo:"
    echo "   cd $APP_DIR"
    echo "   sudo -u $APP_USER ./venv/bin/python main.py"
    PROBLEMS_FOUND=1
fi

if [[ $PROBLEMS_FOUND -eq 0 ]]; then
    log "✅ Nenhum problema crítico encontrado!"
    echo
    echo "🌐 Acesso ao sistema:"
    echo "• URL: http://$(curl -s ipinfo.io/ip 2>/dev/null || echo 'SEU-IP'):80"
    echo "• Usuário: joel" 
    echo "• Senha: Admin@2025!"
else
    warn "❌ Problemas encontrados. Execute as correções sugeridas acima."
fi

echo
echo "📝 Para monitoramento contínuo:"
echo "• sudo journalctl -u financeiro -f"
echo "• sudo tail -f /var/log/financeiro-max/app.log"
echo "• sudo systemctl status financeiro nginx"