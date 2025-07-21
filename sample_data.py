from app import db
from models import (User, Client, Receivable, Payable, Supplier, InstallmentSale, 
                   PaymentReminder, UserPlan, UserWhatsAppInstance, SystemSettings)
from datetime import datetime, timedelta, date, time
import uuid

def create_sample_data():
    """Create sample data if database is empty"""
    
    # Check if data already exists
    if User.query.first():
        return
    
    # Create admin user
    admin = User(
        username='joel',
        email='joel@financeiro.com',
        phone='11999999999',
        is_admin=True
    )
    admin.set_password('123456')
    db.session.add(admin)
    db.session.commit()
    
    # Create admin plan
    admin_plan = UserPlan(
        user_id=admin.id,
        plan_name='Enterprise',
        max_clients=999,
        max_receivables=9999,
        max_payables=9999
    )
    db.session.add(admin_plan)
    
    # Create sample users
    users_data = [
        {'username': 'maria', 'email': 'maria@email.com', 'phone': '11988888888', 'plan': 'Basic'},
        {'username': 'joao', 'email': 'joao@email.com', 'phone': '11977777777', 'plan': 'Premium'},
        {'username': 'ana', 'email': 'ana@email.com', 'phone': '11966666666', 'plan': 'Basic'}
    ]
    
    users = []
    for user_data in users_data:
        user = User(
            username=user_data['username'],
            email=user_data['email'],
            phone=user_data['phone']
        )
        user.set_password('123456')
        db.session.add(user)
        db.session.commit()
        
        # Create user plan
        plan_limits = {
            'Basic': {'clients': 10, 'receivables': 50, 'payables': 50},
            'Premium': {'clients': 50, 'receivables': 200, 'payables': 200},
            'Enterprise': {'clients': 999, 'receivables': 9999, 'payables': 9999}
        }
        
        limits = plan_limits[user_data['plan']]
        user_plan = UserPlan(
            user_id=user.id,
            plan_name=user_data['plan'],
            max_clients=limits['clients'],
            max_receivables=limits['receivables'],
            max_payables=limits['payables']
        )
        db.session.add(user_plan)
        users.append(user)
    
    # Create sample clients for admin
    clients_data = [
        {'name': 'João Silva', 'whatsapp': '5511999999999', 'document': '12345678901', 'email': 'joao@email.com', 'city': 'São Paulo', 'state': 'SP'},
        {'name': 'Maria Santos', 'whatsapp': '5511888888888', 'document': '98765432109', 'email': 'maria@email.com', 'city': 'Rio de Janeiro', 'state': 'RJ'},
        {'name': 'Empresa ABC Ltda', 'whatsapp': '5511777777777', 'document': '12345678000190', 'email': 'contato@abc.com', 'city': 'Belo Horizonte', 'state': 'MG'},
        {'name': 'Pedro Costa', 'whatsapp': '5511666666666', 'document': '11122233344', 'email': 'pedro@email.com', 'city': 'Salvador', 'state': 'BA'},
        {'name': 'Ana Oliveira', 'whatsapp': '5511555555555', 'document': '55566677788', 'email': 'ana@email.com', 'city': 'Curitiba', 'state': 'PR'},
        {'name': 'TechCorp S.A.', 'whatsapp': '5511444444444', 'document': '98765432000111', 'email': 'contato@techcorp.com', 'city': 'Porto Alegre', 'state': 'RS'},
        {'name': 'Carlos Mendes', 'whatsapp': '5511333333333', 'document': '99988877766', 'email': 'carlos@email.com', 'city': 'Fortaleza', 'state': 'CE'},
        {'name': 'Fernanda Lima', 'whatsapp': '5511222222222', 'document': '44455566677', 'email': 'fernanda@email.com', 'city': 'Recife', 'state': 'PE'}
    ]
    
    clients = []
    for client_data in clients_data:
        client = Client(
            user_id=admin.id,
            name=client_data['name'],
            whatsapp=client_data['whatsapp'],
            document=client_data['document'],
            email=client_data['email'],
            address=f"Rua das Flores, 123",
            zip_code='01234-567',
            city=client_data['city'],
            state=client_data['state']
        )
        db.session.add(client)
        clients.append(client)
    
    db.session.commit()
    
    # Create sample receivables
    receivables_data = [
        {'client_idx': 0, 'description': 'Serviço de consultoria', 'amount': 1500.00, 'days_offset': 10, 'status': 'pending'},
        {'client_idx': 1, 'description': 'Venda de produto A', 'amount': 2500.00, 'days_offset': 5, 'status': 'pending'},
        {'client_idx': 2, 'description': 'Projeto desenvolvimento', 'amount': 8000.00, 'days_offset': 15, 'status': 'pending'},
        {'client_idx': 3, 'description': 'Manutenção mensal', 'amount': 800.00, 'days_offset': -5, 'status': 'overdue'},
        {'client_idx': 4, 'description': 'Treinamento equipe', 'amount': 3200.00, 'days_offset': 20, 'status': 'pending'},
        {'client_idx': 5, 'description': 'Licença software', 'amount': 1200.00, 'days_offset': 7, 'status': 'pending'},
        {'client_idx': 6, 'description': 'Hospedagem anual', 'amount': 600.00, 'days_offset': -2, 'status': 'overdue'},
        {'client_idx': 7, 'description': 'Design gráfico', 'amount': 950.00, 'days_offset': 12, 'status': 'pending'},
        {'client_idx': 0, 'description': 'Suporte técnico', 'amount': 450.00, 'days_offset': 25, 'status': 'pending'},
        {'client_idx': 2, 'description': 'Análise de sistemas', 'amount': 2800.00, 'days_offset': 30, 'status': 'pending'},
        {'client_idx': 1, 'description': 'Pagamento recebido', 'amount': 1800.00, 'days_offset': -10, 'status': 'paid'},
        {'client_idx': 4, 'description': 'Consultoria paga', 'amount': 2200.00, 'days_offset': -15, 'status': 'paid'}
    ]
    
    for rec_data in receivables_data:
        receivable = Receivable(
            user_id=admin.id,
            client_id=clients[rec_data['client_idx']].id,
            description=rec_data['description'],
            amount=rec_data['amount'],
            due_date=date.today() + timedelta(days=rec_data['days_offset']),
            status=rec_data['status']
        )
        db.session.add(receivable)
    
    # Create sample suppliers
    suppliers_data = [
        {'name': 'Fornecedor ABC', 'document': '12345678000123', 'email': 'contato@abc.com', 'phone': '1133334444'},
        {'name': 'TechSupplier Ltda', 'document': '98765432000144', 'email': 'vendas@techsupplier.com', 'phone': '1155556666'},
        {'name': 'ServiçosPro S.A.', 'document': '11223344000155', 'email': 'financeiro@servicospro.com', 'phone': '1177778888'}
    ]
    
    suppliers = []
    for sup_data in suppliers_data:
        supplier = Supplier(
            user_id=admin.id,
            name=sup_data['name'],
            document=sup_data['document'],
            email=sup_data['email'],
            phone=sup_data['phone'],
            address='Av. Comercial, 456'
        )
        db.session.add(supplier)
        suppliers.append(supplier)
    
    db.session.commit()
    
    # Create sample payables
    payables_data = [
        {'supplier_idx': 0, 'description': 'Compra de equipamentos', 'amount': 5500.00, 'days_offset': 15, 'category': 'Equipamentos', 'status': 'pending'},
        {'supplier_idx': 1, 'description': 'Licenças de software', 'amount': 2400.00, 'days_offset': 10, 'category': 'Software', 'status': 'pending'},
        {'supplier_idx': 2, 'description': 'Serviços terceirizados', 'amount': 3200.00, 'days_offset': 20, 'category': 'Serviços', 'status': 'pending'},
        {'supplier_idx': 0, 'description': 'Manutenção preventiva', 'amount': 800.00, 'days_offset': -3, 'category': 'Manutenção', 'status': 'overdue'},
        {'supplier_idx': 1, 'description': 'Suporte técnico', 'amount': 1500.00, 'days_offset': 25, 'category': 'Suporte', 'status': 'pending'},
        {'supplier_idx': 2, 'description': 'Consultoria paga', 'amount': 4000.00, 'days_offset': -20, 'category': 'Consultoria', 'status': 'paid'}
    ]
    
    for pay_data in payables_data:
        payable = Payable(
            user_id=admin.id,
            supplier_id=suppliers[pay_data['supplier_idx']].id,
            description=pay_data['description'],
            amount=pay_data['amount'],
            due_date=date.today() + timedelta(days=pay_data['days_offset']),
            category=pay_data['category'],
            status=pay_data['status']
        )
        db.session.add(payable)
    
    # Create sample installment sales
    sales_data = [
        {'client_idx': 0, 'total_amount': 12000.00, 'installments': 6, 'description': 'Projeto completo de software', 'status': 'confirmed'},
        {'client_idx': 2, 'total_amount': 8500.00, 'installments': 4, 'description': 'Sistema de gestão empresarial', 'status': 'pending'}
    ]
    
    for sale_data in sales_data:
        sale = InstallmentSale(
            user_id=admin.id,
            client_id=clients[sale_data['client_idx']].id,
            total_amount=sale_data['total_amount'],
            installments=sale_data['installments'],
            description=sale_data['description'],
            status=sale_data['status'],
            confirmation_token=str(uuid.uuid4()),
            confirmed_at=datetime.utcnow() if sale_data['status'] == 'confirmed' else None
        )
        db.session.add(sale)
    
    # Create sample payment reminders
    reminders_data = [
        {'name': 'Lembrete 3 dias antes', 'message': 'Olá {cliente}! Sua conta de {valor} vence em 3 dias. Por favor, efetue o pagamento.', 'time': time(9, 0), 'days': 3, 'type': 'due_date'},
        {'name': 'Lembrete no vencimento', 'message': 'Olá {cliente}! Sua conta de {valor} vence hoje. Por favor, efetue o pagamento.', 'time': time(10, 0), 'days': 0, 'type': 'due_date'},
        {'name': 'Cobrança em atraso', 'message': 'Olá {cliente}! Sua conta de {valor} está em atraso. Por favor, regularize a situação.', 'time': time(14, 0), 'days': -1, 'type': 'overdue'}
    ]
    
    for rem_data in reminders_data:
        reminder = PaymentReminder(
            user_id=admin.id,
            name=rem_data['name'],
            message=rem_data['message'],
            time=rem_data['time'],
            days=rem_data['days'],
            reminder_type=rem_data['type']
        )
        db.session.add(reminder)
    
    # Create sample WhatsApp instances
    instance = UserWhatsAppInstance(
        user_id=admin.id,
        instance_name='financeiro_principal',
        phone_number='5511999999999',
        status='connected'
    )
    db.session.add(instance)
    
    # Create system settings
    settings = SystemSettings(
        system_name='FinanceiroMax',
        primary_color='#007bff',
        secondary_color='#6c757d',
        description='Sistema completo de gestão financeira'
    )
    db.session.add(settings)
    
    db.session.commit()
    print("Sample data created successfully!")
