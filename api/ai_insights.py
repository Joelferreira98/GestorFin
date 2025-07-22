from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app import db
from models import User, SystemSettings
from utils import login_required, get_current_user, admin_required
from ai_insights import financial_ai
from datetime import datetime
import logging

ai_insights_bp = Blueprint('ai_insights', __name__)

def check_premium_plan():
    """Verificar se o usuário tem plano Premium"""
    from flask import session
    user_plan = session.get('user_plan_name', 'Free')
    if user_plan != 'Premium':
        flash('IA Insights disponível apenas no plano Premium! Faça upgrade para acessar.', 'warning')
        return redirect(url_for('plans.index'))
    return None

@ai_insights_bp.route('/')
@login_required
def index():
    """Página principal de insights de IA"""
    # Verificar se o usuário tem plano Premium
    premium_check = check_premium_plan()
    if premium_check:
        return premium_check
        
    user = get_current_user()
    
    if not financial_ai.is_enabled():
        flash('IA não configurada. Solicite ao administrador para configurar a API key da OpenAI.', 'warning')
        return render_template('ai_insights.html', ai_enabled=False)
    
    return render_template('ai_insights.html', ai_enabled=True)

@ai_insights_bp.route('/cash_flow_prediction')
@login_required
def cash_flow_prediction():
    """API endpoint para predição de fluxo de caixa"""
    # Verificar plano Premium
    premium_check = check_premium_plan()
    if premium_check:
        return premium_check
        
    user = get_current_user()
    months_ahead = request.args.get('months', 3, type=int)
    
    prediction = financial_ai.get_cash_flow_prediction(user.id, months_ahead)
    return jsonify(prediction)

@ai_insights_bp.route('/client_risk_analysis')
@login_required
def client_risk_analysis():
    """API endpoint para análise de risco de clientes"""
    # Verificar plano Premium
    premium_check = check_premium_plan()
    if premium_check:
        return premium_check
        
    user = get_current_user()
    
    analysis = financial_ai.get_client_risk_analysis(user.id)
    return jsonify(analysis)

@ai_insights_bp.route('/business_insights')
@login_required
def business_insights():
    """API endpoint para insights do negócio"""
    # Verificar plano Premium
    premium_check = check_premium_plan()
    if premium_check:
        return premium_check
        
    user = get_current_user()
    
    insights = financial_ai.get_business_insights(user.id)
    return jsonify(insights)

@ai_insights_bp.route('/admin/config')
@admin_required
def admin_config():
    """Página de configuração da IA no painel admin"""
    settings = SystemSettings.query.first()
    if not settings:
        settings = SystemSettings()
        db.session.add(settings)
        db.session.commit()
    
    return render_template('admin/ai_config.html', settings=settings, ai_enabled=financial_ai.is_enabled())

@ai_insights_bp.route('/admin/update_config', methods=['POST'])
@admin_required
def update_config():
    """Atualizar configurações da IA"""
    settings = SystemSettings.query.first()
    if not settings:
        settings = SystemSettings()
        db.session.add(settings)
    
    # Atualizar configurações específicas da IA
    settings.ai_enabled = request.form.get('ai_enabled') == 'on'
    
    # Atualizar API key se fornecida
    api_key = request.form.get('ai_api_key', '').strip()
    if api_key:
        settings.ai_api_key = api_key
    
    settings.ai_model = request.form.get('ai_model', 'gpt-4o')
    settings.ai_temperature = float(request.form.get('ai_temperature', 0.3))
    settings.ai_max_tokens = int(request.form.get('ai_max_tokens', 2000))
    settings.prediction_months = int(request.form.get('prediction_months', 3))
    
    db.session.commit()
    
    # Atualizar cliente OpenAI com nova configuração
    financial_ai.update_client()
    
    flash('Configurações da IA atualizadas com sucesso!', 'success')
    return redirect(url_for('ai_insights.admin_config'))

@ai_insights_bp.route('/admin/test_ai', methods=['POST'])
@admin_required
def test_ai():
    """Testar conectividade da IA"""
    # Forçar atualização do cliente antes do teste
    financial_ai.update_client()
    
    if not financial_ai.is_enabled():
        return jsonify({
            'success': False, 
            'message': 'IA não configurada. Configure a API key da OpenAI no painel administrativo.'
        })
    
    try:
        # Teste simples
        response = financial_ai.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Você é um assistente de teste."},
                {"role": "user", "content": "Responda apenas 'OK' se você conseguir me ouvir."}
            ],
            max_tokens=10
        )
        
        if response.choices[0].message.content.strip().upper() == 'OK':
            return jsonify({'success': True, 'message': 'IA conectada e funcionando corretamente!'})
        else:
            return jsonify({'success': False, 'message': 'IA respondeu de forma inesperada.'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro ao testar IA: {str(e)}'})

@ai_insights_bp.route('/generate_report')
@login_required
def generate_report():
    """Gerar relatório completo com IA"""
    user = get_current_user()
    
    if not financial_ai.is_enabled():
        return jsonify({'error': 'IA não configurada'})
    
    try:
        # Gerar todos os insights
        cash_flow = financial_ai.get_cash_flow_prediction(user.id, 3)
        risk_analysis = financial_ai.get_client_risk_analysis(user.id)
        business_insights = financial_ai.get_business_insights(user.id)
        
        report = {
            'data_geracao': datetime.now().strftime('%d/%m/%Y %H:%M'),
            'fluxo_caixa': cash_flow,
            'analise_risco': risk_analysis,
            'insights_negocio': business_insights,
            'resumo_executivo': 'Relatório gerado com sucesso usando IA'
        }
        
        return jsonify(report)
        
    except Exception as e:
        return jsonify({'error': f'Erro ao gerar relatório: {str(e)}'})