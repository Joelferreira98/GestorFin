from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app import db
from models import User, UserPlan
from utils import login_required, get_current_user
from datetime import datetime, timedelta

plans_bp = Blueprint('plans', __name__)

# Definição dos planos disponíveis
PLANS = {
    'Free': {
        'name': 'Gratuito',
        'price': 0,
        'max_clients': 5,
        'max_receivables': 20,
        'max_payables': 20,
        'features': [
            '5 clientes cadastrados',
            '20 contas a receber',
            '20 contas a pagar',
            'Dashboard básico',
            'Suporte por email'
        ]
    },
    'Premium': {
        'name': 'Premium',
        'price': 29.90,
        'max_clients': 999999,
        'max_receivables': 999999,
        'max_payables': 999999,
        'features': [
            'Clientes ilimitados',
            'Contas a receber ilimitadas',
            'Contas a pagar ilimitadas',
            'Dashboard avançado',
            'IA Insights financeiros',
            'Integração WhatsApp',
            'Lembretes automáticos',
            'Vendas parceladas',
            'Suporte prioritário',
            'Relatórios avançados'
        ]
    }
}

@plans_bp.route('/')
@login_required
def index():
    """Página de planos e preços"""
    user = get_current_user()
    if not user:
        return redirect(url_for('auth.login'))
    
    # Buscar plano atual do usuário
    user_plan = UserPlan.query.filter_by(user_id=user.id).first()
    current_plan = user_plan.plan_name if user_plan else 'Free'
    
    # Calcular estatísticas de uso
    usage_stats = {
        'clients_count': len(user.clients),
        'receivables_count': len(user.receivables),
        'payables_count': len(user.payables)
    }
    
    return render_template('plans.html', 
                         plans=PLANS, 
                         current_plan=current_plan,
                         user_plan=user_plan,
                         usage_stats=usage_stats)

@plans_bp.route('/request_upgrade/<plan_name>')
@login_required
def request_upgrade(plan_name):
    """Solicitar upgrade de plano via WhatsApp do admin"""
    user = get_current_user()
    if not user:
        return redirect(url_for('auth.login'))
    
    if plan_name not in PLANS:
        flash('Plano inválido!', 'error')
        return redirect(url_for('plans.index'))
    
    # Buscar número do admin
    from models import User, UserWhatsAppInstance
    admin_user = User.query.filter_by(is_admin=True).first()
    if not admin_user:
        flash('Admin não encontrado. Contate o suporte.', 'error')
        return redirect(url_for('plans.index'))
    
    admin_instance = UserWhatsAppInstance.query.filter_by(
        user_id=admin_user.id,
        status='connected'
    ).first()
    
    if not admin_instance or not admin_instance.phone_number:
        flash('WhatsApp do admin não configurado. Contate o suporte.', 'error')
        return redirect(url_for('plans.index'))
    
    # Formatar número do admin para WhatsApp
    admin_phone = admin_instance.phone_number
    if not admin_phone.startswith('55'):
        admin_phone = '55' + admin_phone
    
    # Mensagem personalizada para o admin
    plan_info = PLANS[plan_name]
    current_plan = UserPlan.query.filter_by(user_id=user.id).first()
    current_plan_name = current_plan.plan_name if current_plan else 'Free'
    
    message = f"""🔄 *Solicitação de Mudança de Plano*

👤 *Usuário:* {user.username}
📧 *Email:* {user.email}
📱 *Telefone:* {user.phone or 'Não informado'}

📊 *Plano Atual:* {current_plan_name}
🎯 *Plano Solicitado:* {plan_info['name']}
💰 *Valor:* R$ {plan_info['price']:.2f}/mês

📋 *Recursos do plano:*
{chr(10).join(['• ' + feature for feature in plan_info['features'][:5]])}

Para aprovar, acesse o painel admin e altere o plano do usuário.

---
*FinanceiroMax - Solicitação Automática*"""
    
    # URL do WhatsApp com mensagem pré-formatada
    import urllib.parse
    encoded_message = urllib.parse.quote(message)
    whatsapp_url = f"https://wa.me/{admin_phone}?text={encoded_message}"
    
    return redirect(whatsapp_url)

@plans_bp.route('/upgrade/<plan_name>', methods=['POST'])
@login_required
def upgrade(plan_name):
    """Fazer upgrade para um plano (apenas para downgrade para Free)"""
    user = get_current_user()
    if not user:
        return redirect(url_for('auth.login'))
    
    if plan_name not in PLANS:
        flash('Plano inválido!', 'error')
        return redirect(url_for('plans.index'))
    
    # Apenas permitir mudança para plano gratuito diretamente
    if plan_name != 'Free':
        return redirect(url_for('plans.request_upgrade', plan_name=plan_name))
    
    # Buscar ou criar plano do usuário
    user_plan = UserPlan.query.filter_by(user_id=user.id).first()
    if not user_plan:
        user_plan = UserPlan(user_id=user.id)
        db.session.add(user_plan)
    
    plan_config = PLANS[plan_name]
    
    # Atualizar configurações do plano
    user_plan.plan_name = plan_name
    user_plan.max_clients = plan_config['max_clients']
    user_plan.max_receivables = plan_config['max_receivables']
    user_plan.max_payables = plan_config['max_payables']
    user_plan.is_active = True
    user_plan.expires_at = None  # Plano gratuito não expira
    
    flash('Plano alterado para Gratuito com sucesso!', 'success')
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao alterar plano: {str(e)}', 'error')
    
    return redirect(url_for('plans.index'))

@plans_bp.route('/check_limits')
@login_required
def check_limits():
    """API para verificar limites do plano atual"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Usuário não autenticado'}), 401
    
    user_plan = UserPlan.query.filter_by(user_id=user.id).first()
    if not user_plan:
        # Criar plano gratuito padrão se não existir
        user_plan = UserPlan(
            user_id=user.id,
            plan_name='Free',
            max_clients=PLANS['Free']['max_clients'],
            max_receivables=PLANS['Free']['max_receivables'],
            max_payables=PLANS['Free']['max_payables']
        )
        db.session.add(user_plan)
        db.session.commit()
    
    # Verificar se o plano expirou
    plan_expired = False
    if user_plan.expires_at and user_plan.expires_at < datetime.utcnow():
        plan_expired = True
        # Reverter para plano gratuito se expirou
        user_plan.plan_name = 'Free'
        user_plan.max_clients = PLANS['Free']['max_clients']
        user_plan.max_receivables = PLANS['Free']['max_receivables']
        user_plan.max_payables = PLANS['Free']['max_payables']
        user_plan.expires_at = None
        db.session.commit()
    
    # Calcular uso atual
    current_usage = {
        'clients': len(user.clients),
        'receivables': len(user.receivables),
        'payables': len(user.payables)
    }
    
    # Verificar limites
    limits_exceeded = {
        'clients': current_usage['clients'] >= user_plan.max_clients,
        'receivables': current_usage['receivables'] >= user_plan.max_receivables,
        'payables': current_usage['payables'] >= user_plan.max_payables
    }
    
    return jsonify({
        'plan_name': user_plan.plan_name,
        'plan_expired': plan_expired,
        'limits': {
            'max_clients': user_plan.max_clients,
            'max_receivables': user_plan.max_receivables,
            'max_payables': user_plan.max_payables
        },
        'usage': current_usage,
        'limits_exceeded': limits_exceeded,
        'expires_at': user_plan.expires_at.isoformat() if user_plan.expires_at else None
    })

def check_plan_limit(user, limit_type):
    """Função auxiliar para verificar se o usuário pode adicionar mais itens"""
    user_plan = UserPlan.query.filter_by(user_id=user.id).first()
    
    if not user_plan:
        # Criar plano gratuito padrão
        user_plan = UserPlan(
            user_id=user.id,
            plan_name='Free',
            max_clients=PLANS['Free']['max_clients'],
            max_receivables=PLANS['Free']['max_receivables'],
            max_payables=PLANS['Free']['max_payables']
        )
        db.session.add(user_plan)
        db.session.commit()
    
    # Verificar se o plano expirou
    if user_plan.expires_at and user_plan.expires_at < datetime.utcnow():
        # Reverter para plano gratuito
        user_plan.plan_name = 'Free'
        user_plan.max_clients = PLANS['Free']['max_clients']
        user_plan.max_receivables = PLANS['Free']['max_receivables']
        user_plan.max_payables = PLANS['Free']['max_payables']
        user_plan.expires_at = None
        db.session.commit()
    
    # Verificar limite específico
    if limit_type == 'clients':
        return len(user.clients) < user_plan.max_clients
    elif limit_type == 'receivables':
        return len(user.receivables) < user_plan.max_receivables
    elif limit_type == 'payables':
        return len(user.payables) < user_plan.max_payables
    
    return True

def get_plan_info(user):
    """Função auxiliar para obter informações do plano do usuário"""
    user_plan = UserPlan.query.filter_by(user_id=user.id).first()
    
    if not user_plan:
        return {
            'plan_name': 'Free',
            'plan_display_name': 'Gratuito',
            'is_premium': False,
            'expires_at': None
        }
    
    # Verificar se expirou
    if user_plan.expires_at and user_plan.expires_at < datetime.utcnow():
        user_plan.plan_name = 'Free'
        db.session.commit()
    
    return {
        'plan_name': user_plan.plan_name,
        'plan_display_name': PLANS.get(user_plan.plan_name, {}).get('name', user_plan.plan_name),
        'is_premium': user_plan.plan_name == 'Premium',
        'expires_at': user_plan.expires_at
    }