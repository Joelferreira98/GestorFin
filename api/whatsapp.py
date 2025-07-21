from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app import db
from models import UserWhatsAppInstance, WhatsAppMessage, PaymentReminder, Client, SystemSettings
from utils import login_required, get_current_user, send_whatsapp_message
import requests
import os
import logging

whatsapp_bp = Blueprint('whatsapp', __name__)

@whatsapp_bp.route('/')
@login_required
def index():
    user = get_current_user()
    instances = UserWhatsAppInstance.query.filter_by(user_id=user.id).all()
    messages = db.session.query(WhatsAppMessage, Client).join(Client).filter(
        WhatsAppMessage.user_id == user.id
    ).order_by(WhatsAppMessage.created_at.desc()).limit(50).all()
    reminders = PaymentReminder.query.filter_by(user_id=user.id).all()
    clients = Client.query.filter_by(user_id=user.id).filter(Client.whatsapp.isnot(None)).all()
    
    return render_template('whatsapp.html', instances=instances, messages=messages, reminders=reminders, clients=clients)

@whatsapp_bp.route('/instances/add', methods=['POST'])
@login_required
def add_instance():
    user = get_current_user()
    
    instance_name = request.form.get('instance_name')
    phone_number = request.form.get('phone_number')
    
    # Get Evolution API settings from admin panel
    system_settings = SystemSettings.query.first()
    
    if not system_settings or not system_settings.evolution_enabled:
        flash('Integração Evolution API não está configurada ou ativada!', 'error')
        return redirect(url_for('whatsapp.index'))
    
    if not system_settings.evolution_api_url or not system_settings.evolution_api_key:
        flash('URL da API e chave de acesso devem ser configurados no painel administrativo!', 'error')
        return redirect(url_for('whatsapp.index'))
    
    try:
        # First, check if the instance already exists
        check_response = requests.get(
            f"{system_settings.evolution_api_url.rstrip('/')}/instance/fetchInstances",
            headers={
                'apikey': system_settings.evolution_api_key,
                'Content-Type': 'application/json'
            },
            timeout=10
        )
        
        logging.debug(f"Check instances response: {check_response.status_code} - {check_response.text}")
        
        if check_response.status_code == 401:
            flash('Chave da API inválida! Verifique as configurações no painel administrativo.', 'error')
            return redirect(url_for('whatsapp.index'))
        elif check_response.status_code != 200:
            flash(f'Erro ao conectar com a Evolution API: {check_response.status_code}', 'error')
            return redirect(url_for('whatsapp.index'))
        
        # Create the instance
        create_response = requests.post(
            f"{system_settings.evolution_api_url.rstrip('/')}/instance/create",
            headers={
                'apikey': system_settings.evolution_api_key,
                'Content-Type': 'application/json'
            },
            json={
                'instanceName': instance_name,
                'token': system_settings.evolution_api_key,
                'qrcode': True,
                'integration': 'WHATSAPP-BAILEYS'
            },
            timeout=30
        )
        
        logging.debug(f"Create instance response: {create_response.status_code} - {create_response.text}")
        
        if create_response.status_code in [200, 201]:
            result = create_response.json()
            
            instance = UserWhatsAppInstance(
                user_id=user.id,
                instance_name=instance_name,
                phone_number=phone_number,
                status='connecting'
            )
            
            db.session.add(instance)
            db.session.commit()
            
            flash('Instância criada com sucesso! Use o QR Code para conectar seu WhatsApp.', 'success')
        else:
            error_msg = create_response.text
            try:
                error_data = create_response.json()
                if 'message' in error_data:
                    error_msg = error_data['message']
            except:
                pass
            flash(f'Erro ao criar instância: {error_msg}', 'error')
    
    except requests.exceptions.Timeout:
        flash('Tempo limite esgotado. Verifique se a URL da API está correta.', 'error')
    except requests.exceptions.ConnectionError:
        flash('Erro de conexão. Verifique se a URL da API está correta e acessível.', 'error')
    except Exception as e:
        logging.error(f"Error creating instance: {str(e)}")
        flash(f'Erro inesperado: {str(e)}', 'error')
    
    return redirect(url_for('whatsapp.index'))

@whatsapp_bp.route('/instances/qrcode/<instance_name>')
@login_required
def get_qrcode(instance_name):
    """Get QR Code for WhatsApp instance connection"""
    user = get_current_user()
    
    # Check if user owns this instance
    instance = UserWhatsAppInstance.query.filter_by(
        instance_name=instance_name, 
        user_id=user.id
    ).first_or_404()
    
    # Get Evolution API settings
    system_settings = SystemSettings.query.first()
    
    if not system_settings or not system_settings.evolution_enabled:
        return jsonify({'error': 'Evolution API não configurada'}), 400
    
    try:
        response = requests.get(
            f"{system_settings.evolution_api_url.rstrip('/')}/instance/connect/{instance_name}",
            headers={
                'apikey': system_settings.evolution_api_key,
            },
            timeout=10
        )
        
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({'error': 'Erro ao obter QR Code'}), response.status_code
    
    except Exception as e:
        logging.error(f"Error getting QR code: {str(e)}")
        return jsonify({'error': str(e)}), 500

@whatsapp_bp.route('/instances/delete/<int:instance_id>', methods=['POST'])
@login_required
def delete_instance(instance_id):
    user = get_current_user()
    instance = UserWhatsAppInstance.query.filter_by(id=instance_id, user_id=user.id).first_or_404()
    
    db.session.delete(instance)
    db.session.commit()
    
    flash('Instância removida com sucesso!', 'success')
    return redirect(url_for('whatsapp.index'))

@whatsapp_bp.route('/send_message', methods=['POST'])
@login_required
def send_message():
    user = get_current_user()
    
    client_id = request.form.get('client_id')
    message = request.form.get('message')
    message_type = request.form.get('message_type', 'manual')
    
    client = Client.query.filter_by(id=client_id, user_id=user.id).first_or_404()
    
    if not client.whatsapp:
        flash('Cliente não possui WhatsApp cadastrado!', 'error')
        return redirect(url_for('whatsapp.index'))
    
    # Send message via Evolution API
    success = send_whatsapp_message(user.id, client.whatsapp, message)
    
    # Log message
    whatsapp_msg = WhatsAppMessage(
        user_id=user.id,
        client_id=client_id,
        message_type=message_type,
        content=message,
        status='sent' if success else 'failed'
    )
    db.session.add(whatsapp_msg)
    db.session.commit()
    
    if success:
        flash('Mensagem enviada com sucesso!', 'success')
    else:
        flash('Erro ao enviar mensagem!', 'error')
    
    return redirect(url_for('whatsapp.index'))

@whatsapp_bp.route('/reminders/add', methods=['POST'])
@login_required
def add_reminder():
    user = get_current_user()
    
    name = request.form.get('name')
    message = request.form.get('message')
    time = request.form.get('time')
    days = request.form.get('days')
    reminder_type = request.form.get('reminder_type', 'due_date')
    
    reminder = PaymentReminder(
        user_id=user.id,
        name=name,
        message=message,
        time=time,
        days=int(days),
        reminder_type=reminder_type
    )
    
    db.session.add(reminder)
    db.session.commit()
    
    flash('Lembrete configurado com sucesso!', 'success')
    return redirect(url_for('whatsapp.index'))

@whatsapp_bp.route('/reminders/toggle/<int:reminder_id>', methods=['POST'])
@login_required
def toggle_reminder(reminder_id):
    user = get_current_user()
    reminder = PaymentReminder.query.filter_by(id=reminder_id, user_id=user.id).first_or_404()
    
    reminder.is_active = not reminder.is_active
    db.session.commit()
    
    status = 'ativado' if reminder.is_active else 'desativado'
    flash(f'Lembrete {status} com sucesso!', 'success')
    return redirect(url_for('whatsapp.index'))

@whatsapp_bp.route('/reminders/delete/<int:reminder_id>', methods=['POST'])
@login_required
def delete_reminder(reminder_id):
    user = get_current_user()
    reminder = PaymentReminder.query.filter_by(id=reminder_id, user_id=user.id).first_or_404()
    
    db.session.delete(reminder)
    db.session.commit()
    
    flash('Lembrete removido com sucesso!', 'success')
    return redirect(url_for('whatsapp.index'))
