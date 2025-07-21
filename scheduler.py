"""
Sistema de lembretes automáticos para FinanceiroMax
Executa tarefas agendadas para envio de lembretes via WhatsApp
"""

import threading
import time
from datetime import datetime, date, timedelta
from app import db
from models import Receivable, Payable, Client, User, UserPlan, AutoReminderConfig
from utils import send_whatsapp_message
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ReminderScheduler:
    def __init__(self):
        self.running = False
        self.thread = None
        
    def start(self):
        """Inicia o scheduler de lembretes"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
            self.thread.start()
            logger.info("Scheduler de lembretes iniciado")
            
    def stop(self):
        """Para o scheduler de lembretes"""
        self.running = False
        if self.thread:
            self.thread.join()
        logger.info("Scheduler de lembretes parado")
        
    def _run_scheduler(self):
        """Loop principal do scheduler"""
        while self.running:
            try:
                # Executa verificações a cada hora
                self._check_due_reminders()
                self._check_overdue_reminders()
                
                # Aguarda 1 hora (3600 segundos)
                time.sleep(3600)
                
            except Exception as e:
                logger.error(f"Erro no scheduler de lembretes: {str(e)}")
                time.sleep(300)  # Aguarda 5 minutos antes de tentar novamente
                
    def _check_due_reminders(self):
        """Verifica contas próximas do vencimento e envia lembretes"""
        from app import app, db
        
        with app.app_context():
            try:
                today = date.today()
                
                # Busca contas que vencem em 1, 3 e 7 dias
                for days_ahead in [1, 3, 7]:
                    due_date = today + timedelta(days=days_ahead)
                    
                    # Contas a receber
                    receivables = db.session.query(Receivable, Client, User).join(
                        Client, Receivable.client_id == Client.id
                    ).join(
                        User, Receivable.user_id == User.id
                    ).filter(
                        Receivable.due_date == due_date,
                        Receivable.status == 'pending'
                    ).all()
                    
                    for receivable, client, user in receivables:
                        self._send_due_reminder(receivable, client, user, days_ahead)
                        
                    # Contas a pagar
                    payables = db.session.query(Payable, User).join(
                        User, Payable.user_id == User.id
                    ).filter(
                        Payable.due_date == due_date,
                        Payable.status == 'pending'
                    ).all()
                    
                    for payable, user in payables:
                        self._send_payable_reminder(payable, user, days_ahead)
                        
            except Exception as e:
                logger.error(f"Erro ao verificar lembretes de vencimento: {str(e)}")
            
    def _check_overdue_reminders(self):
        """Verifica contas em atraso e envia lembretes"""
        from app import app, db
        
        with app.app_context():
            try:
                today = date.today()
                
                # Contas a receber em atraso
                overdue_receivables = db.session.query(Receivable, Client, User).join(
                    Client, Receivable.client_id == Client.id
                ).join(
                    User, Receivable.user_id == User.id
                ).filter(
                    Receivable.due_date < today,
                    Receivable.status.in_(['pending', 'overdue'])
                ).all()
                
                for receivable, client, user in overdue_receivables:
                    days_overdue = (today - receivable.due_date).days
                    
                    # Envia lembrete nos dias 1, 3, 7, 15 e 30 após vencimento
                    if days_overdue in [1, 3, 7, 15, 30]:
                        self._send_overdue_reminder(receivable, client, user, days_overdue)
                        
            except Exception as e:
                logger.error(f"Erro ao verificar lembretes de atraso: {str(e)}")
            
    def _send_due_reminder(self, receivable, client, user, days_ahead):
        """Envia lembrete de conta próxima do vencimento"""
        if not client.whatsapp:
            return
            
        message = f"""⏰ *LEMBRETE DE VENCIMENTO* ⏰

Olá {client.name}!

Sua conta vence em {days_ahead} dia{'s' if days_ahead > 1 else ''}:

📋 *Descrição:* {receivable.description}
💰 *Valor:* R$ {receivable.amount:.2f}
📅 *Vencimento:* {receivable.due_date.strftime('%d/%m/%Y')}

Para evitar juros, efetue o pagamento até a data de vencimento.

Obrigado!"""

        success = send_whatsapp_message(user.id, client.whatsapp, message)
        
        if success:
            logger.info(f"Lembrete de vencimento enviado: {client.name} - {receivable.description}")
        else:
            logger.warning(f"Falha ao enviar lembrete: {client.name} - {client.whatsapp}")
            
    def _send_overdue_reminder(self, receivable, client, user, days_overdue):
        """Envia lembrete de conta em atraso"""
        if not client.whatsapp:
            return
            
        message = f"""🔴 *CONTA EM ATRASO* 🔴

Olá {client.name}!

Temos uma conta em aberto em seu nome:

📋 *Descrição:* {receivable.description}
💰 *Valor:* R$ {receivable.amount:.2f}
📅 *Vencimento:* {receivable.due_date.strftime('%d/%m/%Y')}
⚠️ *Atraso:* {days_overdue} dias

Por favor, entre em contato urgentemente para regularização.

Obrigado!"""

        success = send_whatsapp_message(user.id, client.whatsapp, message)
        
        if success:
            logger.info(f"Lembrete de atraso enviado: {client.name} - {receivable.description}")
            
            # Marcar como overdue se ainda não estiver
            if receivable.status != 'overdue':
                receivable.status = 'overdue'
                db.session.commit()
        else:
            logger.warning(f"Falha ao enviar lembrete de atraso: {client.name} - {client.whatsapp}")
            
    def _send_payable_reminder(self, payable, user, days_ahead):
        """Envia lembrete interno de conta a pagar"""
        # Este seria um lembrete interno para o próprio usuário
        # Poderia ser via email, notificação no sistema, etc.
        logger.info(f"Lembrete interno: Conta a pagar vence em {days_ahead} dias - {payable.description}")

# Instância global do scheduler
reminder_scheduler = ReminderScheduler()

def start_reminder_system():
    """Inicia o sistema de lembretes automáticos"""
    reminder_scheduler.start()
    
def stop_reminder_system():
    """Para o sistema de lembretes automáticos"""
    reminder_scheduler.stop()