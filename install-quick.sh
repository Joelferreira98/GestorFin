#!/bin/bash

# Script de Instalação Rápida do FinanceiroMax
# Para servidores que já possuem MySQL configurado

set -e

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${GREEN}[$(date +'%H:%M:%S')] $1${NC}"; }
error() { echo -e "${RED}[ERRO] $1${NC}"; exit 1; }
warning() { echo -e "${YELLOW}[AVISO] $1${NC}"; }
info() { echo -e "${BLUE}[INFO] $1${NC}"; }

echo -e "${BLUE}"
cat << "EOF"
  ______ _                          _            __  __           
 |  ____(_)                        (_)          |  \/  |          
 | |__   _ _ __   __ _ _ __   ___ ___ _ _ __ ___   | \  / | __ ___  __
 |  __| | | '_ \ / _` | '_ \ / __/ _ \ | '__/ _ \  | |\/| |/ _` \ \/ /
 | |    | | | | | (_| | | | | (_|  __/ | | | (_) | | |  | | (_| |>  < 
 |_|    |_|_| |_|\__,_|_| |_|\___\___|_|_|  \___/  |_|  |_|\__,_/_/\_\
                                                                     
    Instalação Rápida - MySQL Existente
EOF
echo -e "${NC}"

# Verificar MySQL
if ! command -v mysql &> /dev/null; then
    error "MySQL não está instalado. Use o script install.sh completo."
fi

if ! systemctl is-active --quiet mysql; then
    error "MySQL não está rodando. Inicie o serviço: sudo systemctl start mysql"
fi

log "MySQL detectado e rodando ✓"

# Configurações básicas
read -p "Usuário do sistema (padrão: financeiro): " APP_USER
APP_USER=${APP_USER:-financeiro}

read -p "Porta da aplicação (padrão: 5000): " APP_PORT
APP_PORT=${APP_PORT:-5000}

read -p "Domínio/IP do servidor: " DOMAIN
if [[ -z "$DOMAIN" ]]; then
    error "Domínio é obrigatório!"
fi

# Configuração do banco
echo
echo "=== CONFIGURAÇÃO DO BANCO DE DADOS ==="
read -p "Senha do root do MySQL: " -s MYSQL_ROOT_PASSWORD
echo

read -p "Nome do banco (padrão: financeiro_max): " DB_NAME
DB_NAME=${DB_NAME:-financeiro_max}

read -p "Usuário do banco (padrão: financeiro_user): " DB_USER
DB_USER=${DB_USER:-financeiro_user}

read -p "Senha do usuário do banco: " -s DB_PASSWORD
echo

if [[ -z "$DB_PASSWORD" ]]; then
    error "Senha do banco é obrigatória!"
fi

# Testar conexão MySQL
log "Testando conexão com MySQL..."
if ! mysql -u root -p"$MYSQL_ROOT_PASSWORD" -e "SELECT 1;" &>/dev/null; then
    error "Falha na autenticação MySQL. Verifique a senha do root."
fi

# Atualizar sistema
log "Atualizando sistema..."
sudo apt update

# Instalar apenas dependências necessárias
log "Instalando dependências..."
sudo apt install -y \
    python3 python3-pip python3-venv python3-dev \
    nginx build-essential libmysqlclient-dev pkg-config \
    ufw certbot python3-certbot-nginx

# Criar banco de dados
log "Criando banco de dados..."
mysql -u root -p"$MYSQL_ROOT_PASSWORD" << EOF
CREATE DATABASE IF NOT EXISTS $DB_NAME CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS '$DB_USER'@'localhost' IDENTIFIED BY '$DB_PASSWORD';
GRANT ALL PRIVILEGES ON $DB_NAME.* TO '$DB_USER'@'localhost';
FLUSH PRIVILEGES;
EOF

log "✓ Banco configurado!"

# Criar usuário do sistema
if ! id "$APP_USER" &>/dev/null; then
    sudo useradd -r -s /bin/bash -d /opt/financeiro-max $APP_USER
    log "✓ Usuário $APP_USER criado"
fi

# Configurar aplicação
APP_DIR="/opt/financeiro-max"
sudo mkdir -p $APP_DIR
sudo mkdir -p /var/log/financeiro-max
sudo chown $APP_USER:$APP_USER $APP_DIR /var/log/financeiro-max

# Copiar arquivos
sudo cp -r . $APP_DIR/
cd $APP_DIR

# Python environment
sudo -u $APP_USER python3 -m venv venv
sudo -u $APP_USER $APP_DIR/venv/bin/pip install --upgrade pip

# Escolher arquivo de requirements mais adequado
if [[ -f requirements.production.txt ]]; then
    REQUIREMENTS_FILE="requirements.production.txt"
elif [[ -f requirements.txt ]]; then
    REQUIREMENTS_FILE="requirements.txt"
elif [[ -f requirements-minimal.txt ]]; then
    REQUIREMENTS_FILE="requirements-minimal.txt"
else
    # Criar requirements temporário com versões flexíveis
    sudo -u $APP_USER tee $APP_DIR/requirements-temp.txt > /dev/null << 'EOF'
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
    REQUIREMENTS_FILE="requirements-temp.txt"
fi

log "Instalando dependências Python..."
sudo -u $APP_USER $APP_DIR/venv/bin/pip install -r $REQUIREMENTS_FILE

# Remover arquivo temporário
[[ -f requirements-temp.txt ]] && rm -f requirements-temp.txt

# Criar .env
sudo -u $APP_USER tee $APP_DIR/.env > /dev/null << EOF
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=$(openssl rand -hex 32)
SESSION_SECRET=$(openssl rand -hex 32)
DATABASE_URL=mysql+pymysql://$DB_USER:$DB_PASSWORD@localhost/$DB_NAME
HOST=0.0.0.0
PORT=$APP_PORT
DOMAIN=$DOMAIN
LOG_LEVEL=INFO
EOF

# Inicializar banco
log "Inicializando banco..."
sudo -u $APP_USER $APP_DIR/venv/bin/python -c "
from app import app, db
with app.app_context():
    db.create_all()
"

# Criar admin
echo
read -p "Email do administrador: " ADMIN_EMAIL
read -p "Senha do administrador: " -s ADMIN_PASSWORD
echo

sudo -u $APP_USER $APP_DIR/venv/bin/python -c "
from app import app, db
from models import User, UserPlan
from werkzeug.security import generate_password_hash
from datetime import datetime

with app.app_context():
    admin = User(
        username='admin',
        email='$ADMIN_EMAIL',
        password_hash=generate_password_hash('$ADMIN_PASSWORD'),
        is_admin=True,
        phone_confirmed=True,
        created_at=datetime.utcnow()
    )
    db.session.add(admin)
    db.session.flush()
    
    plan = UserPlan(
        user_id=admin.id,
        plan_name='Premium',
        is_active=True,
        created_at=datetime.utcnow()
    )
    db.session.add(plan)
    db.session.commit()
"

# Configurar systemd
sudo tee /etc/systemd/system/financeiro-max.service > /dev/null << EOF
[Unit]
Description=FinanceiroMax
After=network.target mysql.service

[Service]
Type=notify
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_DIR
Environment=PATH=$APP_DIR/venv/bin
EnvironmentFile=$APP_DIR/.env
ExecStart=$APP_DIR/venv/bin/gunicorn -c gunicorn.conf.py main:app
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Configurar Gunicorn
sudo -u $APP_USER tee $APP_DIR/gunicorn.conf.py > /dev/null << EOF
bind = "0.0.0.0:$APP_PORT"
workers = 2
worker_class = "sync"
timeout = 300
keepalive = 5
preload_app = True
user = "$APP_USER"
group = "$APP_USER"
chdir = "$APP_DIR"
EOF

# Configurar Nginx
sudo tee /etc/nginx/sites-available/financeiro-max > /dev/null << EOF
server {
    listen 80;
    server_name $DOMAIN;

    location /static/ {
        alias $APP_DIR/static/;
        expires 30d;
    }

    location / {
        proxy_pass http://127.0.0.1:$APP_PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        client_max_body_size 10M;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/financeiro-max /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t

# Configurar firewall
sudo ufw --force enable
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'

# Iniciar serviços
sudo systemctl daemon-reload
sudo systemctl enable financeiro-max nginx
sudo systemctl start financeiro-max nginx

sleep 3

if sudo systemctl is-active --quiet financeiro-max; then
    log "✓ Instalação concluída!"
    log "✓ Acesse: http://$DOMAIN"
    log "✓ Admin: $ADMIN_EMAIL"
else
    error "Falha na inicialização!"
fi
EOF