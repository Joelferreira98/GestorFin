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
    if user is None:
        flash('Usuário não autenticado', 'error')
        return redirect(url_for('auth.login'))
        
    config = AutoReminderConfig.query.filter_by(user_id=user.id).first()
    if not config:
        config = AutoReminderConfig()
        config.user_id = user.id
        db.session.add(config)
        db.session.commit()
    
    return render_template('reminders.html', config=config)

@reminders_bp.route('/update', methods=['POST'])
@login_required
def update():
    """Atualizar configurações de lembretes automáticos"""
    user = get_current_user()
    
    if user is None:
        flash('Usuário não autenticado', 'error')
        return redirect(url_for('auth.login'))
        
    config = AutoReminderConfig.query.filter_by(user_id=user.id).first()
    if not config:
        config = AutoReminderConfig()
        config.user_id = user.id
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
    """Testar sistema de lembretes"""
    user = get_current_user()
    
    if user is None:
        flash('Usuário não autenticado', 'error')
        return redirect(url_for('auth.login'))
    
    try:
        # Importar módulos necessários dentro da função para evitar imports circulares
        from models import Receivable, Client, Payable
        from datetime import datetime, timedelta
        import os
        
        # Verificar configuração de lembretes
        config = AutoReminderConfig.query.filter_by(user_id=user.id).first()
        if not config or not config.is_active:
            flash('Sistema de lembretes não está ativo. Ative-o primeiro nas configurações.', 'warning')
            return redirect(url_for('reminders.index'))
        
        # Verificar se existe instância WhatsApp configurada
        from models import UserWhatsAppInstance, SystemSettings
        
        # Verificar configurações do sistema
        system_settings = SystemSettings.query.first()
        if not system_settings or not system_settings.evolution_api_url or not system_settings.evolution_api_key:
            flash('WhatsApp não configurado no sistema. Configure a Evolution API no painel administrativo.', 'warning')
            return redirect(url_for('reminders.index'))
            
        # Verificar se existe instância conectada para o usuário
        whatsapp_instance = UserWhatsAppInstance.query.filter_by(user_id=user.id, status='connected').first()
        if not whatsapp_instance:
            flash('Nenhuma instância WhatsApp conectada encontrada. Conecte uma instância na seção WhatsApp.', 'warning')
            return redirect(url_for('reminders.index'))
        
        # Contar contas que receberiam lembretes
        today = datetime.now().date()
        
        # Contas próximas do vencimento (próximos 7 dias)
        due_soon_count = Receivable.query.join(Client).filter(
            Receivable.user_id == user.id,
            Receivable.status == 'pending',
            Receivable.due_date.between(today, today + timedelta(days=7))
        ).count()
        
        # Contas em atraso
        overdue_count = Receivable.query.join(Client).filter(
            Receivable.user_id == user.id,
            Receivable.status == 'pending',
            Receivable.due_date < today
        ).count()
        
        # Contas a pagar próximas
        payables_due_count = Payable.query.filter(
            Payable.user_id == user.id,
            Payable.status == 'pending',
            Payable.due_date.between(today, today + timedelta(days=7))
        ).count()
        
        test_result = {
            'due_soon': due_soon_count,
            'overdue': overdue_count,
            'payables_due': payables_due_count,
            'total_potential_reminders': due_soon_count + overdue_count
        }
        
        # Log do teste
        logging.info(f"Teste de lembretes executado para usuário {user.id}: {test_result}")
        
        if test_result['total_potential_reminders'] > 0:
            flash(f'✓ Sistema funcionando! Encontradas {test_result["total_potential_reminders"]} contas que receberiam lembretes: '
                  f'{due_soon_count} próximas do vencimento, {overdue_count} em atraso, '
                  f'{payables_due_count} contas a pagar.', 'success')
        else:
            flash('✓ Sistema funcionando! Nenhuma conta pendente encontrada para envio de lembretes no momento.', 'info')
            
    except Exception as e:
        logging.error(f"Erro no teste de lembretes: {str(e)}")
        flash(f'Erro no teste: {str(e)}', 'error')
    
    return redirect(url_for('reminders.index'))

@reminders_bp.route('/status')
@login_required
def status():
    """API endpoint para verificar status dos lembretes"""
    user = get_current_user()
    
    if user is None:
        return jsonify({'error': 'Usuário não autenticado'}), 401
    
    config = AutoReminderConfig.query.filter_by(user_id=user.id).first()
    
    return jsonify({
        'active': config.is_active if config else False,
        'due_reminders': config.enable_due_reminders if config else False,
        'overdue_reminders': config.enable_overdue_reminders if config else False,
        'preferred_time': config.preferred_time if config else '09:00'
    })