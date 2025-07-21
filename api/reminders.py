from flask import Blueprint, request, jsonify, session
from app import db
from models import PaymentReminder, User
from datetime import datetime, time
import re

reminders_bp = Blueprint('reminders', __name__)

def require_auth():
    if 'user_id' not in session:
        return False
    return True

def get_current_user():
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    return None

@reminders_bp.route('/reminders', methods=['GET'])
def get_reminders():
    if not require_auth():
        return jsonify({'error': 'Não autenticado'}), 401
    
    user = get_current_user()
    reminders = PaymentReminder.query.filter_by(user_id=user.id).order_by(PaymentReminder.created_at.desc()).all()
    
    result = []
    for reminder in reminders:
        result.append({
            'id': reminder.id,
            'name': reminder.name,
            'message': reminder.message,
            'time': reminder.time,
            'is_active': reminder.is_active,
            'days': reminder.days,
            'reminder_type': reminder.reminder_type,
            'created_at': reminder.created_at.isoformat()
        })
    
    return jsonify({'reminders': result})

@reminders_bp.route('/reminders', methods=['POST'])
def create_reminder():
    if not require_auth():
        return jsonify({'error': 'Não autenticado'}), 401
    
    try:
        user = get_current_user()
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'message', 'time', 'days']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} é obrigatório'}), 400
        
        # Validate time format (HH:MM)
        time_pattern = r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$'
        if not re.match(time_pattern, data['time']):
            return jsonify({'error': 'Formato de hora inválido (use HH:MM)'}), 400
        
        # Validate days
        try:
            days = int(data['days'])
            if days < 0 or days > 365:
                return jsonify({'error': 'Dias deve ser entre 0 e 365'}), 400
        except:
            return jsonify({'error': 'Valor de dias inválido'}), 400
        
        # Validate reminder type
        valid_types = ['due_date', 'overdue', 'follow_up']
        reminder_type = data.get('reminder_type', 'due_date')
        if reminder_type not in valid_types:
            return jsonify({'error': 'Tipo de lembrete inválido'}), 400
        
        # Create reminder
        reminder = PaymentReminder(
            user_id=user.id,
            name=data['name'],
            message=data['message'],
            time=data['time'],
            is_active=data.get('is_active', True),
            days=days,
            reminder_type=reminder_type
        )
        
        db.session.add(reminder)
        db.session.commit()
        
        return jsonify({
            'message': 'Lembrete criado com sucesso',
            'reminder': {
                'id': reminder.id,
                'name': reminder.name,
                'message': reminder.message,
                'time': reminder.time,
                'is_active': reminder.is_active,
                'days': reminder.days,
                'reminder_type': reminder.reminder_type
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@reminders_bp.route('/reminders/<int:reminder_id>', methods=['GET'])
def get_reminder(reminder_id):
    if not require_auth():
        return jsonify({'error': 'Não autenticado'}), 401
    
    user = get_current_user()
    reminder = PaymentReminder.query.filter_by(id=reminder_id, user_id=user.id).first()
    
    if not reminder:
        return jsonify({'error': 'Lembrete não encontrado'}), 404
    
    return jsonify({
        'reminder': {
            'id': reminder.id,
            'name': reminder.name,
            'message': reminder.message,
            'time': reminder.time,
            'is_active': reminder.is_active,
            'days': reminder.days,
            'reminder_type': reminder.reminder_type,
            'created_at': reminder.created_at.isoformat()
        }
    })

@reminders_bp.route('/reminders/<int:reminder_id>', methods=['PUT'])
def update_reminder(reminder_id):
    if not require_auth():
        return jsonify({'error': 'Não autenticado'}), 401
    
    try:
        user = get_current_user()
        reminder = PaymentReminder.query.filter_by(id=reminder_id, user_id=user.id).first()
        
        if not reminder:
            return jsonify({'error': 'Lembrete não encontrado'}), 404
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'message', 'time', 'days']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} é obrigatório'}), 400
        
        # Validate time format (HH:MM)
        time_pattern = r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$'
        if not re.match(time_pattern, data['time']):
            return jsonify({'error': 'Formato de hora inválido (use HH:MM)'}), 400
        
        # Validate days
        try:
            days = int(data['days'])
            if days < 0 or days > 365:
                return jsonify({'error': 'Dias deve ser entre 0 e 365'}), 400
        except:
            return jsonify({'error': 'Valor de dias inválido'}), 400
        
        # Validate reminder type
        valid_types = ['due_date', 'overdue', 'follow_up']
        reminder_type = data.get('reminder_type', 'due_date')
        if reminder_type not in valid_types:
            return jsonify({'error': 'Tipo de lembrete inválido'}), 400
        
        # Update reminder
        reminder.name = data['name']
        reminder.message = data['message']
        reminder.time = data['time']
        reminder.is_active = data.get('is_active', True)
        reminder.days = days
        reminder.reminder_type = reminder_type
        
        db.session.commit()
        
        return jsonify({
            'message': 'Lembrete atualizado com sucesso',
            'reminder': {
                'id': reminder.id,
                'name': reminder.name,
                'message': reminder.message,
                'time': reminder.time,
                'is_active': reminder.is_active,
                'days': reminder.days,
                'reminder_type': reminder.reminder_type
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@reminders_bp.route('/reminders/<int:reminder_id>', methods=['DELETE'])
def delete_reminder(reminder_id):
    if not require_auth():
        return jsonify({'error': 'Não autenticado'}), 401
    
    try:
        user = get_current_user()
        reminder = PaymentReminder.query.filter_by(id=reminder_id, user_id=user.id).first()
        
        if not reminder:
            return jsonify({'error': 'Lembrete não encontrado'}), 404
        
        db.session.delete(reminder)
        db.session.commit()
        
        return jsonify({'message': 'Lembrete excluído com sucesso'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@reminders_bp.route('/reminders/<int:reminder_id>/toggle', methods=['POST'])
def toggle_reminder(reminder_id):
    if not require_auth():
        return jsonify({'error': 'Não autenticado'}), 401
    
    try:
        user = get_current_user()
        reminder = PaymentReminder.query.filter_by(id=reminder_id, user_id=user.id).first()
        
        if not reminder:
            return jsonify({'error': 'Lembrete não encontrado'}), 404
        
        reminder.is_active = not reminder.is_active
        db.session.commit()
        
        status = 'ativado' if reminder.is_active else 'desativado'
        return jsonify({'message': f'Lembrete {status} com sucesso'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@reminders_bp.route('/reminders/test/<int:reminder_id>', methods=['POST'])
def test_reminder(reminder_id):
    """Test a reminder by sending a sample message"""
    if not require_auth():
        return jsonify({'error': 'Não autenticado'}), 401
    
    try:
        user = get_current_user()
        reminder = PaymentReminder.query.filter_by(id=reminder_id, user_id=user.id).first()
        
        if not reminder:
            return jsonify({'error': 'Lembrete não encontrado'}), 404
        
        # Create a test message with sample variables
        test_message = reminder.message
        test_variables = {
            '{cliente}': 'Cliente Teste',
            '{valor}': 'R$ 500,00',
            '{dias}': str(reminder.days),
            '{data_vencimento}': '31/12/2024'
        }
        
        for variable, value in test_variables.items():
            test_message = test_message.replace(variable, value)
        
        return jsonify({
            'message': 'Teste realizado com sucesso',
            'test_message': test_message,
            'original_template': reminder.message
        })
        
    except Exception as e:
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500
