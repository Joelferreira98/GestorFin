import os
from flask import render_template, request, redirect, url_for, session, flash, jsonify
from app import app
from models import User
# from utils import calculate_dashboard_stats

# Import API blueprints
from api.auth import auth_bp
from api.clients import clients_bp
from api.receivables import receivables_bp
from api.payables import payables_bp
from api.installment_sales import installment_sales_bp
from api.accounts import accounts_bp
from api.whatsapp import whatsapp_bp
from api.reminders import reminders_bp
from api.admin import admin_bp
from api.dashboard import dashboard_bp

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/api')
app.register_blueprint(clients_bp, url_prefix='/api')
app.register_blueprint(receivables_bp, url_prefix='/api')
app.register_blueprint(payables_bp, url_prefix='/api')
app.register_blueprint(installment_sales_bp, url_prefix='/api')
app.register_blueprint(accounts_bp, url_prefix='/api')
app.register_blueprint(whatsapp_bp, url_prefix='/api')
app.register_blueprint(reminders_bp, url_prefix='/api')
app.register_blueprint(admin_bp, url_prefix='/api')
app.register_blueprint(dashboard_bp, url_prefix='/api')

def login_required(f):
    """Decorator to require login for routes"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    """Get current user from session"""
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    return None

def admin_required(f):
    """Decorator to require admin privileges"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user or not user.is_admin:
            flash('Acesso negado. Privilégios de administrador necessários.', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# Make functions available in templates
@app.context_processor
def inject_user():
    return dict(current_user=get_current_user())

# Main routes
@app.route('/')
def index():
    user = get_current_user()
    if user:
        return redirect(url_for('dashboard'))
    return render_template('auth/login.html')

@app.route('/login')
def login():
    return render_template('auth/login.html')

@app.route('/register')
def register():
    return render_template('auth/register.html')

@app.route('/dashboard')
@login_required
def dashboard():
    user = get_current_user()
    stats = calculate_dashboard_stats(user.id)
    return render_template('dashboard.html', stats=stats)

@app.route('/clients')
@login_required
def clients():
    return render_template('clients.html')

@app.route('/receivables')
@login_required
def receivables():
    return render_template('receivables.html')

@app.route('/payables')
@login_required
def payables():
    return render_template('payables.html')

@app.route('/installment-sales')
@login_required
def installment_sales():
    return render_template('installment_sales.html')

@app.route('/whatsapp')
@login_required
def whatsapp():
    return render_template('whatsapp.html')

@app.route('/reminders')
@login_required
def reminders():
    return render_template('reminders.html')

@app.route('/admin')
@login_required
@admin_required
def admin():
    return render_template('admin.html')

@app.route('/confirm-sale/<token>')
def confirm_sale(token):
    """Public route for sale confirmation"""
    from models import InstallmentSale
    
    sale = InstallmentSale.query.filter_by(confirmation_token=token).first()
    if not sale:
        return render_template('confirm_sale.html', error='Token inválido ou expirado'), 404
    
    if sale.status != 'pending':
        return render_template('confirm_sale.html', sale=sale, already_confirmed=True)
    
    return render_template('confirm_sale.html', sale=sale)

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return render_template('base.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('base.html'), 500

# PWA routes
@app.route('/manifest.json')
def manifest():
    return app.send_static_file('manifest.json')

@app.route('/sw.js')
def service_worker():
    return app.send_static_file('sw.js')
