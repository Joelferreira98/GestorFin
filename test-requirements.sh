#!/bin/bash

# FinanceiroMax - Teste de Dependências
# Diagnóstico rápido para resolver falhas de inicialização

set -e

APP_DIR="/opt/financeiro"
APP_USER="financeiro"

echo "=== TESTE DE DEPENDÊNCIAS PYTHON ==="

if [[ ! -d "$APP_DIR" ]]; then
    echo "❌ Diretório $APP_DIR não existe"
    exit 1
fi

cd "$APP_DIR"

if [[ ! -f "venv/bin/python" ]]; then
    echo "❌ Ambiente virtual não existe"
    exit 1
fi

echo "📦 Testando imports principais..."

# Teste de imports
sudo -u "$APP_USER" ./venv/bin/python -c "
import sys
try:
    print('✓ Python:', sys.version.split()[0])
    
    import flask
    print('✓ Flask:', flask.__version__)
    
    import sqlalchemy
    print('✓ SQLAlchemy:', sqlalchemy.__version__)
    
    import pymysql
    print('✓ PyMySQL:', pymysql.__version__)
    
    import gunicorn
    print('✓ Gunicorn:', gunicorn.__version__)
    
    print('✓ Todas as dependências principais OK')
    
except ImportError as e:
    print('❌ Erro de import:', e)
    sys.exit(1)
"

echo
echo "🔧 Testando conexão com banco..."
sudo -u "$APP_USER" ./venv/bin/python -c "
import sys
import os
from dotenv import load_dotenv

try:
    load_dotenv()
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print('❌ DATABASE_URL não encontrada no .env')
        sys.exit(1)
    
    print('✓ DATABASE_URL configurada')
    
    # Teste de conexão básica
    import pymysql
    from urllib.parse import urlparse
    
    parsed = urlparse(db_url.replace('mysql+pymysql://', 'mysql://'))
    
    conn = pymysql.connect(
        host=parsed.hostname,
        user=parsed.username,
        password=parsed.password,
        database=parsed.path[1:],
        port=parsed.port or 3306
    )
    
    cursor = conn.cursor()
    cursor.execute('SELECT 1')
    result = cursor.fetchone()
    
    if result[0] == 1:
        print('✓ Conexão com MySQL OK')
    
    conn.close()
    
except Exception as e:
    print('❌ Erro de conexão MySQL:', e)
    sys.exit(1)
"

echo
echo "🚀 Testando inicialização da aplicação..."
sudo -u "$APP_USER" timeout 5s ./venv/bin/python -c "
import sys
try:
    from app import app, db
    print('✓ App Flask criado')
    
    with app.app_context():
        db.create_all()
        print('✓ Banco de dados inicializado')
    
    print('✓ Aplicação pronta para iniciar')
    
except Exception as e:
    print('❌ Erro na inicialização:', e)
    sys.exit(1)
" 2>/dev/null || echo "⚠️ Timeout ou erro na inicialização"

echo
echo "=== TESTE CONCLUÍDO ==="