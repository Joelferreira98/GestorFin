from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from models import Receivable, Client, UserPlan, InstallmentSale
from utils import login_required, get_current_user, send_whatsapp_message
from datetime import datetime, date
from sqlalchemy import and_, extract, or_
from tasks import update_overdue_status

receivables_bp = Blueprint('receivables', __name__)

@receivables_bp.route('/')
@login_required
def index():
    user = get_current_user()
    
    # Atualizar status de contas em atraso automaticamente
    update_overdue_status()
    
    # Get month and year filter from request
    filter_month = request.args.get('month', str(date.today().month), type=int)
    filter_year = request.args.get('year', str(date.today().year), type=int)
    
    # Base query with client join
    base_query = db.session.query(Receivable, Client).join(Client).filter(
        Receivable.user_id == user.id
    )
    
    # Filter by month and year
    base_query = base_query.filter(
        extract('month', Receivable.due_date) == filter_month,
        extract('year', Receivable.due_date) == filter_year
    )
    
    # Filter out installment receivables from unapproved sales
    # Show regular receivables OR installment receivables from approved sales only
    receivables_query = base_query.filter(
        or_(
            Receivable.type != 'installment',  # Regular receivables
            and_(
                Receivable.type == 'installment',
                Receivable.parent_id.in_(
                    db.session.query(InstallmentSale.id).filter(
                        InstallmentSale.status == 'approved'
                    )
                )
            )
        )
    ).order_by(Receivable.due_date.asc())
    
    receivables = receivables_query.all()
    clients = Client.query.filter_by(user_id=user.id).all()
    
    # Generate month options for the filter
    months = [
        {'value': 1, 'name': 'Janeiro'},
        {'value': 2, 'name': 'Fevereiro'},
        {'value': 3, 'name': 'Março'},
        {'value': 4, 'name': 'Abril'},
        {'value': 5, 'name': 'Maio'},
        {'value': 6, 'name': 'Junho'},
        {'value': 7, 'name': 'Julho'},
        {'value': 8, 'name': 'Agosto'},
        {'value': 9, 'name': 'Setembro'},
        {'value': 10, 'name': 'Outubro'},
        {'value': 11, 'name': 'Novembro'},
        {'value': 12, 'name': 'Dezembro'},
    ]
    
    # Generate year options (current year and previous/next years)
    current_year = date.today().year
    years = list(range(current_year - 2, current_year + 3))
    
    return render_template('receivables.html', 
                         receivables=receivables, 
                         clients=clients,
                         months=months,
                         years=years,
                         current_month=filter_month,
                         current_year=filter_year,
                         today=date.today())



@receivables_bp.route('/send_reminder/<int:receivable_id>', methods=['POST'])
@login_required
def send_reminder(receivable_id):
    """Enviar lembrete de cobrança via WhatsApp"""
    user = get_current_user()
    receivable = Receivable.query.filter_by(id=receivable_id, user_id=user.id).first()
    
    if not receivable:
        flash('Conta não encontrada!', 'error')
        return redirect(url_for('receivables.index'))
    
    client = Client.query.get(receivable.client_id)
    if not client or not client.whatsapp:
        flash('Cliente não possui WhatsApp cadastrado!', 'error')
        return redirect(url_for('receivables.index'))
    
    # Validar formato do WhatsApp
    whatsapp = client.whatsapp.strip()
    if not whatsapp or len(whatsapp) < 10:
        flash('Número de WhatsApp inválido!', 'error')
        return redirect(url_for('receivables.index'))
    
    # Formatar mensagem de cobrança
    days_overdue = (datetime.now().date() - receivable.due_date).days
    
    if days_overdue > 0:
        message = f"""🔴 *CONTA EM ATRASO* 🔴

Olá {client.name}!

Temos uma conta em aberto em seu nome:

📋 *Descrição:* {receivable.description}
💰 *Valor:* R$ {receivable.amount:.2f}
📅 *Vencimento:* {receivable.due_date.strftime('%d/%m/%Y')}
⚠️ *Atraso:* {days_overdue} dias

Por favor, entre em contato para regularização.

Obrigado!"""
    else:
        days_to_due = (receivable.due_date - datetime.now().date()).days
        message = f"""💰 *LEMBRETE DE COBRANÇA* 💰

Olá {client.name}!

Lembramos que você possui uma conta a vencer:

📋 *Descrição:* {receivable.description}
💰 *Valor:* R$ {receivable.amount:.2f}
📅 *Vencimento:* {receivable.due_date.strftime('%d/%m/%Y')}
⏰ *Vence em:* {days_to_due} dias

Obrigado!"""
    
    # Enviar mensagem via WhatsApp
    success = send_whatsapp_message(user.id, client.whatsapp, message)
    
    if success:
        flash(f'Cobrança enviada via WhatsApp para {client.name} ({client.whatsapp})!', 'success')
    else:
        flash(f'Erro ao enviar cobrança: O número {client.whatsapp} não existe no WhatsApp ou não está válido. Verifique o número do cliente.', 'error')
    
    return redirect(url_for('receivables.index'))

@receivables_bp.route('/add', methods=['POST'])
@login_required
def add():
    user = get_current_user()
    
    # Check plan limits
    from api.plans import check_plan_limit
    if not check_plan_limit(user, 'receivables'):
        user_plan = UserPlan.query.filter_by(user_id=user.id).first()
        limit = user_plan.max_receivables if user_plan else 20
        flash(f'Limite de {limit} contas a receber atingido! Considere fazer upgrade para o plano Premium.', 'error')
        return redirect(url_for('receivables.index'))
    
    # Get client_id from hidden field or find by name
    client_id = request.form.get('client_id')
    client_name = request.form.get('client_name', '').strip()
    
    # If no client_id provided, try to find by name
    if not client_id and client_name:
        client = Client.query.filter_by(user_id=user.id, name=client_name).first()
        if client:
            client_id = client.id
        else:
            flash(f'Cliente "{client_name}" não encontrado. Por favor, selecione um cliente válido.', 'error')
            return redirect(url_for('receivables.index'))
    
    if not client_id:
        flash('Por favor, selecione um cliente válido.', 'error')
        return redirect(url_for('receivables.index'))
    
    description = request.form.get('description')
    amount = request.form.get('amount')
    due_date = request.form.get('due_date')
    
    receivable = Receivable(
        user_id=user.id,
        client_id=client_id,
        description=description,
        amount=float(amount),
        due_date=datetime.strptime(due_date, '%Y-%m-%d').date()
    )
    
    db.session.add(receivable)
    db.session.commit()
    
    flash('Conta a receber adicionada com sucesso!', 'success')
    return redirect(url_for('receivables.index'))

@receivables_bp.route('/edit/<int:receivable_id>', methods=['POST'])
@login_required
def edit(receivable_id):
    user = get_current_user()
    receivable = Receivable.query.filter_by(id=receivable_id, user_id=user.id).first_or_404()
    
    receivable.client_id = request.form.get('client_id')
    receivable.description = request.form.get('description')
    receivable.amount = float(request.form.get('amount'))
    receivable.due_date = datetime.strptime(request.form.get('due_date'), '%Y-%m-%d').date()
    receivable.status = request.form.get('status')
    
    db.session.commit()
    flash('Conta a receber atualizada com sucesso!', 'success')
    return redirect(url_for('receivables.index'))

@receivables_bp.route('/delete/<int:receivable_id>', methods=['POST'])
@login_required
def delete(receivable_id):
    user = get_current_user()
    receivable = Receivable.query.filter_by(id=receivable_id, user_id=user.id).first_or_404()
    
    db.session.delete(receivable)
    db.session.commit()
    
    flash('Conta a receber removida com sucesso!', 'success')
    return redirect(url_for('receivables.index'))

@receivables_bp.route('/mark_paid/<int:receivable_id>', methods=['POST'])
@login_required
def mark_paid(receivable_id):
    """Marcar conta como paga"""
    user = get_current_user()
    receivable = Receivable.query.filter_by(id=receivable_id, user_id=user.id).first()
    
    if not receivable:
        flash('Conta não encontrada!', 'error')
        return redirect(url_for('receivables.index'))
    
    if receivable.status == 'paid':
        flash('Esta conta já está marcada como paga!', 'warning')
        return redirect(url_for('receivables.index'))
    
    receivable.status = 'paid'
    db.session.commit()
    
    flash(f'Conta "{receivable.description}" marcada como paga!', 'success')
    return redirect(url_for('receivables.index'))
