from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from models import Receivable, Client, UserPlan, InstallmentSale
from utils import login_required, get_current_user
from datetime import datetime, date
from sqlalchemy import and_, extract, or_

receivables_bp = Blueprint('receivables', __name__)

@receivables_bp.route('/')
@login_required
def index():
    user = get_current_user()
    
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
                         current_year=filter_year)

@receivables_bp.route('/add', methods=['POST'])
@login_required
def add():
    user = get_current_user()
    
    # Check plan limits
    user_plan = UserPlan.query.filter_by(user_id=user.id).first()
    current_receivables = Receivable.query.filter_by(user_id=user.id).count()
    
    if current_receivables >= user_plan.max_receivables:
        flash(f'Limite de {user_plan.max_receivables} contas a receber atingido para o plano {user_plan.plan_name}!', 'error')
        return redirect(url_for('receivables.index'))
    
    client_id = request.form.get('client_id')
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
    user = get_current_user()
    receivable = Receivable.query.filter_by(id=receivable_id, user_id=user.id).first_or_404()
    
    receivable.status = 'paid'
    db.session.commit()
    
    flash('Conta marcada como paga!', 'success')
    return redirect(url_for('receivables.index'))
