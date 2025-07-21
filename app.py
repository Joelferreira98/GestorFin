import os
import logging
from datetime import datetime
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///financeiro.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize the app with the extension
db.init_app(app)

# Import models and create tables
with app.app_context():
    import models
    db.create_all()
    
    # Create sample data if not exists
    from sample_data import create_sample_data
    create_sample_data()

# Register blueprints
from api.auth import auth_bp
from api.clients import clients_bp
from api.receivables import receivables_bp
from api.payables import payables_bp
from api.installment_sales import installment_sales_bp
from api.whatsapp import whatsapp_bp
from api.admin import admin_bp
from api.dashboard import dashboard_bp

app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(clients_bp, url_prefix='/clients')
app.register_blueprint(receivables_bp, url_prefix='/receivables')
app.register_blueprint(payables_bp, url_prefix='/payables')
app.register_blueprint(installment_sales_bp, url_prefix='/sales')
app.register_blueprint(whatsapp_bp, url_prefix='/whatsapp')
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(dashboard_bp, url_prefix='/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
