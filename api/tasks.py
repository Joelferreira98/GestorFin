from flask import Blueprint, jsonify, flash, redirect, url_for
from utils import login_required, admin_required, get_current_user
from tasks import update_overdue_status, check_due_soon

tasks_bp = Blueprint('tasks', __name__)

@tasks_bp.route('/update_overdue', methods=['POST'])
@login_required
def manual_update_overdue():
    """Executar manualmente a atualização de status de contas em atraso"""
    result = update_overdue_status()
    
    if result['success']:
        total_updated = result['receivables_updated'] + result['payables_updated']
        if total_updated > 0:
            flash(f'Sucesso! {result["receivables_updated"]} contas a receber e {result["payables_updated"]} contas a pagar marcadas como atrasadas.', 'success')
        else:
            flash('Nenhuma conta precisou ser atualizada.', 'info')
    else:
        flash(f'Erro ao atualizar contas: {result["error"]}', 'error')
    
    return redirect(url_for('dashboard.index'))

@tasks_bp.route('/status', methods=['GET'])
@login_required
def overdue_status():
    """API endpoint para verificar status de contas em atraso"""
    result = update_overdue_status()
    due_soon = check_due_soon()
    
    return jsonify({
        'overdue_update': result,
        'due_soon': due_soon
    })