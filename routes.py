import os
from flask import render_template, request, redirect, url_for, session, flash, jsonify
from app import app
from models import User
from utils import calculate_dashboard_stats

# Blueprints are registered in app.py to avoid conflicts

def login_required(f):
    """Decorator to require login for routes"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
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
            return redirect(url_for('dashboard.index'))
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
        return redirect(url_for('dashboard.index'))
    return render_template('auth/login.html')

# Login e register são tratados pelos blueprints em api/
# Removidas rotas duplicadas

# Todas as rotas principais foram movidas para blueprints em api/
# Mantendo apenas rotas básicas aqui

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
