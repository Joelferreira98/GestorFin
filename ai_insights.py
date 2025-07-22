"""
Módulo de insights e predições financeiras usando IA
Analisa dados financeiros e fornece previsões inteligentes
"""

import os
import json
from datetime import datetime, date, timedelta
from openai import OpenAI
from app import db
from models import Receivable, Payable, Client, User
import logging

logger = logging.getLogger(__name__)

class FinancialAI:
    def __init__(self):
        self.client = None
        self.enabled = False
    
    def _initialize_client(self):
        """Inicializa o cliente OpenAI com a API key do banco de dados"""
        try:
            from models import SystemSettings
            from app import app
            
            with app.app_context():
                settings = SystemSettings.query.first()
                if settings and settings.ai_enabled and settings.ai_api_key:
                    try:
                        self.client = OpenAI(api_key=settings.ai_api_key.strip())
                        self.enabled = True
                        return True
                    except Exception as e:
                        logging.error(f"Erro ao inicializar OpenAI client: {str(e)}")
                        self.client = None
                        self.enabled = False
                        return False
                else:
                    self.client = None
                    self.enabled = False
                    return False
        except Exception as e:
            logging.error(f"Erro ao acessar configurações da IA: {str(e)}")
            self.client = None
            self.enabled = False
            return False
    
    def update_client(self):
        """Atualiza o cliente quando as configurações mudam"""
        return self._initialize_client()
            
    def is_enabled(self):
        """Verifica se a IA está habilitada"""
        if not self.enabled or self.client is None:
            self._initialize_client()
        return self.enabled and self.client is not None
    
    def get_cash_flow_prediction(self, user_id, months_ahead=3):
        """Predição de fluxo de caixa"""
        if not self.is_enabled():
            return {"error": "IA não configurada. Configure a API key no painel admin."}
        
        try:
            # Coletar dados históricos
            historical_data = self._collect_historical_data(user_id, months=12)
            
            # Coletar dados futuros (contas agendadas)
            future_data = self._collect_future_data(user_id, months_ahead)
            
            # Preparar prompt para IA
            prompt = f"""
            Analise os dados financeiros abaixo e forneça uma predição de fluxo de caixa para os próximos {months_ahead} meses.

            DADOS HISTÓRICOS (últimos 12 meses):
            {json.dumps(historical_data, indent=2, ensure_ascii=False)}

            DADOS FUTUROS AGENDADOS:
            {json.dumps(future_data, indent=2, ensure_ascii=False)}

            Forneça uma análise em JSON com o seguinte formato:
            {{
                "predicao_mensal": [
                    {{"mes": "2025-01", "receita_prevista": 0, "gastos_previstos": 0, "saldo_previsto": 0}},
                    ...
                ],
                "tendencias": ["tendência 1", "tendência 2"],
                "recomendacoes": ["recomendação 1", "recomendação 2"],
                "alertas": ["alerta 1", "alerta 2"],
                "probabilidade_inadimplencia": 0.15,
                "melhor_mes_cobranca": "2025-02",
                "resumo": "Resumo executivo da análise"
            }}

            Considere sazonalidade, padrões de pagamento e tendências históricas.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "Você é um analista financeiro especialista em predições de fluxo de caixa para pequenas e médias empresas brasileiras."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            logger.error(f"Erro na predição de fluxo de caixa: {str(e)}")
            return {"error": f"Erro ao gerar predição: {str(e)}"}
    
    def get_client_risk_analysis(self, user_id):
        """Análise de risco de clientes"""
        if not self.is_enabled():
            return {"error": "IA não configurada"}
        
        try:
            # Coletar dados de clientes e histórico de pagamentos
            clients_data = self._collect_client_payment_history(user_id)
            
            prompt = f"""
            Analise o histórico de pagamentos dos clientes abaixo e classifique o risco de inadimplência de cada um.

            DADOS DOS CLIENTES:
            {json.dumps(clients_data, indent=2, ensure_ascii=False)}

            Forneça uma análise em JSON:
            {{
                "clientes_alto_risco": [
                    {{"nome": "Cliente", "risco": "alto", "probabilidade": 0.8, "motivo": "atrasos frequentes"}}
                ],
                "clientes_medio_risco": [...],
                "clientes_baixo_risco": [...],
                "recomendacoes_cobranca": {{
                    "Cliente X": "Cobrar com 5 dias de antecedência",
                    ...
                }},
                "resumo_geral": "Análise geral da carteira"
            }}
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "Você é um especialista em análise de risco de crédito e cobrança."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.2
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            logger.error(f"Erro na análise de risco: {str(e)}")
            return {"error": f"Erro ao gerar análise: {str(e)}"}
    
    def get_business_insights(self, user_id):
        """Insights gerais do negócio"""
        if not self.is_enabled():
            return {"error": "IA não configurada"}
        
        try:
            # Coletar dados abrangentes
            financial_summary = self._get_financial_summary(user_id)
            
            prompt = f"""
            Com base nos dados financeiros da empresa, forneça insights estratégicos para otimização do negócio.

            DADOS FINANCEIROS:
            {json.dumps(financial_summary, indent=2, ensure_ascii=False)}

            Forneça insights em JSON:
            {{
                "indicadores_performance": {{
                    "ticket_medio": 0,
                    "prazo_medio_recebimento": 0,
                    "taxa_inadimplencia": 0,
                    "crescimento_mensal": 0
                }},
                "oportunidades_melhoria": [
                    "Oportunidade 1: descrição e impacto potencial",
                    ...
                ],
                "alertas_financeiros": [
                    "Alerta 1: descrição e ação recomendada",
                    ...
                ],
                "previsao_crescimento": {{
                    "proximo_trimestre": 0.15,
                    "justificativa": "Baseado em tendências..."
                }},
                "recomendacoes_estrategicas": [
                    "Estratégia 1: implementação e benefícios",
                    ...
                ],
                "score_saude_financeira": 85
            }}
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "Você é um consultor financeiro especializado em análise estratégica de negócios."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            logger.error(f"Erro nos insights: {str(e)}")
            return {"error": f"Erro ao gerar insights: {str(e)}"}
    
    def _collect_historical_data(self, user_id, months=12):
        """Coleta dados históricos dos últimos X meses"""
        end_date = date.today()
        start_date = end_date - timedelta(days=months * 30)
        
        receivables = Receivable.query.filter(
            Receivable.user_id == user_id,
            Receivable.due_date >= start_date,
            Receivable.due_date <= end_date
        ).all()
        
        payables = Payable.query.filter(
            Payable.user_id == user_id,
            Payable.due_date >= start_date,
            Payable.due_date <= end_date
        ).all()
        
        # Agrupar por mês
        monthly_data = {}
        
        for r in receivables:
            month_key = r.due_date.strftime('%Y-%m')
            if month_key not in monthly_data:
                monthly_data[month_key] = {"receitas": 0, "gastos": 0}
            if r.status == 'paid':
                monthly_data[month_key]["receitas"] += float(r.amount)
        
        for p in payables:
            month_key = p.due_date.strftime('%Y-%m')
            if month_key not in monthly_data:
                monthly_data[month_key] = {"receitas": 0, "gastos": 0}
            if p.status == 'paid':
                monthly_data[month_key]["gastos"] += float(p.amount)
        
        return monthly_data
    
    def _collect_future_data(self, user_id, months_ahead=3):
        """Coleta dados futuros (contas agendadas)"""
        start_date = date.today()
        end_date = start_date + timedelta(days=months_ahead * 30)
        
        future_receivables = Receivable.query.filter(
            Receivable.user_id == user_id,
            Receivable.due_date >= start_date,
            Receivable.due_date <= end_date,
            Receivable.status.in_(['pending', 'overdue'])
        ).all()
        
        future_payables = Payable.query.filter(
            Payable.user_id == user_id,
            Payable.due_date >= start_date,
            Payable.due_date <= end_date,
            Payable.status.in_(['pending', 'overdue'])
        ).all()
        
        return {
            "contas_receber": [
                {
                    "valor": float(r.amount),
                    "vencimento": r.due_date.isoformat(),
                    "cliente": r.client.name if r.client else "N/A",
                    "status": r.status
                } for r in future_receivables
            ],
            "contas_pagar": [
                {
                    "valor": float(p.amount),
                    "vencimento": p.due_date.isoformat(),
                    "fornecedor": p.supplier.name if p.supplier else "N/A",
                    "status": p.status
                } for p in future_payables
            ]
        }
    
    def _collect_client_payment_history(self, user_id):
        """Coleta histórico de pagamentos por cliente"""
        clients = Client.query.filter_by(user_id=user_id).all()
        clients_data = []
        
        for client in clients:
            receivables = Receivable.query.filter_by(
                user_id=user_id, 
                client_id=client.id
            ).order_by(Receivable.due_date.desc()).all()
            
            payment_history = []
            total_amount = 0
            paid_amount = 0
            overdue_count = 0
            
            for r in receivables:
                payment_history.append({
                    "valor": float(r.amount),
                    "vencimento": r.due_date.isoformat(),
                    "status": r.status,
                    "dias_atraso": max(0, (date.today() - r.due_date).days) if r.status != 'paid' else 0
                })
                
                total_amount += float(r.amount)
                if r.status == 'paid':
                    paid_amount += float(r.amount)
                elif r.status == 'overdue':
                    overdue_count += 1
            
            clients_data.append({
                "nome": client.name,
                "documento": client.document,
                "whatsapp": client.whatsapp,
                "historico_pagamentos": payment_history[-10:],  # Últimos 10
                "total_negociado": total_amount,
                "total_pago": paid_amount,
                "contas_em_atraso": overdue_count,
                "score_pagamento": (paid_amount / total_amount * 100) if total_amount > 0 else 0
            })
        
        return clients_data
    
    def _get_financial_summary(self, user_id):
        """Resumo financeiro geral"""
        today = date.today()
        last_month = today - timedelta(days=30)
        last_3_months = today - timedelta(days=90)
        
        # Métricas gerais
        total_receivables = Receivable.query.filter_by(user_id=user_id).count()
        paid_receivables = Receivable.query.filter_by(user_id=user_id, status='paid').count()
        overdue_receivables = Receivable.query.filter_by(user_id=user_id, status='overdue').count()
        
        # Valores
        total_to_receive = db.session.query(db.func.sum(Receivable.amount)).filter(
            Receivable.user_id == user_id,
            Receivable.status.in_(['pending', 'overdue'])
        ).scalar() or 0
        
        total_received = db.session.query(db.func.sum(Receivable.amount)).filter(
            Receivable.user_id == user_id,
            Receivable.status == 'paid'
        ).scalar() or 0
        
        return {
            "resumo_geral": {
                "total_contas": total_receivables,
                "contas_pagas": paid_receivables,
                "contas_em_atraso": overdue_receivables,
                "valor_a_receber": float(total_to_receive),
                "valor_recebido": float(total_received)
            },
            "periodo_analise": {
                "data_inicio": last_3_months.isoformat(),
                "data_fim": today.isoformat()
            }
        }

# Instância global
financial_ai = FinancialAI()