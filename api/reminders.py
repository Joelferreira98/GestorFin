from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app import db
from models import User, AutoReminderConfig
from utils import login_required, get_current_user
import logging

reminders_bp = Blueprint('reminders', __name__)

@reminders_bp.route('/')
@login_required
def index():
    """Página de configuração de lembretes automáticos"""
    user = get_current_user()
    
    # Buscar ou criar configuração de lembretes
    config = AutoReminderConfig.query.filter_by(user_id=user.id).first()
    if not config:
        config = AutoReminderConfig(user_id=user.id)
        db.session.add(config)
        db.session.commit()
    
    return render_template('reminders.html', config=config)

@reminders_bp.route('/update', methods=['POST'])
@login_required
def update():
    """Atualizar configurações de lembretes automáticos"""
    user = get_current_user()
    
    config = AutoReminderConfig.query.filter_by(user_id=user.id).first()
    if not config:
        config = AutoReminderConfig(user_id=user.id)
        db.session.add(config)
    
    # Atualizar configurações
    config.enable_due_reminders = request.form.get('enable_due_reminders') == 'on'
    config.enable_overdue_reminders = request.form.get('enable_overdue_reminders') == 'on'
    config.is_active = request.form.get('is_active') == 'on'
    
    # Dias antes do vencimento
    days_before = request.form.getlist('days_before_due')
    config.days_before_due = ','.join(days_before) if days_before else '1,3,7'
    
    # Dias após vencimento
    days_after = request.form.getlist('days_after_due')
    config.days_after_due = ','.join(days_after) if days_after else '1,3,7,15,30'
    
    # Horário preferido
    config.preferred_time = request.form.get('preferred_time', '09:00')
    
    db.session.commit()
    
    flash('Configurações de lembretes atualizadas com sucesso!', 'success')
    return redirect(url_for('reminders.index'))

@reminders_bp.route('/test', methods=['POST'])
@login_required
def test_reminder():
    """Testar envio de lembrete"""
    user = get_current_user()
    
    # Aqui você pode implementar um teste de envio
    flash('Teste de lembrete executado. Verifique os logs do sistema.', 'info')
    return redirect(url_for('reminders.index'))

@reminders_bp.route('/status')
@login_required
def status():
    """API endpoint para verificar status dos lembretes"""
    user = get_current_user()
    
    config = AutoReminderConfig.query.filter_by(user_id=user.id).first()
    
    return jsonify({
        'active': config.is_active if config else False,
        'due_reminders': config.enable_due_reminders if config else False,
        'overdue_reminders': config.enable_overdue_reminders if config else False,
        'preferred_time': config.preferred_time if config else '09:00'
    })