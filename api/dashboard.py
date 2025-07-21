from flask import Blueprint, render_template, session, redirect, url_for
from app import db
from models import User, Client, Receivable, Payable, InstallmentSale
from utils import login_required, get_current_user
from sqlalchemy import func
from datetime import datetime, timedelta
from tasks import update_overdue_status

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    user = get_current_user()
    
    # Atualizar status de contas em atraso automaticamente
    update_overdue_status()
    
    # Dashboard statistics
    total_clients = Client.query.filter_by(user_id=user.id).count()
    total_receivables = Receivable.query.filter_by(user_id=user.id).count()
    total_payables = Payable.query.filter_by(user_id=user.id).count()
    
    # Financial summary
    receivables_total = db.session.query(func.sum(Receivable.amount)).filter_by(
        user_id=user.id, status='pending'
    ).scalar() or 0
    
    payables_total = db.session.query(func.sum(Payable.amount)).filter_by(
        user_id=user.id, status='pending'
    ).scalar() or 0
    
    # Overdue counts
    today = datetime.now().date()
    overdue_receivables = Receivable.query.filter(
        Receivable.user_id == user.id,
        Receivable.status == 'pending',
        Receivable.due_date < today
    ).count()
    
    overdue_payables = Payable.query.filter(
        Payable.user_id == user.id,
        Payable.status == 'pending',
        Payable.due_date < today
    ).count()
    
    # Recent activities - agrupadas por conta (não parcelas individuais)
    import re
    
    # Buscar receivables e agrupar
    all_receivables = Receivable.query.filter_by(user_id=user.id).order_by(Receivable.created_at.desc()).all()
    receivables_grouped = {}
    
    for receivable in all_receivables:
        base_description = re.sub(r' - (Parcela|Mês) \d+.*', '', receivable.description)
        key = (base_description, receivable.client_id)
        
        if key not in receivables_grouped:
            receivables_grouped[key] = {
                'description': base_description,
                'client_id': receivable.client_id,
                'total_amount': 0,
                'first_due_date': receivable.due_date,
                'created_at': receivable.created_at,
                'status': receivable.status
            }
        
        receivables_grouped[key]['total_amount'] += receivable.amount
        if receivable.due_date < receivables_grouped[key]['first_due_date']:
            receivables_grouped[key]['first_due_date'] = receivable.due_date
    
    recent_receivables_data = sorted(receivables_grouped.values(), key=lambda x: x['created_at'], reverse=True)[:5]
    recent_receivables = []
    for r in recent_receivables_data:
        client = Client.query.get(r['client_id'])
        recent_receivables.append((type('obj', (object,), {
            'description': r['description'],
            'amount': r['total_amount'],
            'due_date': r['first_due_date'],
            'status': r['status']
        })(), client))
    
    # Buscar payables e agrupar
    all_payables = Payable.query.filter_by(user_id=user.id).order_by(Payable.created_at.desc()).all()
    payables_grouped = {}
    
    for payable in all_payables:
        base_description = re.sub(r' - (Parcela|Mês) \d+.*', '', payable.description)
        key = (base_description, payable.supplier_id)
        
        if key not in payables_grouped:
            payables_grouped[key] = {
                'description': base_description,
                'supplier_id': payable.supplier_id,
                'total_amount': 0,
                'first_due_date': payable.due_date,
                'created_at': payable.created_at,
                'status': payable.status
            }
        
        payables_grouped[key]['total_amount'] += payable.amount
        if payable.due_date < payables_grouped[key]['first_due_date']:
            payables_grouped[key]['first_due_date'] = payable.due_date
    
    recent_payables_data = sorted(payables_grouped.values(), key=lambda x: x['created_at'], reverse=True)[:5]
    recent_payables = []
    for p in recent_payables_data:
        recent_payables.append(type('obj', (object,), {
            'description': p['description'],
            'amount': p['total_amount'],
            'due_date': p['first_due_date'],
            'status': p['status']
        })())
    
    # Installment sales summary
    pending_sales = InstallmentSale.query.filter_by(user_id=user.id, status='pending').count()
    confirmed_sales = InstallmentSale.query.filter_by(user_id=user.id, status='confirmed').count()
    
    # Monthly revenue (paid receivables)
    current_month = datetime.now().replace(day=1)
    monthly_revenue = db.session.query(func.sum(Receivable.amount)).filter(
        Receivable.user_id == user.id,
        Receivable.status == 'paid',
        Receivable.created_at >= current_month
    ).scalar() or 0
    
    return render_template('dashboard.html',
                         total_clients=total_clients,
                         total_receivables=total_receivables,
                         total_payables=total_payables,
                         receivables_total=receivables_total,
                         payables_total=payables_total,
                         overdue_receivables=overdue_receivables,
                         overdue_payables=overdue_payables,
                         recent_receivables=recent_receivables,
                         recent_payables=recent_payables,
                         pending_sales=pending_sales,
                         confirmed_sales=confirmed_sales,
                         monthly_revenue=monthly_revenue)
