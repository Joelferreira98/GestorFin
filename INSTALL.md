# Guia Completo de Instalação - FinanceiroMax

## Pré-requisitos

### Sistema Operacional Suportado
- **Ubuntu**: 20.04 LTS, 22.04 LTS (recomendado)
- **Debian**: 11 (Bullseye), 12 (Bookworm)
- **CentOS/RHEL**: 8+ (com adaptações)

### Recursos Mínimos da VPS
- **CPU**: 2 cores
- **RAM**: 2GB (recomendado 4GB)
- **Armazenamento**: 20GB SSD
- **Rede**: 100 Mbps

### Acesso Necessário
- Usuário com privilégios sudo
- Acesso SSH à VPS
- Domínio configurado (opcional para SSL)

## Cenários de Instalação

### 1. Servidor Novo (Instalação Completa)

#### Passo 1: Preparar o Servidor
```bash
# Conectar via SSH
ssh usuario@seu-servidor.com

# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar git se necessário
sudo apt install -y git
```

#### Passo 2: Baixar e Executar
```bash
# Clonar repositório
git clone https://github.com/seu-usuario/financeiro-max.git
cd financeiro-max

# Tornar executável e instalar
chmod +x install.sh
./install.sh
```

#### Passo 3: Seguir Assistente Interativo
O script irá solicitar:

1. **Configurações Básicas**
   - Nome do usuário do sistema (padrão: financeiro)
   - Porta da aplicação (padrão: 5000)
   - Domínio/IP do servidor

2. **Banco de Dados**
   - Senha para o usuário do banco
   - Nome do banco (padrão: financeiro_max)

3. **Usuário Administrador**
   - Email do admin
   - Senha (mínimo 8 caracteres)

4. **SSL (Opcional)**
   - Configuração automática do Let's Encrypt

### 2. Servidor com MySQL Existente

#### Quando Usar
- MySQL já instalado e configurado
- Quer instalação mais rápida
- Já tem outros bancos no servidor

#### Executar
```bash
cd financeiro-max
chmod +x install-quick.sh
./install-quick.sh
```

#### Informações Necessárias
- Senha do root do MySQL
- Dados do banco a ser criado
- Configurações da aplicação

## Configurações Avançadas

### Personalizar Porta MySQL
Se MySQL estiver em porta não padrão:

```bash
# Editar antes da instalação
export MYSQL_PORT=3307
./install.sh
```

### Configurar SSL Personalizado
Para usar certificado próprio:

```bash
# Após instalação
sudo cp seu-certificado.crt /etc/ssl/certs/
sudo cp sua-chave.key /etc/ssl/private/

# Editar configuração do Nginx
sudo nano /etc/nginx/sites-available/financeiro-max
```

### Configurar Proxy Reverso
Se usar proxy reverso (Cloudflare, etc.):

```bash
# Adicionar ao .env
echo "TRUSTED_PROXIES=cloudflare" >> /opt/financeiro-max/.env
sudo systemctl restart financeiro-max
```

## Verificação Pós-Instalação

### 1. Status dos Serviços
```bash
sudo systemctl status financeiro-max
sudo systemctl status nginx
sudo systemctl status mysql
```

### 2. Teste de Conectividade
```bash
# Teste local
curl http://localhost:5000/health

# Teste externo
curl http://seu-dominio.com/health
```

### 3. Logs de Verificação
```bash
# Logs da aplicação
sudo journalctl -u financeiro-max -n 20

# Logs do Nginx
sudo tail -f /var/log/nginx/error.log
```

## Configurações Opcionais

### Evolution API (WhatsApp)
1. Acesse o painel admin: `http://seu-dominio.com/admin`
2. Vá na aba "Evolution API"
3. Configure:
   - URL da API
   - Chave de acesso
   - Instância padrão

### OpenAI (IA Financeira)
1. No painel admin, aba "IA Financeira"
2. Insira sua chave da OpenAI
3. Configure parâmetros do modelo

### Personalização Visual
1. No painel admin, aba "Sistema"
2. Upload logo e favicon
3. Configure cores do tema
4. Defina nome personalizado

## Solução de Problemas Comuns

### Erro: "MySQL connection failed"
```bash
# Verificar serviço MySQL
sudo systemctl status mysql

# Verificar configurações
sudo mysql -u root -p
> SHOW DATABASES;
> SELECT User FROM mysql.user;
```

### Erro: "Permission denied"
```bash
# Corrigir permissões
sudo chown -R financeiro:financeiro /opt/financeiro-max
sudo chmod -R 755 /opt/financeiro-max/static
```

### Erro: "Port already in use"
```bash
# Ver o que está usando a porta
sudo netstat -tlnp | grep :5000

# Alterar porta da aplicação
sudo nano /opt/financeiro-max/.env
# Alterar PORT=5000 para PORT=5001
sudo systemctl restart financeiro-max
```

### SSL não funciona
```bash
# Verificar certificados
sudo certbot certificates

# Renovar manualmente
sudo certbot renew --dry-run

# Verificar configuração Nginx
sudo nginx -t
```

## Manutenção e Updates

### Backup Manual
```bash
sudo /usr/local/bin/backup-financeiro.sh
```

### Atualização da Aplicação
```bash
cd /opt/financeiro-max
git pull origin main
sudo -u financeiro ./deploy.sh
```

### Monitoramento
```bash
# Ver recursos
htop
df -h

# Ver conexões ativas
ss -tulpn | grep :5000

# Ver logs em tempo real
sudo journalctl -u financeiro-max -f
```

## Desinstalação

### Remover Aplicação
```bash
sudo systemctl stop financeiro-max nginx
sudo systemctl disable financeiro-max

sudo rm -rf /opt/financeiro-max
sudo rm /etc/systemd/system/financeiro-max.service
sudo rm /etc/nginx/sites-available/financeiro-max
sudo rm /etc/nginx/sites-enabled/financeiro-max

sudo userdel financeiro
```

### Remover Banco (Cuidado!)
```bash
mysql -u root -p
> DROP DATABASE financeiro_max;
> DROP USER 'financeiro_user'@'localhost';
> FLUSH PRIVILEGES;
```

## Suporte

### Documentação
- README.md - Visão geral
- INSTALL.md - Este guia
- Comentários no código

### Logs de Debug
```bash
# Habilitar debug
echo "LOG_LEVEL=DEBUG" >> /opt/financeiro-max/.env
sudo systemctl restart financeiro-max

# Ver logs detalhados
sudo journalctl -u financeiro-max -n 100
```

### Contato
- Issues: GitHub Issues
- Email: suporte@financeiromax.com
- Documentação: Wiki do projeto

---

**Dica**: Sempre faça backup antes de qualquer alteração em produção!