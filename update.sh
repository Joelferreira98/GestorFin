#!/bin/bash

# FinanceiroMax - Script de Atualização
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

# Configurações
REPO_URL="https://github.com/Joelferreira98/GestorFin"
APP_DIR="/opt/financeiro"
BACKUP_DIR="/opt/financeiro-backup-$(date +%Y%m%d_%H%M%S)"
SERVICE_NAME="financeiro"

# Funções de log
log() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

header() {
    echo -e "${BLUE}===================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}===================================${NC}"
    echo
}

# Verificar se é root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "Este script deve ser executado como root (use sudo)"
    fi
}

# Verificar se a aplicação está instalada
check_installation() {
    if [[ ! -d "$APP_DIR" ]]; then
        error "FinanceiroMax não está instalado. Execute install.sh primeiro."
    fi
    
    if ! systemctl list-unit-files | grep -q "$SERVICE_NAME.service"; then
        error "Serviço $SERVICE_NAME não encontrado. Execute install.sh primeiro."
    fi
}

# Verificar atualizações disponíveis
check_updates() {
    header "VERIFICANDO ATUALIZAÇÕES"
    
    log "Verificando repositório remoto..."
    cd "$APP_DIR"
    
    # Fazer fetch das mudanças
    git fetch origin main >/dev/null 2>&1 || error "Erro ao acessar repositório remoto"
    
    # Verificar se há atualizações
    local local_commit=$(git rev-parse HEAD)
    local remote_commit=$(git rev-parse origin/main)
    
    if [[ "$local_commit" == "$remote_commit" ]]; then
        log "✅ Sistema já está na versão mais recente!"
        echo "Commit atual: $(git rev-parse --short HEAD)"
        echo "Última modificação: $(git log -1 --format='%cd' --date=format:'%d/%m/%Y %H:%M')"
        read -p "Deseja forçar a reinstalação? (y/N): " force_update
        if [[ "$force_update" != "y" && "$force_update" != "Y" ]]; then
            exit 0
        fi
    else
        log "🔄 Nova versão disponível!"
        echo "Versão atual: $(git rev-parse --short HEAD)"
        echo "Nova versão: $(git rev-parse --short origin/main)"
        echo
        echo "Alterações:"
        git log --oneline $local_commit..$remote_commit | head -10
    fi
}

# Criar backup da instalação atual
create_backup() {
    header "CRIANDO BACKUP DA INSTALAÇÃO ATUAL"
    
    log "Criando backup em: $BACKUP_DIR"
    cp -r "$APP_DIR" "$BACKUP_DIR"
    
    # Backup das configurações do banco
    if command -v mysqldump >/dev/null 2>&1; then
        log "Criando backup do banco de dados..."
        if mysqldump --single-transaction financeiro > "$BACKUP_DIR/database_backup.sql" 2>/dev/null; then
            log "✅ Backup do banco criado: $BACKUP_DIR/database_backup.sql"
        else
            warn "Não foi possível criar backup do banco de dados"
        fi
    fi
    
    log "✅ Backup criado com sucesso"
}

# Parar serviços para atualização
stop_services() {
    header "PARANDO SERVIÇOS PARA ATUALIZAÇÃO"
    
    log "Parando $SERVICE_NAME..."
    systemctl stop "$SERVICE_NAME" || warn "Erro ao parar $SERVICE_NAME"
    
    log "Parando nginx..."
    systemctl stop nginx || warn "Erro ao parar nginx"
    
    log "✅ Serviços parados"
}

# Atualizar código da aplicação
update_application() {
    header "ATUALIZANDO APLICAÇÃO"
    
    cd "$APP_DIR"
    
    log "Fazendo pull das últimas mudanças..."
    git pull origin main || error "Erro ao atualizar código"
    
    # Verificar se existe requirements atualizado
    if [[ -f "requirements.production.txt" ]]; then
        log "Atualizando dependências Python..."
        pip3 install -r requirements.production.txt || error "Erro ao instalar dependências"
    elif [[ -f "requirements.txt" ]]; then
        log "Atualizando dependências Python..."
        pip3 install -r requirements.txt || error "Erro ao instalar dependências"
    fi
    
    # Ajustar permissões
    chown -R financeiro:financeiro "$APP_DIR"
    chmod +x "$APP_DIR"/*.sh 2>/dev/null || true
    
    log "✅ Aplicação atualizada"
}

# Executar migrações se necessário
run_migrations() {
    header "VERIFICANDO MIGRAÇÕES DO BANCO DE DADOS"
    
    cd "$APP_DIR"
    
    # Verificar se há script de migração
    if [[ -f "migrate.py" ]]; then
        log "Executando migrações do banco..."
        sudo -u financeiro python3 migrate.py || warn "Erro ao executar migrações"
    else
        log "Nenhum script de migração encontrado"
    fi
    
    # Verificar integridade do banco
    if [[ -f "check_db.py" ]]; then
        log "Verificando integridade do banco de dados..."
        sudo -u financeiro python3 check_db.py || warn "Problemas na verificação do banco"
    fi
}

# Atualizar configurações se necessário
update_configurations() {
    header "ATUALIZANDO CONFIGURAÇÕES"
    
    # Verificar se há novas configurações do Nginx
    if [[ -f "$APP_DIR/nginx.conf" ]] && [[ -f "/etc/nginx/sites-available/financeiro" ]]; then
        log "Verificando configurações do Nginx..."
        
        # Comparar arquivos
        if ! cmp -s "$APP_DIR/nginx.conf" "/etc/nginx/sites-available/financeiro"; then
            log "Atualizando configuração do Nginx..."
            cp "$APP_DIR/nginx.conf" "/etc/nginx/sites-available/financeiro"
            nginx -t || error "Erro na configuração do Nginx"
            log "✅ Configuração do Nginx atualizada"
        else
            log "Configuração do Nginx já está atualizada"
        fi
    fi
    
    # Verificar se há novas configurações do systemd
    if [[ -f "$APP_DIR/financeiro.service" ]] && [[ -f "/etc/systemd/system/financeiro.service" ]]; then
        log "Verificando configurações do systemd..."
        
        if ! cmp -s "$APP_DIR/financeiro.service" "/etc/systemd/system/financeiro.service"; then
            log "Atualizando serviço do systemd..."
            cp "$APP_DIR/financeiro.service" "/etc/systemd/system/financeiro.service"
            systemctl daemon-reload
            log "✅ Configuração do systemd atualizada"
        else
            log "Configuração do systemd já está atualizada"
        fi
    fi
}

# Iniciar serviços após atualização
start_services() {
    header "INICIANDO SERVIÇOS"
    
    log "Iniciando nginx..."
    systemctl start nginx || error "Erro ao iniciar nginx"
    
    log "Iniciando $SERVICE_NAME..."
    systemctl start "$SERVICE_NAME" || error "Erro ao iniciar $SERVICE_NAME"
    
    # Aguardar inicialização
    log "Aguardando inicialização..."
    sleep 5
    
    # Verificar se os serviços estão rodando
    if systemctl is-active --quiet nginx && systemctl is-active --quiet "$SERVICE_NAME"; then
        log "✅ Todos os serviços iniciados com sucesso"
    else
        error "Alguns serviços falharam ao iniciar. Verifique os logs."
    fi
}

# Testar a aplicação
test_application() {
    header "TESTANDO APLICAÇÃO ATUALIZADA"
    
    log "Testando conectividade..."
    
    # Testar se a aplicação responde
    local max_attempts=30
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        if curl -s http://localhost:5004/auth/login >/dev/null 2>&1; then
            log "✅ Aplicação respondendo corretamente"
            break
        fi
        
        if [[ $attempt -eq $max_attempts ]]; then
            error "Aplicação não está respondendo após $max_attempts tentativas"
        fi
        
        log "Tentativa $attempt/$max_attempts - aguardando..."
        sleep 2
        ((attempt++))
    done
    
    # Mostrar status dos serviços
    log "Status dos serviços:"
    systemctl is-active nginx && echo "✅ Nginx: Ativo" || echo "❌ Nginx: Inativo"
    systemctl is-active "$SERVICE_NAME" && echo "✅ $SERVICE_NAME: Ativo" || echo "❌ $SERVICE_NAME: Inativo"
}

# Limpeza pós-atualização
cleanup() {
    header "LIMPEZA PÓS-ATUALIZAÇÃO"
    
    log "Limpando cache do sistema..."
    apt-get autoremove -y >/dev/null 2>&1 || true
    apt-get autoclean >/dev/null 2>&1 || true
    
    # Manter apenas os 3 backups mais recentes
    log "Limpando backups antigos..."
    find /opt -name "financeiro-backup-*" -type d | sort | head -n -3 | xargs rm -rf 2>/dev/null || true
    
    log "✅ Limpeza concluída"
}

# Mostrar informações finais
show_final_info() {
    header "ATUALIZAÇÃO CONCLUÍDA COM SUCESSO"
    
    local current_commit=$(cd "$APP_DIR" && git rev-parse --short HEAD)
    local last_change=$(cd "$APP_DIR" && git log -1 --format='%cd' --date=format:'%d/%m/%Y %H:%M')
    
    echo -e "${GREEN}🎉 FinanceiroMax atualizado com sucesso!${NC}"
    echo
    echo "📋 Informações da atualização:"
    echo "• Versão atual: $current_commit"
    echo "• Última modificação: $last_change"
    echo "• Backup criado em: $BACKUP_DIR"
    echo
    echo "🌐 Acesso ao sistema:"
    echo "• URL: http://$(curl -s ipinfo.io/ip):5004"
    echo "• Usuário: joel"  
    echo "• Senha: Admin@2025!"
    echo
    echo "📊 Status dos serviços:"
    systemctl is-active --quiet nginx && echo "✅ Nginx: Ativo" || echo "❌ Nginx: Inativo"
    systemctl is-active --quiet "$SERVICE_NAME" && echo "✅ FinanceiroMax: Ativo" || echo "❌ FinanceiroMax: Inativo"
    echo
    echo "📝 Para verificar logs:"
    echo "• sudo journalctl -u $SERVICE_NAME -f"
    echo "• sudo tail -f /var/log/nginx/error.log"
}

# Função para rollback em caso de erro
rollback() {
    header "EXECUTANDO ROLLBACK"
    
    error "Erro durante a atualização. Executando rollback..."
    
    if [[ -d "$BACKUP_DIR" ]]; then
        log "Restaurando backup..."
        
        systemctl stop "$SERVICE_NAME" 2>/dev/null || true
        systemctl stop nginx 2>/dev/null || true
        
        rm -rf "$APP_DIR"
        mv "$BACKUP_DIR" "$APP_DIR"
        
        systemctl start nginx
        systemctl start "$SERVICE_NAME"
        
        log "✅ Rollback executado. Sistema restaurado para versão anterior."
    else
        error "Backup não encontrado. Rollback não é possível."
    fi
}

# Capturar erros e executar rollback
trap rollback ERR

# Função principal
main() {
    check_root
    check_installation
    
    header "FINANCEIROMAX - SISTEMA DE ATUALIZAÇÃO"
    echo "Repositório: $REPO_URL"
    echo "Diretório: $APP_DIR"
    echo
    
    check_updates
    create_backup
    stop_services
    update_application
    run_migrations
    update_configurations
    start_services
    test_application
    cleanup
    show_final_info
}

# Executar
main "$@"