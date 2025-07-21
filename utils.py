from flask import session, redirect, url_for, flash
from functools import wraps
from models import User
import re
import requests
import os

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
    
    if len(phone) == 10:
        phone = '55' + phone
    elif len(phone) == 11:
        phone = '55' + phone
    elif not phone.startswith('55'):
        phone = '55' + phone
    
    return phone

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
                'textMessage': {
                    'text': message
                }
            },
            timeout=10
        )
        
        logging.debug(f"WhatsApp message response: {response.status_code} - {response.text}")
        
        return response.status_code in [200, 201]
    except Exception as e:
        logging.error(f"Error sending WhatsApp message: {str(e)}")
        return False
