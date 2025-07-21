from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from models import Payable, Supplier, UserPlan
from utils import login_required, get_current_user
from datetime import datetime, date
from sqlalchemy import extract
from tasks import update_overdue_status

payables_bp = Blueprint('payables', __name__)

@payables_bp.route('/')
@login_required
def index():
    user = get_current_user()
    
    # Atualizar status de contas em atraso automaticamente
    update_overdue_status()
    
    # Get month and year filter from request
    filter_month = request.args.get('month', str(date.today().month), type=int)
    filter_year = request.args.get('year', str(date.today().year), type=int)
    
    # Filter payables by month and year
    payables = db.session.query(Payable, Supplier).outerjoin(Supplier).filter(
        Payable.user_id == user.id,
        extract('month', Payable.due_date) == filter_month,
        extract('year', Payable.due_date) == filter_year
    ).order_by(Payable.due_date.asc()).all()
    
    suppliers = Supplier.query.filter_by(user_id=user.id).all()
    
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
    
    return render_template('payables.html', 
                         payables=payables, 
                         suppliers=suppliers,
                         months=months,
                         years=years,
                         current_month=filter_month,
                         current_year=filter_year)

@payables_bp.route('/add', methods=['POST'])
@login_required
def add():
    user = get_current_user()
    
    # Check plan limits
    user_plan = UserPlan.query.filter_by(user_id=user.id).first()
    current_payables = Payable.query.filter_by(user_id=user.id).count()
    
    if current_payables >= user_plan.max_payables:
        flash(f'Limite de {user_plan.max_payables} contas a pagar atingido para o plano {user_plan.plan_name}!', 'error')
        return redirect(url_for('payables.index'))
    
    supplier_id = request.form.get('supplier_id') or None
    description = request.form.get('description')
    amount = request.form.get('amount')
    due_date = request.form.get('due_date')
    category = request.form.get('category')
    
    payable = Payable(
        user_id=user.id,
        supplier_id=supplier_id,
        description=description,
        amount=float(amount),
        due_date=datetime.strptime(due_date, '%Y-%m-%d').date(),
        category=category
    )
    
    db.session.add(payable)
    db.session.commit()
    
    flash('Conta a pagar adicionada com sucesso!', 'success')
    return redirect(url_for('payables.index'))

@payables_bp.route('/edit/<int:payable_id>', methods=['POST'])
@login_required
def edit(payable_id):
    user = get_current_user()
    payable = Payable.query.filter_by(id=payable_id, user_id=user.id).first_or_404()
    
    payable.supplier_id = request.form.get('supplier_id') or None
    payable.description = request.form.get('description')
    payable.amount = float(request.form.get('amount'))
    payable.due_date = datetime.strptime(request.form.get('due_date'), '%Y-%m-%d').date()
    payable.category = request.form.get('category')
    payable.status = request.form.get('status')
    
    db.session.commit()
    flash('Conta a pagar atualizada com sucesso!', 'success')
    return redirect(url_for('payables.index'))

@payables_bp.route('/delete/<int:payable_id>', methods=['POST'])
@login_required
def delete(payable_id):
    user = get_current_user()
    payable = Payable.query.filter_by(id=payable_id, user_id=user.id).first_or_404()
    
    db.session.delete(payable)
    db.session.commit()
    
    flash('Conta a pagar removida com sucesso!', 'success')
    return redirect(url_for('payables.index'))

@payables_bp.route('/mark_paid/<int:payable_id>', methods=['POST'])
@login_required
def mark_paid(payable_id):
    user = get_current_user()
    payable = Payable.query.filter_by(id=payable_id, user_id=user.id).first_or_404()
    
    payable.status = 'paid'
    db.session.commit()
    
    flash('Conta marcada como paga!', 'success')
    return redirect(url_for('payables.index'))

@payables_bp.route('/suppliers/add', methods=['POST'])
@login_required
def add_supplier():
    user = get_current_user()
    
    name = request.form.get('name')
    document = request.form.get('document')
    email = request.form.get('email')
    phone = request.form.get('phone')
    address = request.form.get('address')
    
    supplier = Supplier(
        user_id=user.id,
        name=name,
        document=document,
        email=email,
        phone=phone,
        address=address
    )
    
    db.session.add(supplier)
    db.session.commit()
    
    flash('Fornecedor adicionado com sucesso!', 'success')
    return redirect(url_for('payables.index'))
