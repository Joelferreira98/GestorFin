from flask import render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash, generate_password_hash
from app import app, db
from models import User, UserPlan
from datetime import datetime, timedelta
import re

def login_required(f):
    """Decorator to require login for routes"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to require admin privileges"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        
        user = User.query.get(session['user_id'])
        if not user or not user.is_admin:
            flash('Acesso negado. Privilégios de administrador necessários.', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    """Home page - redirect to dashboard if logged in, otherwise show login"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Por favor, preencha todos os campos.', 'error')
            return render_template('auth/login.html')
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['is_admin'] = user.is_admin
            flash(f'Bem-vindo, {user.username}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Usuário ou senha inválidos.', 'error')
    
    return render_template('auth/login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        phone = request.form.get('phone')
        
        # Validation
        if not all([username, email, password, confirm_password]):
            flash('Por favor, preencha todos os campos obrigatórios.', 'error')
            return render_template('auth/register.html')
        
        if password != confirm_password:
            flash('As senhas não coincidem.', 'error')
            return render_template('auth/register.html')
        
        if len(password) < 6:
            flash('A senha deve ter pelo menos 6 caracteres.', 'error')
            return render_template('auth/register.html')
        
        # Email validation
        email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        if not email_pattern.match(email):
            flash('Por favor, insira um email válido.', 'error')
            return render_template('auth/register.html')
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            flash('Nome de usuário já existe.', 'error')
            return render_template('auth/register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email já cadastrado.', 'error')
            return render_template('auth/register.html')
        
        try:
            # Create new user
            user = User(
                username=username,
                email=email,
                password_hash=generate_password_hash(password),
                phone=phone
            )
            db.session.add(user)
            db.session.flush()  # Get user ID
            
            # Create basic plan for new user
            user_plan = UserPlan(
                user_id=user.id,
                plan_name='basic',
                max_clients=10,
                max_receivables=50,
                max_payables=20,
                expires_at=datetime.utcnow() + timedelta(days=30)  # 30 days trial
            )
            db.session.add(user_plan)
            db.session.commit()
            
            flash('Conta criada com sucesso! Você ganhou 30 dias grátis do plano básico.', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            db.session.rollback()
            flash('Erro ao criar conta. Tente novamente.', 'error')
            return render_template('auth/register.html')
    
    return render_template('auth/register.html')

@app.route('/logout')
def logout():
    """User logout"""
    session.clear()
    flash('Logout realizado com sucesso.', 'success')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard"""
    user = User.query.get(session['user_id'])
    
    # Get dashboard statistics
    stats = {
        'total_clients': len(user.clients),
        'total_receivables': len([r for r in user.receivables if r.status == 'pending']),
        'total_payables': len([p for p in user.payables if p.status == 'pending']),
        'overdue_receivables': len([r for r in user.receivables if r.status == 'overdue']),
        'total_receivables_amount': sum([float(r.amount) for r in user.receivables if r.status == 'pending']),
        'total_payables_amount': sum([float(p.amount) for p in user.payables if p.status == 'pending']),
        'pending_sales': len([s for s in user.installment_sales if s.status == 'pending'])
    }
    
    # Recent receivables
    recent_receivables = sorted(user.receivables, key=lambda x: x.created_at, reverse=True)[:5]
    
    # Recent payables
    recent_payables = sorted(user.payables, key=lambda x: x.created_at, reverse=True)[:5]
    
    # Upcoming due dates
    from datetime import date
    upcoming_receivables = [r for r in user.receivables 
                          if r.status == 'pending' and r.due_date <= date.today() + timedelta(days=7)]
    upcoming_payables = [p for p in user.payables 
                        if p.status == 'pending' and p.due_date <= date.today() + timedelta(days=7)]
    
    return render_template('dashboard.html', 
                         user=user,
                         stats=stats,
                         recent_receivables=recent_receivables,
                         recent_payables=recent_payables,
                         upcoming_receivables=upcoming_receivables,
                         upcoming_payables=upcoming_payables)

@app.route('/clients')
@login_required
def clients():
    """Clients management page"""
    return render_template('clients.html')

@app.route('/receivables')
@login_required
def receivables():
    """Receivables management page"""
    return render_template('receivables.html')

@app.route('/payables')
@login_required
def payables():
    """Payables management page"""
    return render_template('payables.html')

@app.route('/installment-sales')
@login_required
def installment_sales():
    """Installment sales management page"""
    return render_template('installment_sales.html')

@app.route('/whatsapp')
@login_required
def whatsapp():
    """WhatsApp configuration page"""
    return render_template('whatsapp.html')

@app.route('/admin')
@admin_required
def admin():
    """Admin panel"""
    return render_template('admin.html')

@app.route('/confirm-sale/<token>')
def confirm_sale(token):
    """Public page for sale confirmation"""
    from models import InstallmentSale
    sale = InstallmentSale.query.filter_by(confirmation_token=token).first()
    if not sale:
        flash('Link inválido ou expirado.', 'error')
        return redirect(url_for('login'))
    
    return render_template('confirm_sale.html', sale=sale)
