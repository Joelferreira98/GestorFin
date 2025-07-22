# FinanceiroMax - Sistema de Gestão Financeira Inteligente

Sistema completo de gestão financeira com inteligência artificial, integrações avançadas e interface moderna.

## 🚀 Funcionalidades

### Gestão Financeira
- **Contas a Receber**: Controle completo com vencimentos e status
- **Contas a Pagar**: Gestão de fornecedores e pagamentos
- **Vendas Parceladas**: Sistema público de confirmação digital
- **Dashboard Inteligente**: Métricas em tempo real com gráficos

### Clientes
- **CRUD Completo**: Gestão total de clientes
- **Validação de Documentos**: CPF/CNPJ brasileiros
- **Integração WhatsApp**: Comunicação automatizada

### Inteligência Artificial
- **Predições Financeiras**: Análise de fluxo de caixa até 12 meses
- **Análise de Risco**: Identificação de clientes inadimplentes
- **Insights Estratégicos**: Otimização do negócio com IA

### Sistema Multi-usuário
- **Planos Flexíveis**: Free (limitado) e Premium (ilimitado)
- **Controle de Acesso**: Administradores e usuários regulares
- **Isolamento de Dados**: Segurança por usuário

### Integrações
- **Evolution API**: WhatsApp automatizado
- **OpenAI**: Análises preditivas e insights
- **Lembretes Automáticos**: Notificações personalizáveis

### PWA (Progressive Web App)
- **Funcionalidade Offline**: Service Worker implementado
- **Instalação Nativa**: Comportamento de app móvel
- **Notificações Push**: Lembretes e alertas

## 📋 Requisitos de Sistema

### Produção (VPS)
- **Sistema Operacional**: Ubuntu 20.04+ ou Debian 11+
- **Python**: 3.8+
- **Banco de Dados**: MySQL 8.0+ (recomendado) ou PostgreSQL 12+
- **Servidor Web**: Nginx
- **Memória RAM**: Mínimo 2GB (recomendado 4GB)
- **Armazenamento**: Mínimo 10GB SSD
- **CPU**: 2 cores (recomendado)

### Desenvolvimento
- **Python**: 3.8+
- **SQLite**: Para desenvolvimento local
- **Node.js**: Para ferramentas de build (opcional)

## 🛠️ Instalação

### Instalação Automatizada (VPS)

#### Opção 1: Instalação Completa (Recomendada)
Para servidores novos sem MySQL:

```bash
git clone <repository-url>
cd financeiro-max
chmod +x *.sh
./install.sh
```

#### Opção 2: Instalação Rápida
Para servidores que já possuem MySQL configurado:

```bash
git clone <repository-url>
cd financeiro-max
chmod +x *.sh
./install-quick.sh
```

#### Opção 3: Teste Prévio de Dependências
Para evitar problemas de versão:

```bash
git clone <repository-url>
cd financeiro-max
chmod +x *.sh
./test-requirements.sh  # Testa compatibilidade
./install.sh            # Instala com dependências compatíveis
```

#### Configuração Interativa:
- **Usuário do sistema**: Nome do usuário Linux
- **Porta da aplicação**: Porta interna (padrão: 5000)
- **Domínio/IP**: Endereço público do servidor
- **Credenciais MySQL**: Senha root e dados do banco
- **Administrador**: Email e senha do primeiro usuário admin
- **SSL**: Certificado gratuito via Let's Encrypt (opcional)

### Instalação Manual

#### 1. Preparação do Sistema
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv mysql-server nginx supervisor
```

#### 2. Configuração do MySQL

**Para MySQL existente:**
```bash
python3 mysql_setup.py
```

**Para nova instalação do MySQL:**
```bash
sudo apt install mysql-server
sudo mysql_secure_installation
python3 mysql_setup.py
```

#### 3. Instalação da Aplicação
```bash
# Criar usuário do sistema
sudo useradd -r -s /bin/bash -d /opt/financeiro-max financeiro

# Criar diretórios
sudo mkdir -p /opt/financeiro-max
sudo chown financeiro:financeiro /opt/financeiro-max

# Copiar arquivos
sudo cp -r . /opt/financeiro-max/
cd /opt/financeiro-max

# Ambiente virtual
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 4. Configuração do Ambiente
```bash
# Criar arquivo .env
cp .env.example .env
# Editar .env com suas configurações
```

#### 5. Inicialização do Banco
```bash
python3 -c "from app import app, db; app.app_context().push(); db.create_all()"
```

## ⚙️ Configuração

### Variáveis de Ambiente (.env)

#### Essenciais
```env
# Flask
SECRET_KEY=sua-chave-secreta-muito-forte
SESSION_SECRET=outra-chave-secreta-diferente
FLASK_ENV=production

# Banco de Dados
DATABASE_URL=mysql+pymysql://user:password@localhost/financeiro_max

# Servidor
HOST=0.0.0.0
PORT=5000
DOMAIN=seudominio.com
```

#### Opcionais
```env
# Evolution API (WhatsApp)
EVOLUTION_API_URL=https://api.evolutionapi.com
EVOLUTION_API_KEY=sua-chave-evolution
EVOLUTION_DEFAULT_INSTANCE=sua-instancia

# OpenAI (IA Financeira)
OPENAI_API_KEY=sua-chave-openai

# Logs
LOG_LEVEL=INFO
LOG_FILE=/var/log/financeiro-max/app.log
```

### Configuração do Nginx
```nginx
server {
    listen 80;
    server_name seudominio.com;

    location /static/ {
        alias /opt/financeiro-max/static/;
        expires 30d;
    }

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 🚀 Uso

### Primeiro Acesso
1. Acesse `http://seudominio.com`
2. Registre-se com email e telefone
3. Confirme telefone via WhatsApp
4. Configure APIs no painel admin (se admin)

### Painel Administrativo
- **URL**: `/admin`
- **Funcões**:
  - Gerenciar usuários e planos
  - Configurar APIs (Evolution, OpenAI)
  - Personalizar sistema (nome, logo, cores)
  - Controlar limites de planos

### APIs Configuráveis

#### Evolution API (WhatsApp)
- Envio de lembretes automáticos
- Confirmação de telefone de usuários
- Links públicos para vendas parceladas

#### OpenAI (IA Financeira)
- Predições de fluxo de caixa
- Análise de risco de inadimplência
- Insights estratégicos personalizados

## 📊 Estrutura do Banco de Dados

### Tabelas Principais
- `users` - Usuários do sistema
- `user_plans` - Planos dos usuários
- `clients` - Clientes cadastrados
- `receivables` - Contas a receber
- `payables` - Contas a pagar
- `installment_sales` - Vendas parceladas
- `system_settings` - Configurações do sistema

### Relacionamentos
- Isolamento por `user_id` em todas as tabelas
- Chaves estrangeiras com integridade referencial
- Índices otimizados para consultas frequentes

## 🔧 Manutenção

### Logs do Sistema
```bash
# Logs da aplicação
sudo journalctl -u financeiro-max -f

# Logs do Nginx
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Logs personalizados
tail -f /var/log/financeiro-max/app.log
```

### Backup Automático
```bash
# Executar backup manual
sudo /usr/local/bin/backup-financeiro.sh

# Verificar backups agendados
sudo crontab -l
```

### Monitoramento
```bash
# Status dos serviços
sudo systemctl status financeiro-max
sudo systemctl status nginx
sudo systemctl status mysql

# Uso de recursos
htop
df -h
```

### Comandos Úteis
```bash
# Verificar instalação completa
./check-install.sh

# Atualizar sistema
sudo -u financeiro ./deploy.sh

# Reiniciar aplicação
sudo systemctl restart financeiro-max

# Ver logs em tempo real
sudo journalctl -u financeiro-max -f

# Ver recursos do sistema
htop
df -h

# Ver conexões ativas
ss -tulpn | grep :5000

# Limpar logs antigos
sudo journalctl --vacuum-time=30d
```

## 🛡️ Segurança

### Implementações de Segurança
- **Autenticação**: Sistema de sessões Flask seguro
- **Autorização**: Controle baseado em roles (admin/usuário)
- **Validação**: Sanitização rigorosa de todos os inputs
- **CSRF Protection**: Proteção automática contra ataques CSRF
- **SQL Injection**: ORM SQLAlchemy previne injeções SQL
- **XSS Protection**: Templates Jinja2 com escape automático
- **Firewall**: Configuração automática via UFW
- **SSL/TLS**: HTTPS obrigatório em produção

### Configurações de Segurança Automáticas
- **Firewall UFW**: Liberação apenas das portas necessárias (SSH, HTTP, HTTPS)
- **Headers de Segurança**: X-Frame-Options, X-Content-Type-Options, etc.
- **Cookies Seguros**: HttpOnly, Secure, SameSite configurados
- **Rate Limiting**: Proteção contra força bruta via Nginx
- **Backup Criptografado**: Backups automáticos com rotação

### Recomendações Adicionais
- **Senhas Fortes**: Mínimo 8 caracteres para todas as contas
- **Atualizações**: Sistema de atualizações automáticas de segurança
- **Monitoramento**: Logs de segurança e alertas automáticos
- **Backup 3-2-1**: 3 cópias, 2 mídias, 1 externa
- **Acesso SSH**: Use chaves SSH em vez de senhas quando possível

## 📈 Performance

### Otimizações Implementadas
- **Connection Pooling**: Pool de conexões MySQL configurado
- **Static Files**: Cache de 30 dias para arquivos estáticos
- **Database Indexing**: Índices otimizados nas consultas principais
- **Lazy Loading**: Carregamento sob demanda de recursos
- **Gzip Compression**: Compressão automática pelo Nginx

### Métricas de Performance
- **Tempo de Resposta**: < 200ms para operações básicas
- **Throughput**: > 100 req/s com configuração padrão
- **Uso de Memória**: ~150MB por worker Gunicorn
- **Conexões DB**: Pool de 20 conexões por padrão

## 🔄 Atualizações

### Processo de Atualização
1. **Backup**: Sempre faça backup antes de atualizar
2. **Download**: Baixe a nova versão
3. **Dependências**: Atualize dependências Python
4. **Migrações**: Execute migrações de banco se necessário
5. **Restart**: Reinicie os serviços

### Versionamento
- **Semantic Versioning**: MAJOR.MINOR.PATCH
- **Changelog**: Documentação detalhada de mudanças
- **Backward Compatibility**: Mantida em minor versions

## 🐛 Solução de Problemas

### Problemas Comuns

#### Aplicação não inicia
```bash
# Verificar logs
sudo journalctl -u financeiro-max -n 50

# Verificar configuração
python3 -c "from config import get_config; print(get_config().__dict__)"
```

#### Erro de conexão com banco
```bash
# Testar conexão
python3 mysql_setup.py

# Verificar serviço MySQL
sudo systemctl status mysql
```

#### Problema de permissões
```bash
# Corrigir proprietário
sudo chown -R financeiro:financeiro /opt/financeiro-max

# Corrigir permissões de upload
sudo chmod -R 755 /opt/financeiro-max/static/uploads
```

## 📞 Suporte

### Documentação
- README.md (este arquivo)
- Comentários no código
- Docstrings nas funções

### Logs de Debug
- Configure `LOG_LEVEL=DEBUG` para logs detalhados
- Use `FLASK_DEBUG=True` apenas em desenvolvimento

---

## 📄 Licença

Este projeto é proprietário. Todos os direitos reservados.

## 👥 Contribuição

Para contribuir com o projeto:
1. Fork o repositório
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Abra um Pull Request

---

**FinanceiroMax** - Sistema de Gestão Financeira Inteligente 🚀