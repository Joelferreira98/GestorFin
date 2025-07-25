import os
import logging
from datetime import datetime
from flask import Flask, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from config import get_config

# Configure logging
log_level = os.environ.get('LOG_LEVEL', 'DEBUG')
logging.basicConfig(
    level=getattr(logging, log_level.upper()),
    format='%(asctime)s %(levelname)s %(name)s: %(message)s'
)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the app
app = Flask(__name__)

# Load configuration
config_class = get_config()
app.config.from_object(config_class)

# Set secret key explicitly if not set in config
if not app.config.get('SECRET_KEY'):
    app.config['SECRET_KEY'] = os.environ.get("SESSION_SECRET")

app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Initialize the app with the extension
db.init_app(app)

# Import models and create tables
with app.app_context():
    import models
    db.create_all()
    
    # Create sample data if not exists
    from sample_data import create_sample_data
    create_sample_data()

# Template context processors
@app.context_processor
def inject_user_plan():
    """Inject user plan information into all templates"""
    from models import SystemSettings
    
    # Get system settings
    system_settings = SystemSettings.query.first()
    
    context = {
        'system_name': system_settings.system_name if system_settings else 'FinanceiroMax',
        'system_logo': system_settings.logo_url if system_settings else None,
        'system_favicon': system_settings.favicon_url if system_settings else None,
        'primary_color': system_settings.primary_color if system_settings else '#007bff',
        'secondary_color': system_settings.secondary_color if system_settings else '#6c757d'
    }
    
    # Add user plan info
    if 'user_id' in session:
        from utils import get_user_plan_name, has_premium_access
        user_id = session['user_id']
        context.update({
            'current_user_plan': get_user_plan_name(user_id),
            'has_premium_access': has_premium_access(user_id)
        })
    else:
        context.update({
            'current_user_plan': 'Free',
            'has_premium_access': False
        })
    
    return context

# Register blueprints
from api.auth import auth_bp
from api.clients import clients_bp
from api.receivables import receivables_bp
from api.payables import payables_bp
from api.installment_sales import installment_sales_bp
from api.accounts import accounts_bp
from api.whatsapp import whatsapp_bp
from api.admin import admin_bp
from api.tasks import tasks_bp
from api.reminders import reminders_bp
from api.ai_insights import ai_insights_bp
from api.dashboard import dashboard_bp
from api.profile import profile_bp
from api.plans import plans_bp

app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(clients_bp, url_prefix='/clients')
app.register_blueprint(receivables_bp, url_prefix='/receivables')
app.register_blueprint(payables_bp, url_prefix='/payables')
app.register_blueprint(installment_sales_bp, url_prefix='/sales')
app.register_blueprint(accounts_bp, url_prefix='/accounts')
app.register_blueprint(whatsapp_bp, url_prefix='/whatsapp')
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(tasks_bp, url_prefix='/tasks')
app.register_blueprint(reminders_bp, url_prefix='/reminders')
app.register_blueprint(ai_insights_bp, url_prefix='/ai_insights')
app.register_blueprint(profile_bp, url_prefix='/profile')
app.register_blueprint(plans_bp, url_prefix='/plans')
app.register_blueprint(dashboard_bp, url_prefix='/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
