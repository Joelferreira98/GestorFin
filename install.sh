#!/bin/bash

# FinanceiroMax - Script de Instalação Automatizada
# Versão: 1.4 - Método git clone com diretório temporário
# Autor: Sistema FinanceiroMax
# Data: Janeiro 2025
# Repositório: https://github.com/Joelferreira98/GestorFin

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para logging
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERRO] $1${NC}"
    exit 1
}

warning() {
    echo -e "${YELLOW}[AVISO] $1${NC}"
}

info() {
    echo -e "${BLUE}[INFO] $1${NC}"
}

# Banner
echo -e "${BLUE}"
cat << "EOF"
  ______ _                          _            __  __           
 |  ____(_)                        (_)          |  \/  |          
 | |__   _ _ __   __ _ _ __   ___ ___ _ _ __ ___   | \  / | __ ___  __
 |  __| | | '_ \ / _` | '_ \ / __/ _ \ | '__/ _ \  | |\/| |/ _` \ \/ /
 | |    | | | | | (_| | | | | (_|  __/ | | | (_) | | |  | | (_| |>  < 
 |_|    |_|_| |_|\__,_|_| |_|\___\___|_|_|  \___/  |_|  |_|\__,_/_/\_\
                                                                     
    Sistema de Gestão Financeira Inteligente
    Instalação Automatizada para VPS
EOF
echo -e "${NC}"

# Verificar se está rodando como root
if [[ $EUID -eq 0 ]]; then
   error "Este script não deve ser executado como root. Use um usuário com sudo."
fi

# Verificar sistema operacional
if [[ ! -f /etc/os-release ]]; then
    error "Sistema operacional não suportado. Use Ubuntu 20.04+ ou Debian 11+"
fi

source /etc/os-release
if [[ "$ID" != "ubuntu" && "$ID" != "debian" ]]; then
    error "Sistema operacional não suportado. Use Ubuntu 20.04+ ou Debian 11+"
fi

log "Iniciando instalação do FinanceiroMax..."

# Configurações do usuário
echo
echo "=== CONFIGURAÇÃO INICIAL ==="
read -p "Digite o nome do usuário do sistema (padrão: financeiro): " APP_USER
APP_USER=${APP_USER:-financeiro}

read -p "Digite a porta da aplicação (padrão: 5000): " APP_PORT
APP_PORT=${APP_PORT:-5000}

read -p "Digite a senha do banco MySQL (será criada): " -s DB_PASSWORD
echo
if [[ -z "$DB_PASSWORD" ]]; then
    error "Senha do banco é obrigatória!"
fi

# Configuração do MySQL
DB_NAME="financeiro_max"
DB_USER="financeiro_user"

# Diretórios
APP_DIR="/opt/financeiro-max"
SERVICE_DIR="/etc/systemd/system"

log "Configurações:"
info "Usuário: $APP_USER"
info "Porta: $APP_PORT"
info "Banco: $DB_NAME"
info "Diretório: $APP_DIR"

echo
read -p "Continuar com a instalação? (y/N): " CONFIRM
if [[ "$CONFIRM" != "y" && "$CONFIRM" != "Y" ]]; then
    error "Instalação cancelada pelo usuário."
fi

# Atualizar sistema
log "Atualizando sistema..."
sudo apt update && sudo apt upgrade -y

# Verificar se MySQL já está instalado
MYSQL_INSTALLED=false
if command -v mysql &> /dev/null && systemctl is-active --quiet mysql; then
    log "MySQL já está instalado e rodando"
    MYSQL_INSTALLED=true
else
    log "MySQL não encontrado ou não está rodando"
fi

# Instalar dependências básicas
log "Instalando dependências básicas..."
PACKAGES=(
    python3
    python3-pip
    python3-venv
    python3-dev
    nginx
    supervisor
    git
    curl
    wget
    unzip
    build-essential
    libmysqlclient-dev
    pkg-config
    ufw
)

# Adicionar MySQL apenas se não estiver instalado
if [[ "$MYSQL_INSTALLED" == false ]]; then
    PACKAGES+=(mysql-server mysql-client)
fi

sudo apt install -y "${PACKAGES[@]}"

# Configurar MySQL
if [[ "$MYSQL_INSTALLED" == false ]]; then
    log "Configurando MySQL (nova instalação)..."
    sudo systemctl start mysql
    sudo systemctl enable mysql
    
    # Solicitar configuração inicial do MySQL
    log "MySQL foi instalado. Configure a senha do root:"
    sudo mysql_secure_installation
    
    echo
    log "Agora vamos criar o banco de dados e usuário..."
fi

# Obter credenciais do root para criar banco
echo
echo "=== CONFIGURAÇÃO DO BANCO DE DADOS ==="
if [[ "$MYSQL_INSTALLED" == true ]]; then
    info "MySQL já está instalado. Vamos criar o banco de dados e usuário."
fi

read -p "Digite a senha do usuário root do MySQL: " -s MYSQL_ROOT_PASSWORD
echo

# Testar conexão com root
log "Testando conexão com MySQL..."
if ! mysql -u root -p"$MYSQL_ROOT_PASSWORD" -e "SELECT 1;" &>/dev/null; then
    error "Falha na autenticação MySQL. Verifique a senha do root."
fi

# Criar banco e usuário
log "Criando banco de dados..."
mysql -u root -p"$MYSQL_ROOT_PASSWORD" << EOF
CREATE DATABASE IF NOT EXISTS $DB_NAME CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS '$DB_USER'@'localhost' IDENTIFIED BY '$DB_PASSWORD';
GRANT ALL PRIVILEGES ON $DB_NAME.* TO '$DB_USER'@'localhost';
FLUSH PRIVILEGES;
EOF

# Verificar se a criação foi bem-sucedida
log "Testando conexão com novo usuário..."
if mysql -u "$DB_USER" -p"$DB_PASSWORD" -e "USE $DB_NAME; SELECT 1;" &>/dev/null; then
    log "✓ Banco de dados e usuário criados com sucesso!"
else
    error "Falha ao criar banco de dados ou usuário"
fi

# Criar usuário do sistema
log "Criando usuário do sistema..."
if ! id "$APP_USER" &>/dev/null; then
    sudo useradd -r -s /bin/bash -d $APP_DIR $APP_USER
fi

# Criar diretórios
log "Criando estrutura de diretórios..."
sudo mkdir -p $APP_DIR
sudo mkdir -p /var/log/financeiro-max
sudo chown $APP_USER:$APP_USER $APP_DIR
sudo chown $APP_USER:$APP_USER /var/log/financeiro-max

# Clonar aplicação do repositório GitHub
log "Baixando aplicação do repositório..."
TEMP_DIR="/tmp/financeiro-clone-$$"

# Clonar em diretório temporário
log "Clonando repositório em diretório temporário..."
git clone https://github.com/Joelferreira98/GestorFin.git $TEMP_DIR

# Mover arquivos para diretório final
log "Movendo arquivos para diretório de instalação..."
cp -r $TEMP_DIR/* $APP_DIR/
cp -r $TEMP_DIR/.git $APP_DIR/ 2>/dev/null || true

# Limpar diretório temporário
rm -rf $TEMP_DIR

# Ajustar permissões
sudo chown -R $APP_USER:$APP_USER $APP_DIR
cd $APP_DIR

# Criar ambiente virtual
log "Criando ambiente virtual Python..."
sudo -u $APP_USER python3 -m venv venv
sudo -u $APP_USER $APP_DIR/venv/bin/pip install --upgrade pip

# Instalar dependências Python
log "Instalando dependências Python..."

# Escolher arquivo de requirements mais adequado
REQUIREMENTS_FILE=""
if [[ -f requirements.production.txt ]]; then
    REQUIREMENTS_FILE="requirements.production.txt"
elif [[ -f requirements.txt ]]; then
    REQUIREMENTS_FILE="requirements.txt"
elif [[ -f requirements-minimal.txt ]]; then
    REQUIREMENTS_FILE="requirements-minimal.txt"
else
    log "Criando arquivo requirements.txt com versões flexíveis..."
    sudo -u $APP_USER tee $APP_DIR/requirements.txt > /dev/null << 'EOF'
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
    REQUIREMENTS_FILE="requirements.txt"
fi

log "Instalando dependências do arquivo: $REQUIREMENTS_FILE"
sudo -u $APP_USER $APP_DIR/venv/bin/pip install -r $REQUIREMENTS_FILE

# Criar arquivo .env
log "Criando arquivo de configuração..."
sudo -u $APP_USER tee $APP_DIR/.env > /dev/null << EOF
# Configurações do FinanceiroMax
# Gerado automaticamente em $(date)

# Flask Configuration
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

# Evolution API (Configure depois)
EVOLUTION_API_URL=
EVOLUTION_API_KEY=
EVOLUTION_DEFAULT_INSTANCE=

# OpenAI API (Configure depois)
OPENAI_API_KEY=

# Logs
LOG_LEVEL=INFO
LOG_FILE=/var/log/financeiro-max/app.log

# Security
ALLOWED_HOSTS=$DOMAIN,localhost,127.0.0.1
EOF

# Configurar Gunicorn
log "Configurando Gunicorn..."
sudo -u $APP_USER tee $APP_DIR/gunicorn.conf.py > /dev/null << EOF
# Gunicorn configuration
bind = "0.0.0.0:$APP_PORT"
workers = 4
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 300
keepalive = 5
preload_app = True
reload = False

# Logging
accesslog = "/var/log/financeiro-max/gunicorn_access.log"
errorlog = "/var/log/financeiro-max/gunicorn_error.log"
loglevel = "info"
access_log_format = '%h %l %u %t "%r" %s %b "%{Referer}i" "%{User-agent}i" %D'

# Process naming
proc_name = "financeiro-max"

# User and group
user = "$APP_USER"
group = "$APP_USER"

# Directory
chdir = "$APP_DIR"

# Preload
def when_ready(server):
    server.log.info("FinanceiroMax is ready. Listening on: %s", server.address)

def worker_int(worker):
    worker.log.info("worker received INT or QUIT signal")

def pre_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)
EOF

# Criar serviço systemd
log "Configurando serviço systemd..."
sudo tee $SERVICE_DIR/financeiro-max.service > /dev/null << EOF
[Unit]
Description=FinanceiroMax - Sistema de Gestão Financeira
After=network.target mysql.service
Requires=mysql.service

[Service]
Type=notify
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_DIR
Environment=PATH=$APP_DIR/venv/bin
EnvironmentFile=$APP_DIR/.env
ExecStart=$APP_DIR/venv/bin/gunicorn -c gunicorn.conf.py main:app
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=10
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
StandardOutput=append:/var/log/financeiro-max/app.log
StandardError=append:/var/log/financeiro-max/app.log

[Install]
WantedBy=multi-user.target
EOF

# Configurar logrotate
log "Configurando rotação de logs..."
sudo tee /etc/logrotate.d/financeiro-max > /dev/null << EOF
/var/log/financeiro-max/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    copytruncate
    su $APP_USER $APP_USER
}
EOF

# Configurar Nginx
log "Configurando Nginx..."
sudo tee /etc/nginx/sites-available/financeiro-max > /dev/null << EOF
server {
    listen 80 default_server;
    listen [::]:80 default_server;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;

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
        proxy_redirect off;
        proxy_buffering off;
        
        # Timeouts
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
        proxy_read_timeout 300;
        send_timeout 300;
        
        # File upload size
        client_max_body_size 10M;
    }

    # Health check
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
EOF

# Ativar site
sudo ln -sf /etc/nginx/sites-available/financeiro-max /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Testar configuração do Nginx
sudo nginx -t

# Configurar firewall
log "Configurando firewall..."
sudo ufw --force enable
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw allow $APP_PORT

# Inicializar banco de dados
log "Inicializando banco de dados..."
cd $APP_DIR
sudo -u $APP_USER $APP_DIR/venv/bin/python -c "
import sys
try:
    from app import app, db
    with app.app_context():
        db.create_all()
        print('✓ Banco de dados inicializado!')
except Exception as e:
    print(f'Erro na inicialização do banco: {e}')
    sys.exit(1)
"

if [[ $? -ne 0 ]]; then
    error "Falha na inicialização do banco de dados"
fi

# Criar usuário admin inicial
echo
echo "=== USUÁRIO ADMINISTRADOR ==="
read -p "Digite o email do administrador: " ADMIN_EMAIL
if [[ ! "$ADMIN_EMAIL" =~ ^[A-Za-z0-9+_.-]+@([A-Za-z0-9.-]+\.[A-Za-z]{2,})$ ]]; then
    error "Email inválido!"
fi

while true; do
    read -p "Digite a senha do administrador (min 8 caracteres): " -s ADMIN_PASSWORD
    echo
    if [[ ${#ADMIN_PASSWORD} -lt 8 ]]; then
        echo "Senha deve ter pelo menos 8 caracteres!"
        continue
    fi
    read -p "Confirme a senha: " -s ADMIN_PASSWORD_CONFIRM
    echo
    if [[ "$ADMIN_PASSWORD" == "$ADMIN_PASSWORD_CONFIRM" ]]; then
        break
    else
        echo "Senhas não coincidem! Tente novamente."
    fi
done

log "Criando usuário administrador..."
sudo -u $APP_USER $APP_DIR/venv/bin/python -c "
import sys
try:
    from app import app, db
    from models import User, UserPlan
    from werkzeug.security import generate_password_hash
    from datetime import datetime

    with app.app_context():
        # Verificar se admin já existe
        admin = User.query.filter_by(email='$ADMIN_EMAIL').first()
        if admin:
            print('✓ Usuário administrador já existe!')
            sys.exit(0)
        
        # Criar usuário admin
        admin = User(
            username='admin',
            email='$ADMIN_EMAIL',
            password_hash=generate_password_hash('$ADMIN_PASSWORD'),
            is_admin=True,
            phone_confirmed=True,
            created_at=datetime.utcnow()
        )
        db.session.add(admin)
        db.session.flush()  # Para obter o ID
        
        # Criar plano Premium para o admin
        admin_plan = UserPlan(
            user_id=admin.id,
            plan_name='Premium',
            is_active=True,
            created_at=datetime.utcnow()
        )
        db.session.add(admin_plan)
        
        db.session.commit()
        print('✓ Usuário administrador criado com sucesso!')
        
except Exception as e:
    print(f'Erro ao criar administrador: {e}')
    sys.exit(1)
"

if [[ $? -ne 0 ]]; then
    error "Falha ao criar usuário administrador"
fi

# Iniciar serviços
log "Iniciando serviços..."
sudo systemctl daemon-reload
sudo systemctl enable financeiro-max
sudo systemctl start financeiro-max
sudo systemctl enable nginx
sudo systemctl restart nginx

# Verificar status
sleep 5
if sudo systemctl is-active --quiet financeiro-max; then
    log "✓ Serviço FinanceiroMax iniciado com sucesso!"
else
    error "Falha ao iniciar o serviço FinanceiroMax"
fi

if sudo systemctl is-active --quiet nginx; then
    log "✓ Nginx iniciado com sucesso!"
else
    error "Falha ao iniciar o Nginx"
fi

# SSL removido - configuração simplificada para qualquer IP/domínio

# Criar script de backup
log "Criando script de backup..."
sudo tee /usr/local/bin/backup-financeiro.sh > /dev/null << 'EOF'
#!/bin/bash

# Backup do FinanceiroMax
BACKUP_DIR="/backups/financeiro-max"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="financeiro_max"
APP_DIR="/opt/financeiro-max"

mkdir -p $BACKUP_DIR

# Backup do banco
mysqldump -u root $DB_NAME | gzip > "$BACKUP_DIR/db_$DATE.sql.gz"

# Backup dos uploads
tar -czf "$BACKUP_DIR/uploads_$DATE.tar.gz" -C "$APP_DIR" static/uploads/

# Manter apenas os últimos 30 backups
find $BACKUP_DIR -name "*.gz" -mtime +30 -delete

echo "Backup concluído: $DATE"
EOF

sudo chmod +x /usr/local/bin/backup-financeiro.sh
sudo mkdir -p /backups/financeiro-max

# Agendar backup diário
(sudo crontab -l 2>/dev/null; echo "0 2 * * * /usr/local/bin/backup-financeiro.sh >> /var/log/backup.log 2>&1") | sudo crontab -

# Script de monitoramento
sudo tee /usr/local/bin/monitor-financeiro.sh > /dev/null << 'EOF'
#!/bin/bash

SERVICE="financeiro-max"

if ! systemctl is-active --quiet $SERVICE; then
    echo "$(date): Serviço $SERVICE parado. Reiniciando..." >> /var/log/monitor.log
    systemctl start $SERVICE
    
    # Notificar admin (implementar webhook/email se necessário)
fi
EOF

sudo chmod +x /usr/local/bin/monitor-financeiro.sh

# Agendar monitoramento a cada 5 minutos
(sudo crontab -l 2>/dev/null; echo "*/5 * * * * /usr/local/bin/monitor-financeiro.sh") | sudo crontab -

# Finalização
echo
echo "=== INSTALAÇÃO CONCLUÍDA ==="
log "✓ FinanceiroMax instalado com sucesso!"
echo
info "📋 INFORMAÇÕES DO SISTEMA:"
SERVER_IP=$(hostname -I | awk '{print $1}')
info "URL: http://$SERVER_IP:$APP_PORT"
info "Porta interna: $APP_PORT"
info "Usuário admin: $ADMIN_EMAIL"
info "Diretório: $APP_DIR"
info "Logs: /var/log/financeiro-max/"
echo
info "🔧 COMANDOS ÚTEIS:"
info "Ver logs: sudo journalctl -u financeiro-max -f"
info "Reiniciar: sudo systemctl restart financeiro-max"
info "Status: sudo systemctl status financeiro-max"
info "Backup: sudo /usr/local/bin/backup-financeiro.sh"
echo
info "⚙️  PRÓXIMOS PASSOS:"
info "1. Configure as APIs no painel administrativo"
info "2. Configure backup remoto se necessário"
info "3. Monitore os logs regularmente"
echo

log "✓ Acesse: http://$SERVER_IP:$APP_PORT"
info "Para usar com domínio personalizado, configure o Nginx manualmente."

echo
log "Instalação finalizada! 🚀"
EOF