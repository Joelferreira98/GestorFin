#!/bin/bash

# FinanceiroMax - Script de Resolução de Conflitos Git
# Autor: Sistema FinanceiroMax
# Data: Janeiro 2025

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

warn() {
    echo -e "${YELLOW}[AVISO] $1${NC}"
}

# Verificar se é root
if [[ $EUID -ne 0 ]]; then
    error "Este script deve ser executado como root (use sudo)"
fi

APP_DIR="/opt/financeiro"
APP_USER="financeiro"

log "=== RESOLVENDO CONFLITOS GIT ==="

# Verificar se o diretório existe
if [[ ! -d "$APP_DIR" ]]; then
    error "Diretório $APP_DIR não encontrado"
fi

cd "$APP_DIR"

# Verificar se é um repositório Git
if [[ ! -d ".git" ]]; then
    error "Este não é um repositório Git"
fi

log "Status atual do repositório:"
git status

# Fazer backup dos arquivos modificados
log "Criando backup dos arquivos locais..."
BACKUP_DIR="/tmp/financeiro-backup-$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup de arquivos modificados
if git status --porcelain | grep -q "^ M"; then
    warn "Fazendo backup de arquivos modificados..."
    git status --porcelain | grep "^ M" | cut -c4- | while read file; do
        mkdir -p "$BACKUP_DIR/$(dirname "$file")" 2>/dev/null || true
        cp "$file" "$BACKUP_DIR/$file"
        log "Backup: $file -> $BACKUP_DIR/$file"
    done
fi

# Backup de arquivos não rastreados
if git status --porcelain | grep -q "^??"; then
    warn "Fazendo backup de arquivos não rastreados..."
    git status --porcelain | grep "^??" | cut -c4- | while read file; do
        mkdir -p "$BACKUP_DIR/$(dirname "$file")" 2>/dev/null || true
        cp "$file" "$BACKUP_DIR/$file"
        log "Backup: $file -> $BACKUP_DIR/$file"
    done
fi

log "✅ Backup criado em: $BACKUP_DIR"

# Limpar alterações locais
log "Resetando alterações locais..."

# Remover arquivos não rastreados
if git status --porcelain | grep -q "^??"; then
    warn "Removendo arquivos não rastreados..."
    git clean -fd
fi

# Resetar alterações nos arquivos rastreados
if git status --porcelain | grep -q "^ M"; then
    warn "Resetando alterações em arquivos rastreados..."
    git checkout -- .
fi

# Verificar status após limpeza
log "Status após limpeza:"
git status

# Fazer pull das últimas mudanças
log "Fazendo pull das últimas mudanças..."
sudo -u "$APP_USER" git pull origin main

# Verificar se o pull foi bem-sucedido
if [[ $? -eq 0 ]]; then
    log "✅ Pull realizado com sucesso!"
else
    error "Falha no pull. Verifique os conflitos manualmente."
fi

# Ajustar permissões
log "Ajustando permissões..."
chown -R "$APP_USER:$APP_USER" "$APP_DIR"

# Restaurar arquivos importantes do backup se necessário
log "Verificando arquivos importantes para restaurar..."

# Lista de arquivos que devem ser preservados
PRESERVE_FILES=(".env" "gunicorn.conf.py")

for file in "${PRESERVE_FILES[@]}"; do
    if [[ -f "$BACKUP_DIR/$file" ]] && [[ ! -f "$APP_DIR/$file" ]]; then
        log "Restaurando arquivo importante: $file"
        cp "$BACKUP_DIR/$file" "$APP_DIR/$file"
        chown "$APP_USER:$APP_USER" "$APP_DIR/$file"
    fi
done

# Instalar/atualizar dependências se necessário
if [[ -f "requirements.production.txt" ]] || [[ -f "requirements.txt" ]]; then
    log "Atualizando dependências Python..."
    REQUIREMENTS_FILE=""
    if [[ -f "requirements.production.txt" ]]; then
        REQUIREMENTS_FILE="requirements.production.txt"
    elif [[ -f "requirements.txt" ]]; then
        REQUIREMENTS_FILE="requirements.txt"
    fi
    
    if [[ -n "$REQUIREMENTS_FILE" ]]; then
        sudo -u "$APP_USER" ./venv/bin/pip install -r "$REQUIREMENTS_FILE" --upgrade
    fi
fi

# Reiniciar serviços
log "Reiniciando serviços..."
systemctl daemon-reload
systemctl restart financeiro 2>/dev/null || systemctl restart financeiro-max 2>/dev/null || warn "Serviço não encontrado"
systemctl restart nginx

# Aguardar inicialização
log "Aguardando inicialização..."
sleep 5

# Verificar status dos serviços
log "Verificando status dos serviços..."
if systemctl is-active --quiet nginx; then
    log "✅ Nginx: Ativo"
else
    warn "❌ Nginx: Problema"
fi

if systemctl is-active --quiet financeiro; then
    log "✅ FinanceiroMax: Ativo"
elif systemctl is-active --quiet financeiro-max; then
    log "✅ FinanceiroMax: Ativo (financeiro-max)"
else
    warn "❌ FinanceiroMax: Problema"
fi

# Testar conectividade
log "Testando aplicação..."
if curl -s http://localhost:5004/auth/login >/dev/null 2>&1; then
    log "✅ Aplicação respondendo"
else
    warn "❌ Aplicação não está respondendo"
fi

# Informações finais
log "=== RESOLUÇÃO CONCLUÍDA ==="
echo
echo "📋 Resumo:"
echo "• Backup criado em: $BACKUP_DIR"
echo "• Conflitos resolvidos"
echo "• Código atualizado do repositório"
echo "• Serviços reiniciados"
echo
echo "🌐 Acesso ao sistema:"
echo "• URL: http://$(curl -s ipinfo.io/ip 2>/dev/null || echo 'SEU-IP'):5004"
echo "• Usuário: joel"
echo "• Senha: Admin@2025!"
echo
echo "📝 Para verificar logs:"
echo "• sudo journalctl -u financeiro -f"
echo "• sudo tail -f /var/log/financeiro-max/app.log"
echo
echo "💾 Arquivos importantes salvos em: $BACKUP_DIR"

log "✅ Conflitos resolvidos com sucesso!"