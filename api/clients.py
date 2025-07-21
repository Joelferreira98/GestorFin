from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app import db
from models import Client, UserPlan
from utils import login_required, get_current_user, validate_cpf, validate_cnpj, format_phone
import re

clients_bp = Blueprint('clients', __name__)

@clients_bp.route('/')
@login_required
def index():
    user = get_current_user()
    clients = Client.query.filter_by(user_id=user.id).order_by(Client.created_at.desc()).all()
    return render_template('clients.html', clients=clients)

@clients_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    user = get_current_user()
    
    # Check plan limits
    user_plan = UserPlan.query.filter_by(user_id=user.id).first()
    current_clients = Client.query.filter_by(user_id=user.id).count()
    
    if current_clients >= user_plan.max_clients:
        flash(f'Limite de {user_plan.max_clients} clientes atingido para o plano {user_plan.plan_name}!', 'error')
        return redirect(url_for('clients.index'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        whatsapp = request.form.get('whatsapp')
        document = request.form.get('document')
        email = request.form.get('email')
        address = request.form.get('address')
        zip_code = request.form.get('zip_code')
        city = request.form.get('city')
        state = request.form.get('state')
        
        # Validate document
        if document:
            document = re.sub(r'[^\d]', '', document)
            if len(document) == 11:
                if not validate_cpf(document):
                    flash('CPF inválido!', 'error')
                    return render_template('clients.html', clients=Client.query.filter_by(user_id=user.id).all())
            elif len(document) == 14:
                if not validate_cnpj(document):
                    flash('CNPJ inválido!', 'error')
                    return render_template('clients.html', clients=Client.query.filter_by(user_id=user.id).all())
            else:
                flash('Documento deve ter 11 (CPF) ou 14 (CNPJ) dígitos!', 'error')
                return render_template('clients.html', clients=Client.query.filter_by(user_id=user.id).all())
        
        # Format WhatsApp
        if whatsapp:
            whatsapp = format_phone(whatsapp)
        
        client = Client(
            user_id=user.id,
            name=name,
            whatsapp=whatsapp,
            document=document,
            email=email,
            address=address,
            zip_code=zip_code,
            city=city,
            state=state
        )
        
        db.session.add(client)
        db.session.commit()
        
        flash('Cliente adicionado com sucesso!', 'success')
        return redirect(url_for('clients.index'))
    
    clients = Client.query.filter_by(user_id=user.id).order_by(Client.created_at.desc()).all()
    return render_template('clients.html', clients=clients)

@clients_bp.route('/edit/<int:client_id>', methods=['POST'])
@login_required
def edit(client_id):
    user = get_current_user()
    client = Client.query.filter_by(id=client_id, user_id=user.id).first_or_404()
    
    client.name = request.form.get('name')
    client.whatsapp = format_phone(request.form.get('whatsapp')) if request.form.get('whatsapp') else None
    client.document = request.form.get('document')
    client.email = request.form.get('email')
    client.address = request.form.get('address')
    client.zip_code = request.form.get('zip_code')
    client.city = request.form.get('city')
    client.state = request.form.get('state')
    
    db.session.commit()
    flash('Cliente atualizado com sucesso!', 'success')
    return redirect(url_for('clients.index'))

@clients_bp.route('/delete/<int:client_id>', methods=['POST'])
@login_required
def delete(client_id):
    user = get_current_user()
    client = Client.query.filter_by(id=client_id, user_id=user.id).first_or_404()
    
    db.session.delete(client)
    db.session.commit()
    
    flash('Cliente removido com sucesso!', 'success')
    return redirect(url_for('clients.index'))
