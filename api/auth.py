import logging
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from models import User, UserPlan, PhoneConfirmationToken
from utils import login_required, get_current_user, send_admin_whatsapp_message

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            # Buscar plano do usuário
            user_plan = UserPlan.query.filter_by(user_id=user.id).first()
            user_plan_name = user_plan.plan_name if user_plan else 'Free'
            
            session['user_id'] = user.id
            session['username'] = user.username
            session['is_admin'] = user.is_admin
            session['user_plan_name'] = user_plan_name
            
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('dashboard.index'))
        else:
            flash('Usuário ou senha inválidos!', 'error')
    
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        phone = request.form.get('phone')
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            flash('Nome de usuário já existe!', 'error')
            return render_template('auth/register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email já cadastrado!', 'error')
            return render_template('auth/register.html')
        
        # Create new user
        user = User(
            username=username,
            email=email,
            phone=phone
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        # Create default Free plan for user
        user_plan = UserPlan(
            user_id=user.id,
            plan_name='Free',
            max_clients=5,
            max_receivables=20,
            max_payables=20
        )
        db.session.add(user_plan)
        
        try:
            db.session.commit()
            
            # Gerar código de confirmação do WhatsApp
            if phone:
                token_code = PhoneConfirmationToken.generate_token()
                confirmation_token = PhoneConfirmationToken(
                    user_id=user.id,
                    token=token_code,
                    phone=phone,
                    expires_at=datetime.utcnow() + timedelta(hours=24)
                )
                db.session.add(confirmation_token)
                db.session.commit()
                
                # Enviar código via WhatsApp da instância do admin
                message = f"""🎉 *Bem-vindo ao FinanceiroMax!*

Olá *{username}*! Sua conta foi criada com sucesso.

🔑 *Código de confirmação:* `{token_code}`

Para confirmar seu número WhatsApp, acesse:
{request.url_root}auth/confirm_phone/{token_code}

✅ Após a confirmação, você terá acesso completo ao sistema!

_Este código expira em 24 horas._

---
*FinanceiroMax - Sistema Financeiro Inteligente*"""
                
                whatsapp_sent = send_admin_whatsapp_message(phone, message)
                
                if whatsapp_sent:
                    flash('Usuário criado com sucesso! Código de confirmação enviado no seu WhatsApp. Confirme seu número para ativar a conta.', 'success')
                else:
                    flash('Usuário criado com sucesso! Porém não foi possível enviar o código de confirmação via WhatsApp. Faça o login normalmente.', 'warning')
            else:
                flash('Usuário criado com sucesso! Faça o login.', 'success')
                
        except Exception as e:
            db.session.rollback()
            logging.error(f"Database error during user registration: {str(e)}")
            flash('Erro interno. Tente novamente em alguns minutos.', 'error')
            return render_template('auth/register.html')
        
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')

@auth_bp.route('/confirm_phone/<token>')
def confirm_phone(token):
    """Confirmar número de telefone com token enviado via WhatsApp"""
    logging.info(f"Attempting to confirm phone with token: {token}")
    
    # Buscar token
    confirmation_token = PhoneConfirmationToken.query.filter_by(
        token=token, 
        is_used=False
    ).first()
    
    logging.info(f"Token found: {confirmation_token is not None}")
    
    if not confirmation_token:
        # Verificar se o token existe mas já foi usado
        used_token = PhoneConfirmationToken.query.filter_by(token=token).first()
        if used_token:
            flash('Este código já foi utilizado!', 'warning')
        else:
            flash('Código de confirmação inválido!', 'error')
        return redirect(url_for('auth.login'))
    
    if confirmation_token.is_expired():
        flash('Código de confirmação expirado! Solicite um novo código.', 'error')
        return redirect(url_for('auth.login'))
    
    # Marcar usuário como confirmado
    user = User.query.get(confirmation_token.user_id)
    if user:
        user.phone_confirmed = True
        confirmation_token.is_used = True
        
        try:
            db.session.commit()
            return render_template('auth/phone_confirmed.html')
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error confirming phone: {str(e)}")
            flash('Erro interno. Tente novamente.', 'error')
    else:
        flash('Usuário não encontrado!', 'error')
    
    return redirect(url_for('auth.login'))

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('Logout realizado com sucesso!', 'success')
    return redirect(url_for('auth.login'))
