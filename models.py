from datetime import datetime
from app import db
from werkzeug.security import generate_password_hash, check_password_hash
import uuid

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    phone = db.Column(db.String(20))
    phone_confirmed = db.Column(db.Boolean, default=False)  # WhatsApp confirmado
    profile_photo = db.Column(db.String(200))  # Caminho para foto de perfil
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    clients = db.relationship('Client', backref='user', lazy=True, cascade='all, delete-orphan')
    receivables = db.relationship('Receivable', backref='user', lazy=True, cascade='all, delete-orphan')
    payables = db.relationship('Payable', backref='user', lazy=True, cascade='all, delete-orphan')
    installment_sales = db.relationship('InstallmentSale', backref='user', lazy=True, cascade='all, delete-orphan')
    whatsapp_messages = db.relationship('WhatsAppMessage', backref='user', lazy=True, cascade='all, delete-orphan')
    payment_reminders = db.relationship('PaymentReminder', backref='user', lazy=True, cascade='all, delete-orphan')
    user_plan = db.relationship('UserPlan', backref='user', uselist=False, cascade='all, delete-orphan')
    whatsapp_instances = db.relationship('UserWhatsAppInstance', backref='user', lazy=True, cascade='all, delete-orphan')
    confirmation_tokens = db.relationship('PhoneConfirmationToken', backref='user', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)

class Client(db.Model):
    __tablename__ = 'clients'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    whatsapp = db.Column(db.String(20))
    document = db.Column(db.String(20))  # CPF/CNPJ
    email = db.Column(db.String(120))
    address = db.Column(db.Text)
    zip_code = db.Column(db.String(10))
    city = db.Column(db.String(80))
    state = db.Column(db.String(2))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    receivables = db.relationship('Receivable', backref='client', lazy=True)
    installment_sales = db.relationship('InstallmentSale', backref='client', lazy=True)
    whatsapp_messages = db.relationship('WhatsAppMessage', backref='client', lazy=True)

class Receivable(db.Model):
    __tablename__ = 'receivables'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, paid, overdue, cancelled
    type = db.Column(db.String(20), default='simple')  # simple, installment
    installment_number = db.Column(db.Integer)
    total_installments = db.Column(db.Integer)
    parent_id = db.Column(db.Integer, db.ForeignKey('installment_sales.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Payable(db.Model):
    __tablename__ = 'payables'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'))
    description = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, paid, overdue, cancelled
    category = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Supplier(db.Model):
    __tablename__ = 'suppliers'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    document = db.Column(db.String(20))  # CPF/CNPJ
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    payables = db.relationship('Payable', backref='supplier', lazy=True)

class InstallmentSale(db.Model):
    __tablename__ = 'installment_sales'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    installments = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, confirmed, approved, rejected, cancelled
    confirmation_token = db.Column(db.String(50), default=lambda: str(uuid.uuid4()))
    document_photo = db.Column(db.String(200))
    approval_notes = db.Column(db.Text)
    confirmed_at = db.Column(db.DateTime)
    approved_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    receivables = db.relationship('Receivable', foreign_keys='Receivable.parent_id', lazy=True)

class WhatsAppMessage(db.Model):
    __tablename__ = 'whatsapp_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    message_type = db.Column(db.String(50), nullable=False)  # confirmation, reminder, approval, rejection
    content = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, sent, failed
    template_type = db.Column(db.String(50))
    sent_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class PaymentReminder(db.Model):
    __tablename__ = 'payment_reminders'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    time = db.Column(db.Time, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    days = db.Column(db.Integer, nullable=False)  # Days before due date
    reminder_type = db.Column(db.String(20), default='due_date')  # due_date, overdue, follow_up
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class UserPlan(db.Model):
    __tablename__ = 'user_plans'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    plan_name = db.Column(db.String(50), default='Basic')  # Basic, Premium, Enterprise
    max_clients = db.Column(db.Integer, default=10)
    max_receivables = db.Column(db.Integer, default=50)
    max_payables = db.Column(db.Integer, default=50)
    is_active = db.Column(db.Boolean, default=True)
    expires_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class AutoReminderConfig(db.Model):
    __tablename__ = 'auto_reminder_configs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Configurações de lembretes de vencimento
    enable_due_reminders = db.Column(db.Boolean, default=True)
    days_before_due = db.Column(db.String(50), default='1,3,7')  # dias separados por vírgula
    
    # Configurações de lembretes de atraso
    enable_overdue_reminders = db.Column(db.Boolean, default=True)
    days_after_due = db.Column(db.String(50), default='1,3,7,15,30')  # dias separados por vírgula
    
    # Horário preferido para envio (formato HH:MM)
    preferred_time = db.Column(db.String(5), default='09:00')
    
    # Status ativo/inativo
    is_active = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamento
    user = db.relationship('User', backref='reminder_config')

class UserWhatsAppInstance(db.Model):
    __tablename__ = 'user_whatsapp_instances'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    instance_name = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(20))
    status = db.Column(db.String(20), default='disconnected')  # disconnected, connecting, connected
    qr_code = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class SystemSettings(db.Model):
    __tablename__ = 'system_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    system_name = db.Column(db.String(100), default='FinanceiroMax')
    system_domain = db.Column(db.String(200))
    logo_url = db.Column(db.String(200))
    favicon_url = db.Column(db.String(200))
    primary_color = db.Column(db.String(7), default='#007bff')
    secondary_color = db.Column(db.String(7), default='#6c757d')
    description = db.Column(db.Text)
    
    # Evolution API Settings
    evolution_api_url = db.Column(db.String(200))
    evolution_api_key = db.Column(db.String(100))
    evolution_default_instance = db.Column(db.String(100))
    evolution_webhook_url = db.Column(db.String(200))
    evolution_enabled = db.Column(db.Boolean, default=False)
    
    # AI Settings
    ai_enabled = db.Column(db.Boolean, default=False)
    ai_api_key = db.Column(db.Text)  # Armazenar API key criptografada
    ai_model = db.Column(db.String(50), default='gpt-4o')
    ai_temperature = db.Column(db.Float, default=0.3)
    ai_max_tokens = db.Column(db.Integer, default=2000)
    prediction_months = db.Column(db.Integer, default=3)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class PhoneConfirmationToken(db.Model):
    """Token para confirmação de número de WhatsApp"""
    __tablename__ = 'phone_confirmation_tokens'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    token = db.Column(db.String(6), nullable=False)  # Código de 6 dígitos
    phone = db.Column(db.String(20), nullable=False)
    is_used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    
    @staticmethod
    def generate_token():
        """Gerar código de confirmação de 6 dígitos"""
        import random
        return str(random.randint(100000, 999999))
    
    def is_expired(self):
        """Verificar se o token expirou"""
        return datetime.utcnow() > self.expires_at
