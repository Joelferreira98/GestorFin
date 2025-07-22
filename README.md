# FinanceiroMax - Sistema Financeiro Completo

## ✅ Status do Sistema

O sistema está **PRONTO PARA PRODUÇÃO** com todas as funcionalidades implementadas:

### 🔧 Problemas Corrigidos
- ✅ **Login funcionando**: Senha admin alterada para "Admin@2025!" 
- ✅ **Configuração de sessão**: Corrigida para HTTP/HTTPS
- ✅ **Rotas organizadas**: Blueprints corretamente registrados
- ✅ **Erros de código**: Todos os conflitos resolvidos

## 🚀 Instalação na VPS

### Instalação Automática (Recomendado)

1. **Instalação inicial**:
```bash
# Baixar e executar o script de instalação
wget -O install.sh https://raw.githubusercontent.com/Joelferreira98/GestorFin/main/install.sh
chmod +x install.sh
sudo ./install.sh
```

2. **Atualização do sistema**:
```bash
# Baixar e executar o script de atualização
wget -O update.sh https://raw.githubusercontent.com/Joelferreira98/GestorFin/main/update.sh
chmod +x update.sh
sudo ./update.sh
```

3. **Correção de Problemas de Instalação**:
```bash
# Se a instalação falhar ou serviços não iniciarem
wget -O install-fix.sh https://raw.githubusercontent.com/Joelferreira98/GestorFin/main/install-fix.sh
chmod +x install-fix.sh
sudo ./install-fix.sh
```

4. **Diagnóstico Completo**:
```bash
# Para diagnóstico detalhado de problemas
wget -O check-install.sh https://raw.githubusercontent.com/Joelferreira98/GestorFin/main/check-install.sh
chmod +x check-install.sh
sudo ./check-install.sh
```

5. **Teste de Dependências**:
```bash
# Para verificar se todas as dependências estão OK
wget -O test-requirements.sh https://raw.githubusercontent.com/Joelferreira98/GestorFin/main/test-requirements.sh
chmod +x test-requirements.sh
sudo ./test-requirements.sh
```

6. **Resolução de Conflitos Git**:
```bash
# Se houver conflitos durante atualizações
wget -O resolve-conflicts.sh https://raw.githubusercontent.com/Joelferreira98/GestorFin/main/resolve-conflicts.sh
chmod +x resolve-conflicts.sh
sudo ./resolve-conflicts.sh
```

7. **Desinstalação (se necessário)**:
```bash
# Baixar e executar o script de desinstalação
wget -O uninstall.sh https://raw.githubusercontent.com/Joelferreira98/GestorFin/main/uninstall.sh
chmod +x uninstall.sh
sudo ./uninstall.sh
```

## 🔧 Instalação Manual (Alternativa)

Para administradores que preferem controle total sobre o processo de instalação:

### Pré-requisitos
- Ubuntu 20.04+ ou Debian 11+
- Acesso root ou sudo
- Porta 80 liberada

### 1. Preparar Sistema
```bash
# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependências
sudo apt install -y python3 python3-pip python3-venv git nginx mysql-server curl openssl
```

### 2. Configurar MySQL
```bash
# Configurar MySQL (pressione Enter para senha root vazia em instalação nova)
sudo mysql_secure_installation

# Criar banco e usuário
sudo mysql -u root -p << 'EOF'
CREATE DATABASE financeiro CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'financeiro'@'localhost' IDENTIFIED BY 'FinanceiroMax2025!';
GRANT ALL PRIVILEGES ON financeiro.* TO 'financeiro'@'localhost';
FLUSH PRIVILEGES;
EXIT;
EOF
```

### 3. Instalar Aplicação
```bash
# Criar usuário do sistema
sudo useradd -r -s /bin/bash -d /opt/financeiro financeiro

# Criar diretórios
sudo mkdir -p /opt/financeiro /var/log/financeiro-max
sudo chown financeiro:financeiro /opt/financeiro /var/log/financeiro-max

# Clonar repositório
git clone https://github.com/Joelferreira98/GestorFin.git /tmp/financeiro-repo
sudo cp -r /tmp/financeiro-repo/* /opt/financeiro/
sudo chown -R financeiro:financeiro /opt/financeiro
rm -rf /tmp/financeiro-repo

# Configurar Python
cd /opt/financeiro
sudo -u financeiro python3 -m venv venv
sudo -u financeiro ./venv/bin/pip install --upgrade pip
sudo -u financeiro ./venv/bin/pip install -r requirements.txt
```

### 4. Configurar Ambiente
```bash
# Criar .env
sudo -u financeiro tee /opt/financeiro/.env > /dev/null << EOF
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=$(openssl rand -hex 32)
SESSION_SECRET=$(openssl rand -hex 32)
DATABASE_URL=mysql+pymysql://financeiro:FinanceiroMax2025!@localhost/financeiro
HOST=0.0.0.0
PORT=5004
EOF
```

### 5. Configurar Serviço
```bash
# Criar serviço systemd
sudo tee /etc/systemd/system/financeiro.service > /dev/null << 'EOF'
[Unit]
Description=FinanceiroMax - Sistema de Gestão Financeira
After=network.target mysql.service
Requires=mysql.service

[Service]
Type=exec
User=financeiro
Group=financeiro
WorkingDirectory=/opt/financeiro
Environment=PATH=/opt/financeiro/venv/bin
EnvironmentFile=/opt/financeiro/.env
ExecStart=/opt/financeiro/venv/bin/gunicorn --bind 0.0.0.0:5004 --reuse-port main:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
```

### 6. Configurar Nginx
```bash
# Remover configuração padrão
sudo rm -f /etc/nginx/sites-enabled/default

# Criar configuração
sudo tee /etc/nginx/sites-available/financeiro > /dev/null << 'EOF'
server {
    listen 80;
    server_name _;

    location /static/ {
        alias /opt/financeiro/static/;
        expires 30d;
    }

    location / {
        proxy_pass http://127.0.0.1:5004;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        client_max_body_size 10M;
    }
}
EOF

# Ativar site
sudo ln -sf /etc/nginx/sites-available/financeiro /etc/nginx/sites-enabled/
sudo nginx -t
```

### 7. Inicializar Sistema
```bash
# Inicializar banco
cd /opt/financeiro
sudo -u financeiro ./venv/bin/python -c "
from app import app, db
with app.app_context():
    db.create_all()
    print('Banco inicializado!')
"

# Criar usuário admin
sudo -u financeiro ./venv/bin/python -c "
from app import app, db
from models import User, UserPlan
from werkzeug.security import generate_password_hash
from datetime import datetime

with app.app_context():
    # Verificar se admin já existe
    admin = User.query.filter_by(username='joel').first()
    if not admin:
        admin = User(
            username='joel',
            email='admin@financeiro.com', 
            password_hash=generate_password_hash('Admin@2025!'),
            is_admin=True,
            phone_confirmed=True,
            created_at=datetime.utcnow()
        )
        db.session.add(admin)
        db.session.flush()
        
        admin_plan = UserPlan(
            user_id=admin.id,
            plan_name='Premium',
            is_active=True,
            created_at=datetime.utcnow()
        )
        db.session.add(admin_plan)
        db.session.commit()
        print('Admin criado: joel / Admin@2025!')
    else:
        print('Admin já existe!')
"

# Iniciar serviços
sudo systemctl daemon-reload
sudo systemctl enable financeiro nginx
sudo systemctl start financeiro nginx

# Verificar status
sudo systemctl status financeiro nginx
```

### 8. Verificar Instalação
```bash
# Testar conectividade
curl -I http://localhost
curl -I http://localhost:5004

# Verificar logs se necessário
sudo journalctl -u financeiro -f
```

8. **Credenciais de Admin**:
   - **Usuário**: `joel`
   - **Senha**: `Admin@2025!`

### 📋 Funcionalidades Prontas

- 🔐 **Autenticação completa** com sistema de sessões
- 👥 **Sistema multi-usuário** com planos Free e Premium
- 💰 **Gestão financeira** (contas a pagar/receber, vendas parceladas)
- 👤 **Gestão de clientes** com validação CPF/CNPJ
- 📱 **Integração WhatsApp** via Evolution API
- 🔔 **Lembretes automáticos** configuráveis
- 🤖 **IA Financeira** com insights preditivos
- 👤 **Perfil de usuário** com upload de fotos
- ⚙️ **Painel administrativo** completo
- 📊 **Dashboard** com estatísticas em tempo real
- 📱 **PWA** (Progressive Web App) funcional

### 🎯 Próximos Passos

1. **Fazer deploy na VPS** com os scripts de instalação
2. **Testar todas as funcionalidades** no ambiente de produção  
3. **Configurar Evolution API** se necessário WhatsApp
4. **Configurar OpenAI** se necessário funcionalidades de IA

### 📞 Suporte

Sistema desenvolvido e testado, pronto para uso em produção!