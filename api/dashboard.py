from flask import Blueprint, render_template, session, redirect, url_for
from app import db
from models import User, Client, Receivable, Payable, InstallmentSale
from utils import login_required, get_current_user
from sqlalchemy import func
from datetime import datetime, timedelta

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    user = get_current_user()
    
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
    
    # Recent activities
    recent_receivables = db.session.query(Receivable, Client).join(Client).filter(
        Receivable.user_id == user.id
    ).order_by(Receivable.created_at.desc()).limit(5).all()
    
    recent_payables = Payable.query.filter_by(user_id=user.id).order_by(
        Payable.created_at.desc()
    ).limit(5).all()
    
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
