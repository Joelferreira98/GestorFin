from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from app import db
from models import InstallmentSale, Client, Receivable, WhatsAppMessage
from utils import login_required, get_current_user, send_whatsapp_message, generate_system_url
from datetime import datetime, timedelta
import uuid
import os

installment_sales_bp = Blueprint('installment_sales', __name__)

@installment_sales_bp.route('/')
@login_required
def index():
    user = get_current_user()
    sales = db.session.query(InstallmentSale, Client).join(Client).filter(
        InstallmentSale.user_id == user.id
    ).order_by(InstallmentSale.created_at.desc()).all()
    
    clients = Client.query.filter_by(user_id=user.id).all()
    return render_template('installment_sales.html', sales=sales, clients=clients)

@installment_sales_bp.route('/add', methods=['POST'])
@login_required
def add():
    user = get_current_user()
    
    client_id = request.form.get('client_id')
    total_amount = request.form.get('total_amount')
    installments = request.form.get('installments')
    description = request.form.get('description')
    
    sale = InstallmentSale(
        user_id=user.id,
        client_id=client_id,
        total_amount=float(total_amount),
        installments=int(installments),
        description=description,
        confirmation_token=str(uuid.uuid4())
    )
    
    db.session.add(sale)
    db.session.commit()
    
    # Send WhatsApp confirmation link
    client = Client.query.get(client_id)
    if client and client.whatsapp:
        confirmation_url = generate_system_url('installment_sales.confirm_public', token=sale.confirmation_token)
        message = f"Olá {client.name}! Você tem uma venda parcelada para confirmar. Acesse: {confirmation_url}"
        
        # Actually send the message via WhatsApp
        success = send_whatsapp_message(user.id, client.whatsapp, message)
        
        # Log message
        whatsapp_msg = WhatsAppMessage(
            user_id=user.id,
            client_id=client_id,
            message_type='confirmation',
            content=message,
            status='sent' if success else 'failed'
        )
        db.session.add(whatsapp_msg)
        db.session.commit()
    
    flash('Venda parcelada criada e link de confirmação enviado!', 'success')
    return redirect(url_for('installment_sales.index'))

@installment_sales_bp.route('/confirm/<token>')
def confirm_public(token):
    sale = InstallmentSale.query.filter_by(confirmation_token=token).first_or_404()
    
    if sale.status != 'pending':
        return render_template('public/confirm_sale.html', sale=sale, error='Esta venda já foi processada.')
    
    return render_template('public/confirm_sale.html', sale=sale)

@installment_sales_bp.route('/confirm/<token>', methods=['POST'])
def confirm_sale(token):
    sale = InstallmentSale.query.filter_by(confirmation_token=token).first_or_404()
    
    if sale.status != 'pending':
        flash('Esta venda já foi processada.', 'error')
        return redirect(url_for('installment_sales.confirm_public', token=token))
    
    # Handle file upload (document photo)
    document_photo = request.files.get('document_photo')
    if document_photo and document_photo.filename:
        import os
        from werkzeug.utils import secure_filename
        
        # Create uploads directory if it doesn't exist
        upload_dir = 'static/uploads/documents'
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate secure filename
        file_extension = document_photo.filename.rsplit('.', 1)[1].lower() if '.' in document_photo.filename else 'jpg'
        filename = f"doc_{sale.id}_{uuid.uuid4().hex}.{file_extension}"
        filepath = os.path.join(upload_dir, filename)
        
        # Save the file
        document_photo.save(filepath)
        sale.document_photo = filename
    
    sale.status = 'confirmed'
    sale.confirmed_at = datetime.utcnow()
    
    db.session.commit()
    
    return render_template('public/confirm_sale.html', sale=sale, success=True)

@installment_sales_bp.route('/approve/<int:sale_id>', methods=['POST'])
@login_required
def approve(sale_id):
    user = get_current_user()
    sale = InstallmentSale.query.filter_by(id=sale_id, user_id=user.id).first_or_404()
    
    if sale.status != 'confirmed':
        flash('Apenas vendas confirmadas podem ser aprovadas!', 'error')
        return redirect(url_for('installment_sales.index'))
    
    sale.status = 'approved'
    sale.approved_at = datetime.utcnow()
    sale.approval_notes = request.form.get('approval_notes')
    
    # Generate installment receivables
    installment_amount = sale.total_amount / sale.installments
    for i in range(sale.installments):
        due_date = datetime.now().date() + timedelta(days=30 * (i + 1))
        
        receivable = Receivable(
            user_id=user.id,
            client_id=sale.client_id,
            description=f"{sale.description} - Parcela {i+1}/{sale.installments}",
            amount=installment_amount,
            due_date=due_date,
            type='installment',
            installment_number=i+1,
            total_installments=sale.installments,
            parent_id=sale.id
        )
        db.session.add(receivable)
    
    db.session.commit()
    
    # Send WhatsApp approval notification
    client = Client.query.get(sale.client_id)
    if client and client.whatsapp:
        message = f"Olá {client.name}! Sua venda parcelada foi APROVADA. As parcelas foram geradas no sistema."
        
        # Actually send the message via WhatsApp
        success = send_whatsapp_message(user.id, client.whatsapp, message)
        
        whatsapp_msg = WhatsAppMessage(
            user_id=user.id,
            client_id=sale.client_id,
            message_type='approval',
            content=message,
            status='sent' if success else 'failed'
        )
        db.session.add(whatsapp_msg)
        db.session.commit()
    
    flash('Venda aprovada e parcelas geradas com sucesso!', 'success')
    return redirect(url_for('installment_sales.index'))

@installment_sales_bp.route('/reject/<int:sale_id>', methods=['POST'])
@login_required
def reject(sale_id):
    user = get_current_user()
    sale = InstallmentSale.query.filter_by(id=sale_id, user_id=user.id).first_or_404()
    
    rejection_notes = request.form.get('rejection_notes')
    send_new_link = request.form.get('send_new_link') == 'true'
    
    # If sending new link, reset sale status and generate new token
    if send_new_link:
        sale.status = 'pending'
        sale.confirmation_token = str(uuid.uuid4())
        sale.confirmed_at = None
        sale.document_photo = None
        sale.approval_notes = f"REJEITADO - {rejection_notes}"
    else:
        sale.status = 'rejected'
        sale.approval_notes = rejection_notes
    
    db.session.commit()
    
    # Send WhatsApp notification
    client = Client.query.get(sale.client_id)
    if client and client.whatsapp:
        if send_new_link:
            confirmation_url = generate_system_url('installment_sales.confirm_public', token=sale.confirmation_token)
            message = f"Olá {client.name}! Sua venda parcelada foi REJEITADA. Motivo: {rejection_notes}\n\nVocê pode enviar um novo documento através deste link: {confirmation_url}"
        else:
            message = f"Olá {client.name}! Infelizmente sua venda parcelada foi REJEITADA. Motivo: {rejection_notes}"
        
        # Actually send the message via WhatsApp
        success = send_whatsapp_message(user.id, client.whatsapp, message)
        
        whatsapp_msg = WhatsAppMessage(
            user_id=user.id,
            client_id=sale.client_id,
            message_type='rejection_with_resubmit' if send_new_link else 'rejection',
            content=message,
            status='sent' if success else 'failed'
        )
        db.session.add(whatsapp_msg)
        db.session.commit()
    
    if send_new_link:
        flash('Venda rejeitada e novo link enviado ao cliente!', 'success')
    else:
        flash('Venda rejeitada com sucesso!', 'success')
    
    return redirect(url_for('installment_sales.index'))

@installment_sales_bp.route('/regenerate_token/<int:sale_id>', methods=['POST'])
@login_required
def regenerate_token(sale_id):
    user = get_current_user()
    sale = InstallmentSale.query.filter_by(id=sale_id, user_id=user.id).first_or_404()
    
    sale.confirmation_token = str(uuid.uuid4())
    sale.status = 'pending'
    sale.confirmed_at = None
    sale.document_photo = None
    
    db.session.commit()
    
    flash('Token regenerado com sucesso!', 'success')
    return redirect(url_for('installment_sales.index'))

@installment_sales_bp.route('/delete/<int:sale_id>', methods=['POST'])
@login_required
def delete(sale_id):
    user = get_current_user()
    sale = InstallmentSale.query.filter_by(id=sale_id, user_id=user.id).first_or_404()
    
    # Delete related receivables if any
    Receivable.query.filter_by(parent_id=sale_id).delete()
    
    db.session.delete(sale)
    db.session.commit()
    
    flash('Venda parcelada removida com sucesso!', 'success')
    return redirect(url_for('installment_sales.index'))
