from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash
import os
import uuid
from PIL import Image
from app import db
from models import User
from utils import login_required, get_current_user

profile_bp = Blueprint('profile', __name__)

UPLOAD_FOLDER = 'static/uploads/profiles'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def ensure_upload_folder():
    """Garante que a pasta de uploads existe"""
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@profile_bp.route('/')
@login_required
def index():
    """Página de perfil do usuário"""
    user = get_current_user()
    if user is None:
        flash('Usuário não autenticado', 'error')
        return redirect(url_for('auth.login'))
    
    return render_template('profile.html', user=user)

@profile_bp.route('/update', methods=['POST'])
@login_required
def update():
    """Atualizar informações do perfil"""
    user = get_current_user()
    if user is None:
        flash('Usuário não autenticado', 'error')
        return redirect(url_for('auth.login'))
    
    try:
        # Atualizar nome de usuário
        new_username = request.form.get('username', '').strip()
        if new_username and new_username != user.username:
            # Verificar se username já existe
            existing_user = User.query.filter_by(username=new_username).first()
            if existing_user and existing_user.id != user.id:
                flash('Nome de usuário já está em uso', 'error')
                return redirect(url_for('profile.index'))
            user.username = new_username

        # Atualizar email
        new_email = request.form.get('email', '').strip()
        if new_email and new_email != user.email:
            # Verificar se email já existe
            existing_user = User.query.filter_by(email=new_email).first()
            if existing_user and existing_user.id != user.id:
                flash('Email já está em uso', 'error')
                return redirect(url_for('profile.index'))
            user.email = new_email

        # Atualizar telefone
        new_phone = request.form.get('phone', '').strip()
        if new_phone != user.phone:
            user.phone = new_phone

        db.session.commit()
        flash('Perfil atualizado com sucesso!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao atualizar perfil: {str(e)}', 'error')
    
    return redirect(url_for('profile.index'))

@profile_bp.route('/update-password', methods=['POST'])
@login_required
def update_password():
    """Atualizar senha do usuário"""
    user = get_current_user()
    if user is None:
        flash('Usuário não autenticado', 'error')
        return redirect(url_for('auth.login'))
    
    try:
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validar senha atual
        if not user.check_password(current_password):
            flash('Senha atual incorreta', 'error')
            return redirect(url_for('profile.index'))
        
        # Validar nova senha
        if len(new_password) < 6:
            flash('Nova senha deve ter pelo menos 6 caracteres', 'error')
            return redirect(url_for('profile.index'))
        
        if new_password != confirm_password:
            flash('Confirmação de senha não confere', 'error')
            return redirect(url_for('profile.index'))
        
        # Atualizar senha
        user.set_password(new_password)
        db.session.commit()
        flash('Senha atualizada com sucesso!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao atualizar senha: {str(e)}', 'error')
    
    return redirect(url_for('profile.index'))

@profile_bp.route('/upload-photo', methods=['POST'])
@login_required
def upload_photo():
    """Upload de foto de perfil"""
    user = get_current_user()
    if user is None:
        flash('Usuário não autenticado', 'error')
        return redirect(url_for('auth.login'))
    
    try:
        ensure_upload_folder()
        
        if 'profile_photo' not in request.files:
            flash('Nenhum arquivo selecionado', 'error')
            return redirect(url_for('profile.index'))
        
        file = request.files['profile_photo']
        
        if file.filename == '':
            flash('Nenhum arquivo selecionado', 'error')
            return redirect(url_for('profile.index'))
        
        if file and allowed_file(file.filename):
            # Gerar nome único para o arquivo
            filename = secure_filename(file.filename)
            file_extension = filename.rsplit('.', 1)[1].lower()
            unique_filename = f"user_{user.id}_{uuid.uuid4().hex[:8]}.{file_extension}"
            filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
            
            # Salvar arquivo
            file.save(filepath)
            
            # Redimensionar imagem para economizar espaço
            try:
                with Image.open(filepath) as img:
                    # Converter para RGB se necessário
                    if img.mode in ('RGBA', 'LA', 'P'):
                        img = img.convert('RGB')
                    
                    # Redimensionar mantendo proporção (max 400x400)
                    img.thumbnail((400, 400), Image.Resampling.LANCZOS)
                    img.save(filepath, optimize=True, quality=85)
            except Exception as img_error:
                flash(f'Erro ao processar imagem: {str(img_error)}', 'warning')
            
            # Remover foto anterior se existir
            if user.profile_photo and user.profile_photo != 'default-avatar.png':
                old_path = os.path.join('static', user.profile_photo)
                if os.path.exists(old_path):
                    try:
                        os.remove(old_path)
                    except:
                        pass  # Ignorar erro ao remover arquivo antigo
            
            # Atualizar banco de dados
            user.profile_photo = f"uploads/profiles/{unique_filename}"
            db.session.commit()
            
            flash('Foto de perfil atualizada com sucesso!', 'success')
        else:
            flash('Tipo de arquivo não permitido. Use PNG, JPG, JPEG, GIF ou WebP', 'error')
            
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao fazer upload da foto: {str(e)}', 'error')
    
    return redirect(url_for('profile.index'))

@profile_bp.route('/remove-photo', methods=['POST'])
@login_required
def remove_photo():
    """Remover foto de perfil"""
    user = get_current_user()
    if user is None:
        flash('Usuário não autenticado', 'error')
        return redirect(url_for('auth.login'))
    
    try:
        # Remover arquivo se existir
        if user.profile_photo and user.profile_photo != 'default-avatar.png':
            old_path = os.path.join('static', user.profile_photo)
            if os.path.exists(old_path):
                try:
                    os.remove(old_path)
                except:
                    pass  # Ignorar erro ao remover arquivo
        
        # Resetar para foto padrão
        user.profile_photo = None
        db.session.commit()
        
        flash('Foto de perfil removida com sucesso!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao remover foto: {str(e)}', 'error')
    
    return redirect(url_for('profile.index'))