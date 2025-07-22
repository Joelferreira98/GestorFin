from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from models import Receivable, Payable, Client, Supplier, UserPlan, InstallmentSale, WhatsAppMessage
from utils import login_required, get_current_user, send_whatsapp_message, generate_system_url
from datetime import datetime, timedelta
import uuid

accounts_bp = Blueprint('accounts', __name__)

@accounts_bp.route('/')
@login_required
def index():
    """Página principal de cadastro de contas"""
    user = get_current_user()
    clients = Client.query.filter_by(user_id=user.id).all()
    suppliers = Supplier.query.filter_by(user_id=user.id).all()
    
    # Buscar contas recentes agrupadas (sem mostrar parcelas individuais)
    import re
    
    # Buscar todas as receivables e agrupar manualmente
    all_receivables = Receivable.query.filter_by(user_id=user.id).order_by(Receivable.created_at.desc()).all()
    receivables_grouped = {}
    
    for receivable in all_receivables:
        # Remove "- Parcela X" e "- Mês X" da descrição para agrupar
        base_description = re.sub(r' - (Parcela|Mês) \d+.*', '', receivable.description)
        key = (base_description, receivable.client_id)
        
        if key not in receivables_grouped:
            receivables_grouped[key] = {
                'description': base_description,
                'client_id': receivable.client_id,
                'total_amount': 0,
                'first_due_date': receivable.due_date,
                'created_at': receivable.created_at
            }
        
        receivables_grouped[key]['total_amount'] += receivable.amount
        if receivable.due_date < receivables_grouped[key]['first_due_date']:
            receivables_grouped[key]['first_due_date'] = receivable.due_date
    
    # Ordenar por data de criação e pegar os 5 mais recentes
    recent_receivables_data = sorted(receivables_grouped.values(), key=lambda x: x['created_at'], reverse=True)[:5]
    
    # Buscar todas as payables e agrupar manualmente
    all_payables = Payable.query.filter_by(user_id=user.id).order_by(Payable.created_at.desc()).all()
    payables_grouped = {}
    
    for payable in all_payables:
        # Remove "- Parcela X" e "- Mês X" da descrição para agrupar
        base_description = re.sub(r' - (Parcela|Mês) \d+.*', '', payable.description)
        key = (base_description, payable.supplier_id)
        
        if key not in payables_grouped:
            payables_grouped[key] = {
                'description': base_description,
                'supplier_id': payable.supplier_id,
                'total_amount': 0,
                'first_due_date': payable.due_date,
                'created_at': payable.created_at
            }
        
        payables_grouped[key]['total_amount'] += payable.amount
        if payable.due_date < payables_grouped[key]['first_due_date']:
            payables_grouped[key]['first_due_date'] = payable.due_date
    
    # Ordenar por data de criação e pegar os 5 mais recentes
    recent_payables_data = sorted(payables_grouped.values(), key=lambda x: x['created_at'], reverse=True)[:5]
    
    recent_installment_sales = InstallmentSale.query.filter_by(user_id=user.id).order_by(InstallmentSale.created_at.desc()).limit(5).all()
    
    # Calcular totais
    receivables_total = sum(r['total_amount'] for r in recent_receivables_data)
    payables_total = sum(p['total_amount'] for p in recent_payables_data)
    
    # Preparar dados estruturados para o template
    recent_receivables = []
    for r in recent_receivables_data:
        client = Client.query.get(r['client_id'])
        recent_receivables.append({
            'description': r['description'],
            'amount': r['total_amount'],
            'due_date': r['first_due_date'],
            'client': client
        })
    
    recent_payables = []
    for p in recent_payables_data:
        supplier = Supplier.query.get(p['supplier_id']) if p['supplier_id'] else None
        recent_payables.append({
            'description': p['description'],
            'amount': p['total_amount'],
            'due_date': p['first_due_date'],
            'supplier': supplier
        })
    
    return render_template('accounts.html', 
                         clients=clients, 
                         suppliers=suppliers,
                         recent_receivables=recent_receivables,
                         recent_payables=recent_payables,
                         recent_installment_sales=recent_installment_sales,
                         receivables_total=receivables_total,
                         payables_total=payables_total)

@accounts_bp.route('/add_receivable', methods=['POST'])
@login_required
def add_receivable():
    """Adicionar conta a receber"""
    user = get_current_user()
    
    # Check plan limits
    user_plan = UserPlan.query.filter_by(user_id=user.id).first()
    current_receivables = Receivable.query.filter_by(user_id=user.id).count()
    
    if current_receivables >= user_plan.max_receivables:
        flash(f'Limite de {user_plan.max_receivables} contas a receber atingido para o plano {user_plan.plan_name}!', 'error')
        return redirect(url_for('accounts.index'))
    
    account_type = request.form.get('account_type')
    client_id = request.form.get('client_id')
    description = request.form.get('description')
    amount = float(request.form.get('amount'))
    due_date = datetime.strptime(request.form.get('due_date'), '%Y-%m-%d').date()
    
    if account_type == 'simple':
        # Conta simples
        receivable = Receivable(
            user_id=user.id,
            client_id=client_id,
            description=description,
            amount=amount,
            due_date=due_date,
            type='simple'
        )
        db.session.add(receivable)
        db.session.commit()
        flash('Conta a receber simples criada com sucesso!', 'success')
        
    elif account_type == 'installment':
        # Conta parcelada com confirmação
        installments = int(request.form.get('installments'))
        needs_confirmation = request.form.get('needs_confirmation') == '1'
        
        if needs_confirmation:
            # Criar venda parcelada com confirmação
            sale = InstallmentSale(
                user_id=user.id,
                client_id=client_id,
                total_amount=amount,
                installments=installments,
                description=description,
                confirmation_token=str(uuid.uuid4())
            )
            db.session.add(sale)
            db.session.commit()
            
            # Enviar link de confirmação via WhatsApp
            client = Client.query.get(client_id)
            if client and client.whatsapp:
                confirmation_url = generate_system_url('installment_sales.confirm_public', token=sale.confirmation_token)
                message = f"Olá {client.name}! Você tem uma venda parcelada para confirmar. Acesse: {confirmation_url}"
                
                success = send_whatsapp_message(user.id, client.whatsapp, message)
                
                # Log message
                whatsapp_msg = WhatsAppMessage(
                    user_id=user.id,
                    client_id=client_id,
                    message_type='confirmation',
                    content=message,
                    status='sent' if success else 'failed'
                )
                db.session.add(whatsapp_msg)
                db.session.commit()
            
            flash('Venda parcelada criada e link de confirmação enviado!', 'success')
        else:
            # Criar parcelas diretamente sem confirmação
            installment_amount = amount / installments
            for i in range(installments):
                installment_due_date = due_date + timedelta(days=30 * i)
                receivable = Receivable(
                    user_id=user.id,
                    client_id=client_id,
                    description=f"{description} - Parcela {i+1}/{installments}",
                    amount=installment_amount,
                    due_date=installment_due_date,
                    type='installment',
                    installment_number=i+1,
                    total_installments=installments
                )
                db.session.add(receivable)
            
            db.session.commit()
            flash(f'Conta parcelada criada com {installments} parcelas!', 'success')
    
    elif account_type == 'recurring':
        # Conta recorrente
        recurrence_months = int(request.form.get('recurrence_months'))
        for i in range(recurrence_months):
            recurring_due_date = due_date + timedelta(days=30 * i)
            receivable = Receivable(
                user_id=user.id,
                client_id=client_id,
                description=f"{description} - Mês {i+1}",
                amount=amount,
                due_date=recurring_due_date,
                type='recurring'
            )
            db.session.add(receivable)
        
        db.session.commit()
        flash(f'Conta recorrente criada para {recurrence_months} meses!', 'success')
    
    return redirect(url_for('accounts.index'))

@accounts_bp.route('/add_payable', methods=['POST'])
@login_required
def add_payable():
    """Adicionar conta a pagar"""
    user = get_current_user()
    
    # Check plan limits
    user_plan = UserPlan.query.filter_by(user_id=user.id).first()
    current_payables = Payable.query.filter_by(user_id=user.id).count()
    
    if current_payables >= user_plan.max_payables:
        flash(f'Limite de {user_plan.max_payables} contas a pagar atingido para o plano {user_plan.plan_name}!', 'error')
        return redirect(url_for('accounts.index'))
    
    account_type = request.form.get('account_type')
    supplier_id = request.form.get('supplier_id') or None
    description = request.form.get('description')
    amount = float(request.form.get('amount'))
    due_date = datetime.strptime(request.form.get('due_date'), '%Y-%m-%d').date()
    category = request.form.get('category')
    
    if account_type == 'simple':
        # Conta simples
        payable = Payable(
            user_id=user.id,
            supplier_id=supplier_id,
            description=description,
            amount=amount,
            due_date=due_date,
            category=category
        )
        db.session.add(payable)
        db.session.commit()
        flash('Conta a pagar simples criada com sucesso!', 'success')
        
    elif account_type == 'installment':
        # Conta parcelada
        installments = int(request.form.get('installments'))
        installment_amount = amount / installments
        
        for i in range(installments):
            installment_due_date = due_date + timedelta(days=30 * i)
            payable = Payable(
                user_id=user.id,
                supplier_id=supplier_id,
                description=f"{description} - Parcela {i+1}/{installments}",
                amount=installment_amount,
                due_date=installment_due_date,
                category=category
            )
            db.session.add(payable)
        
        db.session.commit()
        flash(f'Conta parcelada criada com {installments} parcelas!', 'success')
    
    elif account_type == 'recurring':
        # Conta recorrente
        recurrence_months = int(request.form.get('recurrence_months'))
        for i in range(recurrence_months):
            recurring_due_date = due_date + timedelta(days=30 * i)
            payable = Payable(
                user_id=user.id,
                supplier_id=supplier_id,
                description=f"{description} - Mês {i+1}",
                amount=amount,
                due_date=recurring_due_date,
                category=category
            )
            db.session.add(payable)
        
        db.session.commit()
        flash(f'Conta recorrente criada para {recurrence_months} meses!', 'success')
    
    return redirect(url_for('accounts.index'))