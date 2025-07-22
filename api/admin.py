from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from models import User, UserPlan, SystemSettings
from utils import admin_required, get_current_user
from datetime import datetime, timedelta
import requests
import logging
import os
import uuid

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
    duration_days = int(request.form.get('duration_days', 30))
    
    if not user_plan:
        user_plan = UserPlan(user_id=user_id)
        db.session.add(user_plan)
    
    # Set plan limits based on new plan structure
    if plan_name == 'Free':
        user_plan.max_clients = 5
        user_plan.max_receivables = 20
        user_plan.max_payables = 20
        user_plan.expires_at = None  # Plano gratuito não expira
    elif plan_name == 'Premium':
        user_plan.max_clients = 999999
        user_plan.max_receivables = 999999
        user_plan.max_payables = 999999
        # Definir expiração para planos Premium
        user_plan.expires_at = datetime.utcnow() + timedelta(days=duration_days)
    
    user_plan.plan_name = plan_name
    user_plan.is_active = True
    
    try:
        db.session.commit()
        
        expiry_text = ""
        if plan_name == 'Premium':
            expiry_date = user_plan.expires_at.strftime('%d/%m/%Y')
            expiry_text = f" (expira em {expiry_date})"
        
        flash(f'Plano do usuário {user.username} atualizado para {plan_name}{expiry_text}!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao atualizar plano: {str(e)}', 'error')
    
    return redirect(url_for('admin.index'))

@admin_bp.route('/users/<int:user_id>/extend_plan', methods=['POST'])
@admin_required
def extend_plan(user_id):
    """Estender duração do plano Premium"""
    user = User.query.get_or_404(user_id)
    user_plan = UserPlan.query.filter_by(user_id=user_id).first()
    
    if not user_plan or user_plan.plan_name != 'Premium':
        flash('Usuário não possui plano Premium para estender!', 'error')
        return redirect(url_for('admin.index'))
    
    days_to_add = int(request.form.get('days', 30))
    
    if user_plan.expires_at:
        # Se já tem data de expiração, adicionar mais dias
        user_plan.expires_at = user_plan.expires_at + timedelta(days=days_to_add)
    else:
        # Se não tem data de expiração, criar uma nova
        user_plan.expires_at = datetime.utcnow() + timedelta(days=days_to_add)
    
    try:
        db.session.commit()
        expiry_date = user_plan.expires_at.strftime('%d/%m/%Y')
        flash(f'Plano Premium de {user.username} estendido por {days_to_add} dias (expira em {expiry_date})!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao estender plano: {str(e)}', 'error')
    
    return redirect(url_for('admin.index'))

@admin_bp.route('/system_settings', methods=['POST'])
@admin_required
def update_system_settings():
    settings = SystemSettings.query.first()
    
    if not settings:
        settings = SystemSettings()
        db.session.add(settings)
    
    # Update basic settings
    settings.system_name = request.form.get('system_name')
    settings.system_domain = request.form.get('system_domain')
    settings.primary_color = request.form.get('primary_color')
    settings.secondary_color = request.form.get('secondary_color')
    settings.description = request.form.get('description')
    
    # Handle logo upload
    logo_file = request.files.get('logo_file')
    if logo_file and logo_file.filename:
        logo_url = handle_file_upload(logo_file, 'logo', max_size_mb=2)
        if logo_url:
            # Remove old logo if exists
            if settings.logo_url:
                remove_old_file(settings.logo_url)
            settings.logo_url = logo_url
    
    # Handle favicon upload
    favicon_file = request.files.get('favicon_file')
    if favicon_file and favicon_file.filename:
        favicon_url = handle_file_upload(favicon_file, 'favicon', max_size_mb=1)
        if favicon_url:
            # Remove old favicon if exists
            if settings.favicon_url:
                remove_old_file(settings.favicon_url)
            settings.favicon_url = favicon_url
    
    try:
        db.session.commit()
        flash('Configurações do sistema atualizadas!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao salvar configurações: {str(e)}', 'error')
    
    return redirect(url_for('admin.index'))

def handle_file_upload(file, file_type, max_size_mb=2):
    """Handle file upload for logo/favicon"""
    from werkzeug.utils import secure_filename
    try:
        from PIL import Image
    except ImportError:
        # Fallback if Pillow is not available
        flash('Sistema de processamento de imagens não disponível. Contate o administrador.', 'error')
        return None
    
    try:
        # Check file size
        file.seek(0, 2)  # Seek to end of file
        file_size = file.tell()
        file.seek(0)  # Reset to beginning
        
        if file_size > max_size_mb * 1024 * 1024:
            flash(f'Arquivo muito grande! Máximo {max_size_mb}MB.', 'error')
            return None
        
        # Create uploads directory
        upload_dir = 'static/uploads/system'
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate secure filename
        file_extension = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'png'
        filename = f"{file_type}_{uuid.uuid4().hex}.{file_extension}"
        filepath = os.path.join(upload_dir, filename)
        
        # Save and optimize image
        file.save(filepath)
        
        # Resize if needed (logo max 300x100, favicon max 32x32)
        if file_type == 'logo':
            max_size = (300, 100)
        else:  # favicon
            max_size = (32, 32)
        
        with Image.open(filepath) as img:
            # Convert to RGB if necessary (for PNG with transparency)
            if img.mode not in ('RGB', 'RGBA'):
                img = img.convert('RGBA')
            
            # Resize maintaining aspect ratio
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Save optimized image
            if file_extension.lower() == 'png':
                img.save(filepath, 'PNG', optimize=True)
            elif file_extension.lower() in ['jpg', 'jpeg']:
                if img.mode == 'RGBA':
                    img = img.convert('RGB')
                img.save(filepath, 'JPEG', optimize=True, quality=85)
            else:
                img.save(filepath)
        
        # Return URL path
        return f"/static/uploads/system/{filename}"
        
    except Exception as e:
        flash(f'Erro no upload: {str(e)}', 'error')
        return None

def remove_old_file(file_url):
    """Remove old uploaded file"""
    try:
        if file_url and file_url.startswith('/static/'):
            file_path = file_url[1:]  # Remove leading slash
            if os.path.exists(file_path):
                os.remove(file_path)
    except Exception:
        pass  # Silently ignore errors when removing old files

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

@admin_bp.route('/users/<int:user_id>/change_plan', methods=['POST'])
@admin_required
def change_user_plan(user_id):
    """Admin pode alterar plano de qualquer usuário com período personalizado"""
    user = User.query.get_or_404(user_id)
    
    plan_name = request.form.get('plan_name')
    days_duration = request.form.get('days_duration', type=int)
    
    if not plan_name or plan_name not in ['Free', 'Premium']:
        flash('Plano inválido!', 'error')
        return redirect(url_for('admin.index'))
    
    # Buscar ou criar plano do usuário
    user_plan = UserPlan.query.filter_by(user_id=user.id).first()
    if not user_plan:
        user_plan = UserPlan(user_id=user.id)
        db.session.add(user_plan)
    
    # Configurações do plano
    if plan_name == 'Free':
        user_plan.plan_name = 'Free'
        user_plan.max_clients = 5
        user_plan.max_receivables = 20
        user_plan.max_payables = 20
        user_plan.expires_at = None
        flash(f'Usuário {user.username} alterado para plano Gratuito!', 'success')
    else:  # Premium
        user_plan.plan_name = 'Premium'
        user_plan.max_clients = 999999
        user_plan.max_receivables = 999999
        user_plan.max_payables = 999999
        
        if days_duration and days_duration > 0:
            user_plan.expires_at = datetime.utcnow() + timedelta(days=days_duration)
            flash(f'Usuário {user.username} alterado para plano Premium por {days_duration} dias!', 'success')
        else:
            user_plan.expires_at = datetime.utcnow() + timedelta(days=30)  # Padrão 30 dias
            flash(f'Usuário {user.username} alterado para plano Premium por 30 dias!', 'success')
    
    user_plan.is_active = True
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao alterar plano: {str(e)}', 'error')
    
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
