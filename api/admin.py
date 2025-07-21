from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from models import User, UserPlan, SystemSettings
from utils import admin_required, get_current_user
from datetime import datetime, timedelta

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/')
@admin_required
def index():
    users = User.query.order_by(User.created_at.desc()).all()
    system_settings = SystemSettings.query.first()
    
    # Statistics
    total_users = User.query.count()
    active_plans = UserPlan.query.filter_by(is_active=True).count()
    
    return render_template('admin.html', users=users, system_settings=system_settings,
                         total_users=total_users, active_plans=active_plans)

@admin_bp.route('/users/<int:user_id>/toggle_admin', methods=['POST'])
@admin_required
def toggle_admin(user_id):
    user = User.query.get_or_404(user_id)
    user.is_admin = not user.is_admin
    db.session.commit()
    
    status = 'promovido a' if user.is_admin else 'removido de'
    flash(f'Usuário {status} administrador!', 'success')
    return redirect(url_for('admin.index'))

@admin_bp.route('/users/<int:user_id>/update_plan', methods=['POST'])
@admin_required
def update_plan(user_id):
    user = User.query.get_or_404(user_id)
    user_plan = UserPlan.query.filter_by(user_id=user_id).first()
    
    plan_name = request.form.get('plan_name')
    
    if not user_plan:
        user_plan = UserPlan(user_id=user_id)
        db.session.add(user_plan)
    
    # Set plan limits based on plan name
    if plan_name == 'Basic':
        user_plan.max_clients = 10
        user_plan.max_receivables = 50
        user_plan.max_payables = 50
    elif plan_name == 'Premium':
        user_plan.max_clients = 50
        user_plan.max_receivables = 200
        user_plan.max_payables = 200
    elif plan_name == 'Enterprise':
        user_plan.max_clients = 999
        user_plan.max_receivables = 9999
        user_plan.max_payables = 9999
    
    user_plan.plan_name = plan_name
    user_plan.expires_at = datetime.utcnow() + timedelta(days=30)
    
    db.session.commit()
    
    flash(f'Plano do usuário atualizado para {plan_name}!', 'success')
    return redirect(url_for('admin.index'))

@admin_bp.route('/system_settings', methods=['POST'])
@admin_required
def update_system_settings():
    settings = SystemSettings.query.first()
    
    if not settings:
        settings = SystemSettings()
        db.session.add(settings)
    
    settings.system_name = request.form.get('system_name')
    settings.logo_url = request.form.get('logo_url')
    settings.favicon_url = request.form.get('favicon_url')
    settings.primary_color = request.form.get('primary_color')
    settings.secondary_color = request.form.get('secondary_color')
    settings.description = request.form.get('description')
    
    db.session.commit()
    
    flash('Configurações do sistema atualizadas!', 'success')
    return redirect(url_for('admin.index'))

@admin_bp.route('/evolution_api', methods=['POST'])
@admin_required
def update_evolution_api():
    settings = SystemSettings.query.first()
    
    if not settings:
        settings = SystemSettings()
        db.session.add(settings)
    
    # Clean and validate form inputs to prevent None concatenation
    api_url = request.form.get('evolution_api_url', '').strip()
    api_key = request.form.get('evolution_api_key', '').strip()
    default_instance = request.form.get('evolution_default_instance', '').strip()
    webhook_url = request.form.get('evolution_webhook_url', '').strip()
    
    # Remove any 'None' prefix that might have been accidentally added
    if api_key.startswith('None'):
        api_key = api_key[4:]  # Remove 'None' prefix
    
    settings.evolution_api_url = api_url if api_url else None
    settings.evolution_api_key = api_key if api_key else None
    settings.evolution_default_instance = default_instance if default_instance else None
    settings.evolution_webhook_url = webhook_url if webhook_url else None
    settings.evolution_enabled = 'evolution_enabled' in request.form
    
    db.session.commit()
    
    flash('Configurações da Evolution API atualizadas!', 'success')
    return redirect(url_for('admin.index'))

@admin_bp.route('/evolution_api/test', methods=['POST'])
@admin_required
def test_evolution_api():
    import requests
    import json
    
    settings = SystemSettings.query.first()
    
    if not settings or not settings.evolution_api_url or not settings.evolution_api_key:
        flash('Configure primeiro a URL e chave da Evolution API!', 'error')
        return redirect(url_for('admin.index'))
    
    try:
        # Debug: Log the exact configuration being used
        import logging
        logging.debug(f"Admin Test - API URL: '{settings.evolution_api_url}'")
        logging.debug(f"Admin Test - API Key: '{settings.evolution_api_key}'")
        logging.debug(f"Admin Test - API Key length: {len(settings.evolution_api_key) if settings.evolution_api_key else 'None'}")
        
        # Clean the API key and URL from any potential issues
        clean_api_key = settings.evolution_api_key.strip() if settings.evolution_api_key else ''
        clean_api_url = settings.evolution_api_url.rstrip('/') if settings.evolution_api_url else ''
        
        # Test connection to Evolution API using the correct structure
        response = requests.get(
            f"{clean_api_url}/instance/fetchInstances",
            headers={
                'apikey': clean_api_key
            },
            timeout=10
        )
        
        if response.status_code == 200:
            instances = response.json()
            instance_count = len(instances) if isinstance(instances, list) else 0
            flash(f'✓ Conexão com Evolution API bem-sucedida! {instance_count} instância(s) encontrada(s).', 'success')
        elif response.status_code == 401:
            flash('✗ Chave da API inválida ou incorreta. Verifique a chave no seu painel da Evolution API.', 'error')
        elif response.status_code == 404:
            flash('✗ URL da API incorreta ou serviço indisponível. Verifique a URL.', 'error')
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('message', f'Código de erro: {response.status_code}')
            except:
                error_msg = f'Código de erro: {response.status_code}'
            flash(f'✗ Erro na conexão: {error_msg}', 'error')
            
    except requests.exceptions.ConnectionError:
        flash('✗ Erro de conexão: Não foi possível conectar ao servidor. Verifique a URL.', 'error')
    except requests.exceptions.Timeout:
        flash('✗ Tempo limite esgotado: Servidor não respondeu em 10 segundos.', 'error')
    except requests.exceptions.RequestException as e:
        flash(f'✗ Erro de conexão: {str(e)}', 'error')
    
    return redirect(url_for('admin.index'))

@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@admin_required
def delete_user(user_id):
    current_user = get_current_user()
    
    if user_id == current_user.id:
        flash('Você não pode deletar sua própria conta!', 'error')
        return redirect(url_for('admin.index'))
    
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    
    flash('Usuário removido com sucesso!', 'success')
    return redirect(url_for('admin.index'))
