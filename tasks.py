from datetime import date
from app import db
from models import Receivable, Payable
import logging

def update_overdue_status():
    """
    Atualiza automaticamente o status de contas vencidas para 'overdue'
    """
    today = date.today()
    
    try:
        # Atualizar contas a receber em atraso
        overdue_receivables = Receivable.query.filter(
            Receivable.status == 'pending',
            Receivable.due_date < today
        ).all()
        
        receivables_count = 0
        for receivable in overdue_receivables:
            receivable.status = 'overdue'
            receivables_count += 1
        
        # Atualizar contas a pagar em atraso
        overdue_payables = Payable.query.filter(
            Payable.status == 'pending',
            Payable.due_date < today
        ).all()
        
        payables_count = 0
        for payable in overdue_payables:
            payable.status = 'overdue'
            payables_count += 1
        
        db.session.commit()
        
        if receivables_count > 0 or payables_count > 0:
            logging.info(f"Status atualizado: {receivables_count} contas a receber e {payables_count} contas a pagar marcadas como atrasadas")
        
        return {
            'success': True,
            'receivables_updated': receivables_count,
            'payables_updated': payables_count
        }
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Erro ao atualizar status de contas em atraso: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

def check_due_soon():
    """
    Retorna contas que vencem nos próximos 3 dias
    """
    from datetime import timedelta
    
    today = date.today()
    due_soon_date = today + timedelta(days=3)
    
    receivables_due_soon = Receivable.query.filter(
        Receivable.status == 'pending',
        Receivable.due_date >= today,
        Receivable.due_date <= due_soon_date
    ).count()
    
    payables_due_soon = Payable.query.filter(
        Payable.status == 'pending',
        Payable.due_date >= today,
        Payable.due_date <= due_soon_date
    ).count()
    
    return {
        'receivables_due_soon': receivables_due_soon,
        'payables_due_soon': payables_due_soon
    }