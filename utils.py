from flask import session, redirect, url_for, flash
from functools import wraps
from models import User, UserPlan
import re
import requests
import os
import logging
from datetime import datetime

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Você precisa estar logado para acessar esta página.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Você precisa estar logado para acessar esta página.', 'error')
            return redirect(url_for('auth.login'))
        
        user = get_current_user()
        if not user.is_admin:
            flash('Acesso negado. Apenas administradores podem acessar esta página.', 'error')
            return redirect(url_for('dashboard.index'))
        
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    return None

def get_user_plan_name(user_id):
    """Buscar plano atual do usuário no banco de dados"""
    user_plan = UserPlan.query.filter_by(user_id=user_id).first()
    
    if not user_plan:
        return 'Free'
    
    # Verificar se o plano Premium expirou
    if user_plan.plan_name == 'Premium' and user_plan.expires_at:
        if user_plan.expires_at < datetime.utcnow():
            return 'Free'  # Plano expirou, retornar para Free
    
    return user_plan.plan_name

def has_premium_access(user_id):
    """Verificar se usuário tem acesso Premium válido"""
    return get_user_plan_name(user_id) == 'Premium'

def validate_cpf(cpf):
    """Validate Brazilian CPF"""
    cpf = re.sub(r'[^\d]', '', cpf)
    
    if len(cpf) != 11:
        return False
    
    if cpf == cpf[0] * 11:
        return False
    
    # Calculate first digit
    sum1 = sum(int(cpf[i]) * (10 - i) for i in range(9))
    digit1 = 11 - (sum1 % 11)
    if digit1 >= 10:
        digit1 = 0
    
    # Calculate second digit
    sum2 = sum(int(cpf[i]) * (11 - i) for i in range(10))
    digit2 = 11 - (sum2 % 11)
    if digit2 >= 10:
        digit2 = 0
    
    return cpf[-2:] == f"{digit1}{digit2}"

def validate_cnpj(cnpj):
    """Validate Brazilian CNPJ"""
    cnpj = re.sub(r'[^\d]', '', cnpj)
    
    if len(cnpj) != 14:
        return False
    
    if cnpj == cnpj[0] * 14:
        return False
    
    # Calculate first digit
    weights1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    sum1 = sum(int(cnpj[i]) * weights1[i] for i in range(12))
    digit1 = 11 - (sum1 % 11)
    if digit1 >= 10:
        digit1 = 0
    
    # Calculate second digit
    weights2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    sum2 = sum(int(cnpj[i]) * weights2[i] for i in range(13))
    digit2 = 11 - (sum2 % 11)
    if digit2 >= 10:
        digit2 = 0
    
    return cnpj[-2:] == f"{digit1}{digit2}"

def format_phone(phone):
    """Format phone number for WhatsApp"""
    if not phone:
        return None
    
    phone = re.sub(r'[^\d]', '', phone)
    
    # Handle different Brazilian phone formats
    if len(phone) == 10:  # (11) 9999-9999
        phone = '55' + phone
    elif len(phone) == 11:  # (11) 99999-9999
        phone = '55' + phone
    elif len(phone) == 12 and phone.startswith('55'):  # 55119999999999
        phone = phone
    elif len(phone) == 13 and phone.startswith('55'):  # 5511999999999
        phone = phone
    elif not phone.startswith('55') and len(phone) >= 10:
        phone = '55' + phone
    
    return phone

def get_system_domain():
    """Get configured system domain from admin settings"""
    from models import SystemSettings
    
    try:
        system_settings = SystemSettings.query.first()
        if system_settings and system_settings.system_domain:
            domain = system_settings.system_domain.strip()
            if not domain.startswith(('http://', 'https://')):
                domain = 'https://' + domain
            if not domain.endswith('/'):
                domain += '/'
            return domain
    except Exception:
        pass
    
    # Fallback para desenvolvimento
    return 'https://localhost:5000/'

def generate_system_url(endpoint, **kwargs):
    """Generate URL using system domain instead of request domain"""
    from flask import url_for
    
    # Generate relative URL
    relative_url = url_for(endpoint, **kwargs)
    
    # Combine with system domain
    system_domain = get_system_domain()
    
    # Remove leading slash from relative URL since system_domain ends with /
    if relative_url.startswith('/'):
        relative_url = relative_url[1:]
    
    return f"{system_domain}{relative_url}"

def send_whatsapp_message(user_id, phone, message):
    """Send WhatsApp message via Evolution API"""
    from models import SystemSettings, UserWhatsAppInstance
    import logging
    
    try:
        # Get system settings
        system_settings = SystemSettings.query.first()
        if not system_settings or not system_settings.evolution_enabled:
            logging.warning("Evolution API not configured or disabled")
            return False
        
        # Get user's first connected WhatsApp instance
        instance = UserWhatsAppInstance.query.filter_by(
            user_id=user_id, 
            status='connected'
        ).first()
        
        if not instance:
            logging.warning(f"No connected WhatsApp instance found for user {user_id}")
            return False
        
        # Clean API settings
        clean_api_key = system_settings.evolution_api_key.strip() if system_settings.evolution_api_key else ''
        clean_api_url = system_settings.evolution_api_url.rstrip('/') if system_settings.evolution_api_url else ''
        
        # Format phone number
        formatted_phone = format_phone(phone)
        if not formatted_phone:
            logging.warning(f"Invalid phone number: {phone}")
            return False
        
        # Send message via Evolution API
        response = requests.post(
            f"{clean_api_url}/message/sendText/{instance.instance_name}",
            headers={
                'apikey': clean_api_key,
                'Content-Type': 'application/json'
            },
            json={
                'number': formatted_phone,
                'text': message
            },
            timeout=10
        )
        
        logging.info(f"WhatsApp message response: {response.status_code} - {response.text}")
        
        if response.status_code == 400:
            # Número não existe no WhatsApp
            logging.warning(f"WhatsApp number not found: {formatted_phone}")
            return False
        
        return response.status_code in [200, 201]
    except Exception as e:
        logging.error(f"Error sending WhatsApp message: {str(e)}")
        return False

def send_admin_whatsapp_message(phone, message):
    """Send WhatsApp message from admin instance"""
    from models import SystemSettings, UserWhatsAppInstance, User
    import logging
    import requests
    
    try:
        # Get system settings
        system_settings = SystemSettings.query.first()
        if not system_settings or not system_settings.evolution_enabled:
            logging.warning("Evolution API not configured or disabled")
            return False
        
        # Get first admin's connected WhatsApp instance
        admin_user = User.query.filter_by(is_admin=True).first()
        if not admin_user:
            logging.warning("No admin user found")
            return False
            
        admin_instance = UserWhatsAppInstance.query.filter_by(
            user_id=admin_user.id, 
            status='connected'
        ).first()
        
        if not admin_instance:
            logging.warning(f"No connected WhatsApp instance found for admin")
            return False
        
        # Clean API settings
        clean_api_key = system_settings.evolution_api_key.strip() if system_settings.evolution_api_key else ''
        clean_api_url = system_settings.evolution_api_url.rstrip('/') if system_settings.evolution_api_url else ''
        
        # Format phone number
        formatted_phone = format_phone(phone)
        if not formatted_phone:
            logging.warning(f"Invalid phone number: {phone}")
            return False
        
        # Send message via Evolution API
        response = requests.post(
            f"{clean_api_url}/message/sendText/{admin_instance.instance_name}",
            headers={
                'apikey': clean_api_key,
                'Content-Type': 'application/json'
            },
            json={
                'number': formatted_phone,
                'text': message
            },
            timeout=10
        )
        
        logging.info(f"Admin WhatsApp message response: {response.status_code} - {response.text}")
        
        if response.status_code == 400:
            # Número não existe no WhatsApp
            logging.warning(f"WhatsApp number not found: {formatted_phone}")
            return False
        
        return response.status_code in [200, 201]
    except Exception as e:
        logging.error(f"Error sending admin WhatsApp message: {str(e)}")
        return False
