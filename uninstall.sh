#!/bin/bash

# FinanceiroMax - Script de Desinstalação
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

# Funções de log
log() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
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
        exit 1
    fi
}

# Confirmar desinstalação
confirm_uninstall() {
    header "DESINSTALAÇÃO DO FINANCEIRO MAX"
    
    echo -e "${RED}ATENÇÃO: Esta ação irá:${NC}"
    echo "• Parar todos os serviços do FinanceiroMax"
    echo "• Remover arquivos da aplicação"
    echo "• Remover configurações do Nginx"
    echo "• Remover configurações do systemd"
    echo "• Manter o banco de dados MySQL (por segurança)"
    echo
    
    read -p "Tem certeza que deseja desinstalar? Digite 'DESINSTALAR' para confirmar: " confirm
    if [[ "$confirm" != "DESINSTALAR" ]]; then
        log "Desinstalação cancelada pelo usuário"
        exit 0
    fi
}

# Parar serviços
stop_services() {
    header "PARANDO SERVIÇOS"
    
    log "Parando serviço FinanceiroMax..."
    if systemctl is-active --quiet financeiro; then
        systemctl stop financeiro
        log "Serviço FinanceiroMax parado"
    else
        warn "Serviço FinanceiroMax já estava parado"
    fi
    
    log "Parando Nginx..."
    if systemctl is-active --quiet nginx; then
        systemctl stop nginx
        log "Nginx parado"
    else
        warn "Nginx já estava parado"
    fi
}

# Remover configurações do systemd
remove_systemd() {
    header "REMOVENDO CONFIGURAÇÕES DO SYSTEMD"
    
    if [[ -f "/etc/systemd/system/financeiro.service" ]]; then
        log "Removendo serviço financeiro.service..."
        systemctl disable financeiro >/dev/null 2>&1 || true
        rm -f /etc/systemd/system/financeiro.service
        systemctl daemon-reload
        log "Serviço removido com sucesso"
    else
        warn "Arquivo de serviço não encontrado"
    fi
}

# Remover configurações do Nginx
remove_nginx_config() {
    header "REMOVENDO CONFIGURAÇÕES DO NGINX"
    
    # Remover configuração específica do site
    if [[ -f "/etc/nginx/sites-enabled/financeiro" ]]; then
        log "Removendo configuração do site..."
        rm -f /etc/nginx/sites-enabled/financeiro
        rm -f /etc/nginx/sites-available/financeiro
        log "Configuração do site removida"
    fi
    
    # Restaurar configuração padrão do Nginx
    if [[ ! -f "/etc/nginx/sites-enabled/default" ]] && [[ -f "/etc/nginx/sites-available/default" ]]; then
        log "Restaurando configuração padrão do Nginx..."
        ln -s /etc/nginx/sites-available/default /etc/nginx/sites-enabled/default
    fi
    
    # Testar e reiniciar Nginx
    if nginx -t >/dev/null 2>&1; then
        systemctl start nginx
        log "Nginx reiniciado com configuração padrão"
    else
        warn "Erro na configuração do Nginx, mantendo parado"
    fi
}

# Remover arquivos da aplicação
remove_application_files() {
    header "REMOVENDO ARQUIVOS DA APLICAÇÃO"
    
    local app_dir="/opt/financeiro"
    
    if [[ -d "$app_dir" ]]; then
        log "Removendo diretório da aplicação: $app_dir"
        rm -rf "$app_dir"
        log "Arquivos da aplicação removidos"
    else
        warn "Diretório da aplicação não encontrado"
    fi
    
    # Remover logs específicos
    if [[ -d "/var/log/financeiro" ]]; then
        log "Removendo logs da aplicação..."
        rm -rf /var/log/financeiro
        log "Logs removidos"
    fi
}

# Remover usuário do sistema
remove_system_user() {
    header "REMOVENDO USUÁRIO DO SISTEMA"
    
    if id "financeiro" >/dev/null 2>&1; then
        log "Removendo usuário 'financeiro'..."
        userdel -r financeiro 2>/dev/null || userdel financeiro 2>/dev/null || true
        log "Usuário removido"
    else
        warn "Usuário 'financeiro' não encontrado"
    fi
}

# Limpeza final
cleanup() {
    header "LIMPEZA FINAL"
    
    log "Limpando cache do sistema..."
    apt-get autoremove -y >/dev/null 2>&1 || true
    apt-get autoclean >/dev/null 2>&1 || true
    
    log "Removendo arquivos temporários..."
    rm -rf /tmp/financeiro* 2>/dev/null || true
    
    log "Limpeza concluída"
}

# Informações sobre o banco de dados
database_info() {
    header "INFORMAÇÕES SOBRE O BANCO DE DADOS"
    
    echo -e "${YELLOW}IMPORTANTE:${NC}"
    echo "• O banco de dados MySQL foi MANTIDO por segurança"
    echo "• Para remover completamente, execute manualmente:"
    echo "  mysql -u root -p -e \"DROP DATABASE IF EXISTS financeiro;\""
    echo "• Para remover o usuário do banco:"
    echo "  mysql -u root -p -e \"DROP USER IF EXISTS 'financeiro'@'localhost';\""
    echo
    echo -e "${BLUE}Backup recomendado antes de remover o banco:${NC}"
    echo "  mysqldump -u root -p financeiro > backup_financeiro_$(date +%Y%m%d).sql"
}

# Função principal
main() {
    check_root
    confirm_uninstall
    
    log "Iniciando desinstalação do FinanceiroMax..."
    
    stop_services
    remove_systemd
    remove_nginx_config
    remove_application_files
    remove_system_user
    cleanup
    database_info
    
    header "DESINSTALAÇÃO CONCLUÍDA"
    echo -e "${GREEN}✅ FinanceiroMax foi desinstalado com sucesso!${NC}"
    echo
    echo "Componentes removidos:"
    echo "• ✅ Serviços do sistema"
    echo "• ✅ Configurações do Nginx"  
    echo "• ✅ Arquivos da aplicação"
    echo "• ✅ Usuário do sistema"
    echo "• ⚠️  Banco de dados MySQL mantido"
    echo
    echo "Obrigado por usar o FinanceiroMax!"
}

# Executar
main "$@"