#!/bin/bash

# FinanceiroMax - Script de Correção/Instalação
# Versão: 1.5 - Nginx simplificado sem default_server
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
    exit 1
}

# Verificar se é root
if [[ $EUID -ne 0 ]]; then
    error "Este script deve ser executado como root (use sudo)"
fi

# Configurações
APP_USER="financeiro"
APP_DIR="/opt/financeiro"
DB_NAME="financeiro"
DB_USER="financeiro"
DB_PASSWORD="FinanceiroMax2025!"
APP_PORT=5004

log "=== CORREÇÃO DO PROBLEMA DE INSTALAÇÃO ==="

# Parar serviços se estiverem rodando
log "Parando serviços..."
systemctl stop financeiro-max 2>/dev/null || true
systemctl stop nginx 2>/dev/null || true

# Remover diretório problemático
if [[ -d "$APP_DIR" ]]; then
    log "Removendo diretório problemático..."
    rm -rf "$APP_DIR"
fi

# Recriar diretório e usuário se necessário
log "Recriando estrutura..."
mkdir -p "$APP_DIR"
mkdir -p /var/log/financeiro-max

if ! id "$APP_USER" &>/dev/null; then
    useradd -r -s /bin/bash -d "$APP_DIR" "$APP_USER"
fi

# Instalar Git se não estiver instalado
if ! command -v git &>/dev/null; then
    log "Instalando Git..."
    apt-get update
    apt-get install -y git
fi

# Clonar repositório em diretório temporário
log "Clonando repositório GitHub..."
TEMP_DIR="/tmp/financeiro-clone-$$"
git clone https://github.com/Joelferreira98/GestorFin.git "$TEMP_DIR"

# Mover arquivos para diretório final
log "Movendo arquivos para diretório de instalação..."
cp -r "$TEMP_DIR"/* "$APP_DIR"/
cp -r "$TEMP_DIR"/.git "$APP_DIR"/ 2>/dev/null || true

# Limpar diretório temporário
rm -rf "$TEMP_DIR"

# Ajustar todas as permissões
log "Ajustando permissões..."
chown -R "$APP_USER:$APP_USER" "$APP_DIR"
chown -R "$APP_USER:$APP_USER" /var/log/financeiro-max
chmod -R 755 "$APP_DIR"

# Verificar se clone foi bem sucedido
if [[ -f "$APP_DIR/main.py" ]]; then
    log "✅ Repositório clonado com sucesso!"
else
    error "Falha ao clonar repositório"
fi

# Continuar instalação
cd "$APP_DIR"

# Instalar Python e dependências se necessário
if ! command -v python3 &>/dev/null; then
    log "Instalando Python..."
    apt-get install -y python3 python3-pip python3-venv
fi

# Criar ambiente virtual
log "Criando ambiente virtual Python..."
sudo -u "$APP_USER" python3 -m venv venv
sudo -u "$APP_USER" ./venv/bin/pip install --upgrade pip

# Instalar dependências
log "Instalando dependências Python..."
if [[ -f "requirements.production.txt" ]]; then
    sudo -u "$APP_USER" ./venv/bin/pip install -r requirements.production.txt
elif [[ -f "requirements.txt" ]]; then
    sudo -u "$APP_USER" ./venv/bin/pip install -r requirements.txt
else
    # Criar requirements básico
    cat > requirements.txt << EOF
Flask>=3.0.0
Flask-SQLAlchemy>=3.1.0
Flask-Login>=0.6.0
SQLAlchemy>=2.0.0
Werkzeug>=3.0.0
PyMySQL>=1.1.0
gunicorn>=21.0.0
Pillow>=10.0.0
requests>=2.31.0
python-dateutil>=2.8.0
qrcode[pil]>=7.4.0
PyJWT>=2.8.0
email-validator>=2.1.0
APScheduler>=3.10.0
openai>=1.3.0
phonenumbers>=8.13.0
python-dotenv>=1.0.0
cryptography
EOF
    chown "$APP_USER:$APP_USER" requirements.txt
    sudo -u "$APP_USER" ./venv/bin/pip install -r requirements.txt
fi

# Criar arquivo .env
log "Criando configurações..."
sudo -u "$APP_USER" tee .env > /dev/null << EOF
# Configurações do FinanceiroMax
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=$(openssl rand -hex 32)
SESSION_SECRET=$(openssl rand -hex 32)

# Database Configuration
DATABASE_URL=mysql+pymysql://$DB_USER:$DB_PASSWORD@localhost/$DB_NAME

# Server Configuration
HOST=0.0.0.0
PORT=$APP_PORT
DOMAIN=localhost

# MySQL Connection Pool
SQLALCHEMY_ENGINE_OPTIONS_POOL_SIZE=20
SQLALCHEMY_ENGINE_OPTIONS_MAX_OVERFLOW=30
SQLALCHEMY_ENGINE_OPTIONS_POOL_RECYCLE=3600
SQLALCHEMY_ENGINE_OPTIONS_POOL_PRE_PING=True

# Logs
LOG_LEVEL=INFO
LOG_FILE=/var/log/financeiro-max/app.log
EOF

# Criar serviço systemd corrigido
log "Configurando serviço systemd..."
tee /etc/systemd/system/financeiro.service > /dev/null << EOF
[Unit]
Description=FinanceiroMax - Sistema de Gestão Financeira
After=network.target mysql.service
Requires=mysql.service

[Service]
Type=exec
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_DIR
Environment=PATH=$APP_DIR/venv/bin
EnvironmentFile=$APP_DIR/.env
ExecStart=$APP_DIR/venv/bin/gunicorn --bind 0.0.0.0:$APP_PORT --reuse-port --reload main:app
Restart=always
RestartSec=10
KillMode=mixed
TimeoutStopSec=5
StandardOutput=append:/var/log/financeiro-max/app.log
StandardError=append:/var/log/financeiro-max/app.log

[Install]
WantedBy=multi-user.target
EOF

# Configurar Nginx
log "Configurando Nginx..."
if ! command -v nginx &>/dev/null; then
    apt-get install -y nginx
fi

# Remover todas as configurações que podem causar conflito
rm -f /etc/nginx/sites-enabled/default
rm -f /etc/nginx/sites-enabled/financeiro-max
rm -f /etc/nginx/sites-enabled/financeiro
rm -f /etc/nginx/sites-available/financeiro-max
rm -f /etc/nginx/sites-available/financeiro

# Criar configuração simplificada sem default_server
tee /etc/nginx/sites-available/financeiro > /dev/null << EOF
server {
    listen 80;
    server_name _;

    # Static files
    location /static/ {
        alias $APP_DIR/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    # Uploads
    location /uploads/ {
        alias $APP_DIR/static/uploads/;
        expires 7d;
        add_header Cache-Control "public";
    }

    # Main application
    location / {
        proxy_pass http://127.0.0.1:$APP_PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # File upload size
        client_max_body_size 10M;
    }
}
EOF

ln -sf /etc/nginx/sites-available/financeiro /etc/nginx/sites-enabled/financeiro

# Testar configuração Nginx
nginx -t || error "Erro na configuração do Nginx"

# Ativar e iniciar serviços
log "Ativando serviços..."
systemctl daemon-reload
systemctl enable financeiro
systemctl enable nginx

systemctl start nginx
systemctl start financeiro

# Aguardar inicialização
log "Aguardando inicialização dos serviços..."
sleep 10

# Verificar status
if systemctl is-active --quiet nginx && systemctl is-active --quiet financeiro; then
    log "✅ Instalação corrigida com sucesso!"
    echo
    echo "🌐 Acesso ao sistema:"
    echo "• URL: http://$(curl -s ipinfo.io/ip):5004"
    echo "• Usuário: joel"
    echo "• Senha: Admin@2025!"
    echo
    echo "📊 Status dos serviços:"
    systemctl is-active nginx && echo "✅ Nginx: Ativo" || echo "❌ Nginx: Inativo"  
    systemctl is-active financeiro && echo "✅ FinanceiroMax: Ativo" || echo "❌ FinanceiroMax: Inativo"
    echo
    echo "📝 Para verificar logs:"
    echo "• sudo journalctl -u financeiro -f"
    echo "• sudo tail -f /var/log/financeiro-max/app.log"
else
    error "Alguns serviços falharam ao iniciar."
    echo
    echo "🔍 DIAGNÓSTICO AUTOMÁTICO:"
    
    # Verificar status individual
    if ! systemctl is-active --quiet nginx; then
        echo "❌ Nginx falhou ao iniciar"
        echo "Logs do Nginx:"
        journalctl -u nginx -n 5 --no-pager || true
    fi
    
    if ! systemctl is-active --quiet financeiro; then
        echo "❌ FinanceiroMax falhou ao iniciar"
        echo "Logs do FinanceiroMax:"
        journalctl -u financeiro -n 5 --no-pager || true
        
        echo
        echo "🧪 Executando teste de dependências..."
        cd "$APP_DIR"
        sudo -u "$APP_USER" ./venv/bin/python -c "
import sys
try:
    from app import app
    print('✓ Flask app carregado')
except Exception as e:
    print('❌ Erro ao carregar app:', e)
" 2>/dev/null || echo "❌ Erro crítico na aplicação"
    fi
    
    echo
    echo "📋 SCRIPTS DE DIAGNÓSTICO DISPONÍVEIS:"
    echo "• wget -O check-install.sh https://raw.githubusercontent.com/Joelferreira98/GestorFin/main/check-install.sh"
    echo "  chmod +x check-install.sh && sudo ./check-install.sh"
    echo
    echo "• wget -O test-requirements.sh https://raw.githubusercontent.com/Joelferreira98/GestorFin/main/test-requirements.sh"
    echo "  chmod +x test-requirements.sh && sudo ./test-requirements.sh"
fi