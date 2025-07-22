#!/bin/bash

# FinanceiroMax - Script de Correção de Dependências Python
# Resolve problemas de ModuleNotFoundError e ambiente virtual corrompido

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

log "=== CORREÇÃO DE DEPENDÊNCIAS PYTHON ==="

# Verificar diretório
if [[ ! -d "$APP_DIR" ]]; then
    error "Diretório $APP_DIR não encontrado"
    exit 1
fi

cd "$APP_DIR"

# Verificar usuário
if ! id "$APP_USER" &>/dev/null; then
    warn "Usuário $APP_USER não existe, criando..."
    useradd -r -s /bin/bash -d /opt/financeiro financeiro
    chown -R financeiro:financeiro /opt/financeiro
fi

log "1. Removendo ambiente virtual corrompido..."
if [[ -d "venv" ]]; then
    rm -rf venv
    info "Ambiente virtual removido"
fi

log "2. Verificando Python e pip no sistema..."
# Instalar python3-venv se não existir
if ! dpkg -l | grep -q python3-venv; then
    warn "Instalando python3-venv..."
    apt update
    apt install -y python3-venv python3-pip
fi

python3 --version
pip3 --version

log "3. Criando novo ambiente virtual..."
sudo -u "$APP_USER" python3 -m venv venv
info "Ambiente virtual criado"

log "4. Ativando ambiente e atualizando pip..."
sudo -u "$APP_USER" ./venv/bin/pip install --upgrade pip
info "Pip atualizado: $(sudo -u "$APP_USER" ./venv/bin/pip --version)"

log "5. Verificando requirements.txt..."
if [[ ! -f "requirements.txt" ]]; then
    warn "requirements.txt não encontrado, criando com dependências básicas..."
    sudo -u "$APP_USER" tee requirements.txt > /dev/null << 'EOF'
Flask==3.0.0
Flask-SQLAlchemy==3.1.1
PyMySQL==1.1.0
python-dotenv==1.0.0
gunicorn==21.2.0
Werkzeug==3.0.1
cryptography==41.0.8
APScheduler==3.10.4
Pillow==10.1.0
requests==2.31.0
qrcode==7.4.2
email-validator==2.1.0
sqlalchemy==2.0.23
EOF
    info "requirements.txt criado com dependências essenciais"
else
    info "requirements.txt encontrado"
fi

log "6. Instalando dependências..."
sudo -u "$APP_USER" ./venv/bin/pip install -r requirements.txt

log "7. Verificando instalação das dependências principais..."
sudo -u "$APP_USER" ./venv/bin/python -c "
import sys
try:
    import flask
    print('✓ Flask:', flask.__version__)
    
    import sqlalchemy
    print('✓ SQLAlchemy:', sqlalchemy.__version__)
    
    import pymysql
    print('✓ PyMySQL:', pymysql.__version__)
    
    import gunicorn
    print('✓ Gunicorn:', gunicorn.__version__)
    
    from dotenv import load_dotenv
    print('✓ python-dotenv: OK')
    
    print('✓ Todas as dependências principais instaladas com sucesso!')
    
except ImportError as e:
    print('❌ Erro de import:', e)
    sys.exit(1)
"

log "8. Testando import da aplicação..."
if sudo -u "$APP_USER" ./venv/bin/python -c "from app import app; print('✓ App Flask importado com sucesso')" 2>/dev/null; then
    info "Aplicação importada sem erros"
else
    warn "Erro ao importar aplicação, verificando problemas..."
    
    # Verificar se .env existe
    if [[ ! -f ".env" ]]; then
        warn "Arquivo .env não encontrado, criando..."
        sudo -u "$APP_USER" tee .env > /dev/null << EOF
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=$(openssl rand -hex 32)
SESSION_SECRET=$(openssl rand -hex 32)
DATABASE_URL=mysql+pymysql://financeiro:FinanceiroMax2025!@localhost/financeiro
HOST=0.0.0.0
PORT=5004
EOF
        info ".env criado"
    fi
    
    # Testar novamente
    if sudo -u "$APP_USER" ./venv/bin/python -c "from app import app; print('✓ App Flask importado após correção')" 2>/dev/null; then
        info "Aplicação corrigida e funcionando"
    else
        error "Ainda há problemas com a aplicação"
        sudo -u "$APP_USER" ./venv/bin/python -c "from app import app" || true
    fi
fi

log "9. Testando execução da aplicação..."
timeout 5s sudo -u "$APP_USER" ./venv/bin/python main.py &>/dev/null && \
    info "✓ Aplicação inicia sem erros" || \
    warn "⚠ Aplicação pode ter problemas de inicialização (normal para timeout)"

log "10. Reiniciando serviço systemd..."
if [[ -f "/etc/systemd/system/financeiro.service" ]]; then
    systemctl daemon-reload
    systemctl restart financeiro
    sleep 3
    
    if systemctl is-active --quiet financeiro; then
        info "✓ Serviço reiniciado com sucesso"
    else
        warn "Serviço com problemas, verificando logs..."
        journalctl -u financeiro -n 5 --no-pager || true
    fi
else
    warn "Arquivo de serviço systemd não encontrado"
fi

echo
log "=== CORREÇÃO CONCLUÍDA ==="
echo
echo "✅ DEPENDÊNCIAS CORRIGIDAS:"
echo "• Ambiente virtual recriado"
echo "• Todas as dependências Python instaladas"
echo "• Flask e bibliotecas principais funcionando"
echo
echo "🧪 TESTE MANUAL:"
echo "cd /opt/financeiro"
echo "sudo -u financeiro ./venv/bin/python main.py"
echo
echo "📋 PRÓXIMOS PASSOS SE AINDA HOUVER PROBLEMAS:"
echo "• sudo systemctl status financeiro"
echo "• sudo journalctl -u financeiro -f"
echo "• Execute: wget -O check-install.sh https://raw.githubusercontent.com/Joelferreira98/GestorFin/main/check-install.sh && chmod +x check-install.sh && sudo ./check-install.sh"