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
