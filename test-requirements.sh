#!/bin/bash

# Script para testar instalação de dependências
# Resolve problemas de versões incompatíveis

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}✓ $1${NC}"; }
error() { echo -e "${RED}✗ $1${NC}"; }
warn() { echo -e "${YELLOW}⚠ $1${NC}"; }

echo "=== Teste de Dependências FinanceiroMax ==="

# Criar ambiente virtual de teste
TEST_DIR="/tmp/financeiro-test-$(date +%s)"
mkdir -p "$TEST_DIR"
cd "$TEST_DIR"

log "Criando ambiente virtual de teste..."
python3 -m venv test_env
source test_env/bin/activate

# Testar instalação de dependências individuais
log "Testando instalação individual das dependências..."

declare -a PACKAGES=(
    "Flask>=3.0.0"
    "Flask-SQLAlchemy>=3.1.0" 
    "Flask-Login>=0.6.0"
    "SQLAlchemy>=2.0.0"
    "Werkzeug>=3.0.0"
    "PyMySQL>=1.1.0"
    "gunicorn>=21.0.0"
    "Pillow>=10.0.0"
    "requests>=2.31.0"
    "python-dateutil>=2.8.0"
    "qrcode[pil]>=7.4.0"
    "PyJWT>=2.8.0"
    "email-validator>=2.1.0"
    "APScheduler>=3.10.0"
    "openai>=1.3.0"
    "phonenumbers>=8.13.0"
    "python-dotenv>=1.0.0"
    "cryptography"
)

declare -a FAILED_PACKAGES=()
declare -a SUCCESS_PACKAGES=()

for package in "${PACKAGES[@]}"; do
    echo -n "Testando $package... "
    if pip install "$package" >/dev/null 2>&1; then
        echo -e "${GREEN}OK${NC}"
        SUCCESS_PACKAGES+=("$package")
    else
        echo -e "${RED}FALHOU${NC}"
        FAILED_PACKAGES+=("$package")
    fi
done

echo
echo "=== RESULTADO DO TESTE ==="
echo "Pacotes instalados com sucesso: ${#SUCCESS_PACKAGES[@]}"
echo "Pacotes com problemas: ${#FAILED_PACKAGES[@]}"

if [[ ${#FAILED_PACKAGES[@]} -gt 0 ]]; then
    echo
    warn "Pacotes que falharam:"
    for package in "${FAILED_PACKAGES[@]}"; do
        echo "  - $package"
    done
    
    echo
    echo "Criando requirements.txt com pacotes que funcionam..."
    cat > requirements-working.txt << EOF
# FinanceiroMax - Dependências que funcionam neste sistema
EOF
    
    for package in "${SUCCESS_PACKAGES[@]}"; do
        echo "$package" >> requirements-working.txt
    done
    
    # Tentar versões alternativas para pacotes que falharam
    echo
    warn "Tentando versões alternativas para pacotes que falharam..."
    
    for failed_package in "${FAILED_PACKAGES[@]}"; do
        base_package=$(echo "$failed_package" | cut -d'>' -f1 | cut -d'=' -f1)
        echo -n "Tentando instalar $base_package sem restrição de versão... "
        
        if pip install "$base_package" >/dev/null 2>&1; then
            echo -e "${GREEN}OK${NC}"
            echo "$base_package" >> requirements-working.txt
        else
            echo -e "${RED}FALHOU${NC}"
            echo "# $failed_package  # FALHOU - remova # se conseguir resolver" >> requirements-working.txt
        fi
    done
    
    echo
    log "Arquivo 'requirements-working.txt' criado com dependências que funcionam"
    echo "Copie este arquivo para seu projeto:"
    echo "cp $TEST_DIR/requirements-working.txt /caminho/para/seu/projeto/"
    
else
    log "Todas as dependências foram instaladas com sucesso!"
fi

# Testar importação básica
echo
log "Testando importações básicas..."

python -c "
try:
    import flask
    print('✓ Flask OK')
except ImportError as e:
    print(f'✗ Flask falhou: {e}')

try:
    import flask_sqlalchemy
    print('✓ Flask-SQLAlchemy OK')
except ImportError as e:
    print(f'✗ Flask-SQLAlchemy falhou: {e}')

try:
    import pymysql
    print('✓ PyMySQL OK')
except ImportError as e:
    print(f'✗ PyMySQL falhou: {e}')
"

# Limpeza
cd /tmp
deactivate 2>/dev/null || true

echo
echo "=== RECOMENDAÇÕES ==="

if [[ ${#FAILED_PACKAGES[@]} -eq 0 ]]; then
    log "Sistema está pronto para instalação do FinanceiroMax!"
    echo "Execute: ./install.sh"
else
    warn "Algumas dependências podem causar problemas"
    echo "Recomendações:"
    echo "1. Use o arquivo requirements-working.txt gerado"
    echo "2. Ou use requirements-minimal.txt que tem versões mais flexíveis"
    echo "3. Atualize o sistema: sudo apt update && sudo apt upgrade -y"
    echo "4. Instale build tools: sudo apt install build-essential python3-dev"
fi

# Manter arquivo de resultado
if [[ ${#FAILED_PACKAGES[@]} -gt 0 ]] && [[ -f "$TEST_DIR/requirements-working.txt" ]]; then
    cp "$TEST_DIR/requirements-working.txt" /tmp/requirements-working-$(date +%Y%m%d_%H%M%S).txt
    echo "Backup do arquivo salvo em: /tmp/requirements-working-$(date +%Y%m%d_%H%M%S).txt"
fi

rm -rf "$TEST_DIR"

echo "Teste concluído!"