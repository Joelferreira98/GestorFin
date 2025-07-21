from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app import db
from models import UserWhatsAppInstance, WhatsAppMessage, PaymentReminder, Client, SystemSettings
from utils import login_required, get_current_user, send_whatsapp_message
import requests
import os
import logging
import qrcode
import io
import base64
from PIL import Image

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
    
    # Get Evolution API settings from admin panel
    system_settings = SystemSettings.query.first()
    
    if not system_settings or not system_settings.evolution_enabled:
        flash('Integração Evolution API não está configurada ou ativada! Configure no painel administrativo primeiro.', 'error')
        return redirect(url_for('whatsapp.index'))
    
    if not system_settings.evolution_api_url or not system_settings.evolution_api_key:
        flash('URL da API e chave de acesso devem ser configurados no painel administrativo!', 'error')
        return redirect(url_for('whatsapp.index'))
    
    try:
        # Debug: Log the exact configuration being used
        logging.debug(f"API URL: '{system_settings.evolution_api_url}'")
        logging.debug(f"API Key: '{system_settings.evolution_api_key}'")
        logging.debug(f"API Key length: {len(system_settings.evolution_api_key) if system_settings.evolution_api_key else 'None'}")
        logging.debug(f"Instance Name: '{instance_name}'")
        
        # Clean the API key and URL from any potential whitespace/encoding issues
        clean_api_key = system_settings.evolution_api_key.strip() if system_settings.evolution_api_key else ''
        clean_api_url = system_settings.evolution_api_url.rstrip('/') if system_settings.evolution_api_url else ''
        
        logging.debug(f"Clean API Key: '{clean_api_key}'")
        logging.debug(f"Clean API URL: '{clean_api_url}'")
        
        # Create the instance directly using Baileys (following Evolution API documentation)
        create_response = requests.post(
            f"{clean_api_url}/instance/create",
            headers={
                'Content-Type': 'application/json',
                'apikey': clean_api_key
            },
            json={
                'instanceName': instance_name,
                'token': clean_api_key,
                'qrcode': True,
                'integration': 'WHATSAPP-BAILEYS'
            },
            timeout=30
        )
        
        logging.debug(f"Create instance response: {create_response.status_code} - {create_response.text}")
        
        if create_response.status_code == 401:
            flash('Chave da API inválida! Verifique a configuração no painel administrativo. Certifique-se de que a chave está correta e que a API está funcionando.', 'error')
            return redirect(url_for('whatsapp.index'))
        elif create_response.status_code in [200, 201]:
            result = create_response.json()
            
            instance = UserWhatsAppInstance(
                user_id=user.id,
                instance_name=instance_name,
                phone_number=None,  # Número será preenchido após conectar
                status='connecting'
            )
            
            db.session.add(instance)
            db.session.commit()
            
            flash('Instância criada com sucesso! Clique em "QR Code" para conectar seu WhatsApp.', 'success')
        elif create_response.status_code == 409:
            flash(f'Instância "{instance_name}" já existe! Escolha outro nome.', 'warning')
        else:
            error_msg = 'Erro desconhecido'
            try:
                error_data = create_response.json()
                if 'message' in error_data:
                    error_msg = error_data['message']
                elif 'error' in error_data:
                    error_msg = error_data['error']
            except:
                error_msg = f'Código de erro: {create_response.status_code}'
            flash(f'Erro ao criar instância: {error_msg}', 'error')
    
    except requests.exceptions.Timeout:
        flash('Tempo limite esgotado. Verifique se a URL da API está correta e acessível.', 'error')
    except requests.exceptions.ConnectionError:
        flash('Erro de conexão. Verifique se a URL da API está correta e se o servidor está funcionando.', 'error')
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
        # Clean the API key and URL from any potential issues
        clean_api_key = system_settings.evolution_api_key.strip() if system_settings.evolution_api_key else ''
        clean_api_url = system_settings.evolution_api_url.rstrip('/') if system_settings.evolution_api_url else ''
        
        response = requests.get(
            f"{clean_api_url}/instance/connect/{instance_name}",
            headers={
                'apikey': clean_api_key,
            },
            timeout=10
        )
        
        logging.debug(f"QR Code response: {response.status_code} - {response.text}")
        
        if response.status_code == 200:
            response_data = response.json()
            
            # The Evolution API returns QR code in 'code' field as text
            if 'code' in response_data and response_data['code']:
                try:
                    # Generate QR code image from the text code
                    qr_code_text = response_data['code']
                    
                    # Create QR code
                    qr = qrcode.QRCode(
                        version=1,
                        error_correction=qrcode.constants.ERROR_CORRECT_L,
                        box_size=10,
                        border=4,
                    )
                    qr.add_data(qr_code_text)
                    qr.make(fit=True)
                    
                    # Create image
                    qr_image = qr.make_image(fill_color="black", back_color="white")
                    
                    # Convert to base64
                    buffer = io.BytesIO()
                    qr_image.save(buffer, format='PNG')
                    buffer.seek(0)
                    
                    qr_base64 = base64.b64encode(buffer.getvalue()).decode()
                    
                    return jsonify({'qrcode': qr_base64})
                    
                except Exception as e:
                    logging.error(f"Error generating QR code: {e}")
                    return jsonify({'error': f'Erro ao gerar QR code: {str(e)}'})
            elif 'base64' in response_data:
                return jsonify({'qrcode': response_data['base64']})
            else:
                # Check if instance is already connected
                if response_data.get('instance', {}).get('connectionStatus') == 'open':
                    return jsonify({'error': 'WhatsApp já está conectado para esta instância'})
                else:
                    # Log the full response for debugging
                    logging.debug(f"Full QR response: {response_data}")
                    return jsonify({'error': 'QR Code não disponível. Tente novamente em alguns segundos.'})
        else:
            return jsonify({'error': f'Erro {response.status_code}: {response.text}'}), response.status_code
    
    except Exception as e:
        logging.error(f"Error getting QR code: {str(e)}")
        return jsonify({'error': str(e)}), 500

@whatsapp_bp.route('/instances/status/<instance_name>')
@login_required
def check_instance_status(instance_name):
    """Check the connection status of a WhatsApp instance"""
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
        # Clean the API key and URL from any potential issues
        clean_api_key = system_settings.evolution_api_key.strip() if system_settings.evolution_api_key else ''
        clean_api_url = system_settings.evolution_api_url.rstrip('/') if system_settings.evolution_api_url else ''
        
        response = requests.get(
            f"{clean_api_url}/instance/fetchInstances",
            headers={
                'apikey': clean_api_key,
            },
            timeout=10
        )
        
        if response.status_code == 200:
            instances_data = response.json()
            
            # Find our specific instance in the response
            for api_instance in instances_data:
                if api_instance.get('name') == instance_name:
                    connection_status = api_instance.get('connectionStatus', 'disconnected')
                    owner_jid = api_instance.get('ownerJid')
                    profile_name = api_instance.get('profileName')
                    
                    # Update local database with current status
                    if connection_status == 'open':
                        instance.status = 'connected'
                        if owner_jid:
                            # Extract phone number from JID (format: 5511999999999@s.whatsapp.net)
                            phone_number = owner_jid.split('@')[0]
                            instance.phone_number = phone_number
                    elif connection_status in ['close', 'disconnected']:
                        instance.status = 'disconnected'
                    else:
                        instance.status = 'connecting'
                    
                    db.session.commit()
                    
                    return jsonify({
                        'status': instance.status,
                        'phone_number': instance.phone_number,
                        'profile_name': profile_name,
                        'connection_status': connection_status
                    })
            
            # Instance not found in API response
            return jsonify({'error': 'Instância não encontrada na API'})
        else:
            return jsonify({'error': f'Erro da API: {response.status_code}'}), response.status_code
    
    except Exception as e:
        logging.error(f"Error checking instance status: {str(e)}")
        return jsonify({'error': str(e)}), 500

@whatsapp_bp.route('/instances/delete/<int:instance_id>', methods=['POST'])
@login_required
def delete_instance(instance_id):
    user = get_current_user()
    instance = UserWhatsAppInstance.query.filter_by(id=instance_id, user_id=user.id).first_or_404()
    
    # Try to delete from Evolution API as well
    system_settings = SystemSettings.query.first()
    if system_settings and system_settings.evolution_enabled:
        try:
            clean_api_key = system_settings.evolution_api_key.strip() if system_settings.evolution_api_key else ''
            clean_api_url = system_settings.evolution_api_url.rstrip('/') if system_settings.evolution_api_url else ''
            
            requests.delete(
                f"{clean_api_url}/instance/delete/{instance.instance_name}",
                headers={'apikey': clean_api_key},
                timeout=10
            )
        except Exception as e:
            logging.warning(f"Failed to delete instance from API: {e}")
    
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
