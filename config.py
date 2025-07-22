"""
Configurações do FinanceiroMax para diferentes ambientes
"""
import os
from urllib.parse import quote_plus

class Config:
    """Configurações base"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.environ.get('SESSION_SECRET') or 'dev-secret-key'
    
    # Database
    DATABASE_URL = os.environ.get('DATABASE_URL')
    
    if DATABASE_URL and DATABASE_URL.startswith('mysql'):
        # MySQL configuration
        SQLALCHEMY_DATABASE_URI = DATABASE_URL
        SQLALCHEMY_ENGINE_OPTIONS = {
            'pool_size': int(os.environ.get('SQLALCHEMY_ENGINE_OPTIONS_POOL_SIZE', 20)),
            'max_overflow': int(os.environ.get('SQLALCHEMY_ENGINE_OPTIONS_MAX_OVERFLOW', 30)),
            'pool_recycle': int(os.environ.get('SQLALCHEMY_ENGINE_OPTIONS_POOL_RECYCLE', 3600)),
            'pool_pre_ping': os.environ.get('SQLALCHEMY_ENGINE_OPTIONS_POOL_PRE_PING', 'True').lower() == 'true',
            'echo': False  # Set to True for SQL debugging
        }
    else:
        # SQLite fallback for development
        SQLALCHEMY_DATABASE_URI = DATABASE_URL or 'sqlite:///financeiro.db'
        SQLALCHEMY_ENGINE_OPTIONS = {
            'pool_recycle': 300,
            'pool_pre_ping': True,
        }
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Flask
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    TESTING = False
    
    # Upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = 'static/uploads'
    
    # Security
    SESSION_COOKIE_SECURE = os.environ.get('FLASK_ENV') == 'production'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 3600 * 24 * 7  # 1 week
    
    # External APIs
    EVOLUTION_API_URL = os.environ.get('EVOLUTION_API_URL')
    EVOLUTION_API_KEY = os.environ.get('EVOLUTION_API_KEY')
    EVOLUTION_DEFAULT_INSTANCE = os.environ.get('EVOLUTION_DEFAULT_INSTANCE')
    
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    
    # Server
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', 5000))
    DOMAIN = os.environ.get('DOMAIN', 'localhost:5000')

class DevelopmentConfig(Config):
    """Configurações de desenvolvimento"""
    DEBUG = True
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 300,
        'pool_pre_ping': True,
    }

class ProductionConfig(Config):
    """Configurações de produção"""
    DEBUG = False
    TESTING = False
    
    # Enhanced security for production
    SESSION_COOKIE_SECURE = True
    WTF_CSRF_SSL_STRICT = True
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', '/var/log/financeiro-max/app.log')

class TestingConfig(Config):
    """Configurações de teste"""
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

# Mapeamento de configurações
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Retorna a configuração baseada na variável de ambiente"""
    return config.get(os.environ.get('FLASK_ENV', 'development'), DevelopmentConfig)