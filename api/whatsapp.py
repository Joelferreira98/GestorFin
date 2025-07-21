from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app import db
from models import UserWhatsAppInstance, WhatsAppMessage, PaymentReminder, Client
from utils import login_required, get_current_user, send_whatsapp_message
import requests
import os

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
    
    return render_template('whatsapp.html', instances=instances, messages=messages, reminders=reminders)

@whatsapp_bp.route('/instances/add', methods=['POST'])
@login_required
def add_instance():
    user = get_current_user()
    
    instance_name = request.form.get('instance_name')
    phone_number = request.form.get('phone_number')
    
    # Create instance via Evolution API
    api_url = os.environ.get('EVOLUTION_API_URL', 'https://api.evolutionapi.com')
    api_key = os.environ.get('EVOLUTION_API_KEY', 'default_key')
    
    try:
        response = requests.post(
            f"{api_url}/instance/create",
            headers={
                'apikey': api_key,
                'Content-Type': 'application/json'
            },
            json={
                'instanceName': instance_name,
                'number': phone_number
            }
        )
        
        if response.status_code == 200:
            instance = UserWhatsAppInstance(
                user_id=user.id,
                instance_name=instance_name,
                phone_number=phone_number,
                status='connecting'
            )
            
            db.session.add(instance)
            db.session.commit()
            
            flash('Instância criada com sucesso!', 'success')
        else:
            flash('Erro ao criar instância na Evolution API!', 'error')
    
    except Exception as e:
        flash(f'Erro de conexão: {str(e)}', 'error')
    
    return redirect(url_for('whatsapp.index'))

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
