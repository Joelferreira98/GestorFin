#!/usr/bin/env python3
"""
Script para alterar senha de usuário manualmente
Uso: python change_password.py
"""
import sys
from werkzeug.security import generate_password_hash
from app import app, db
from models import User

def change_user_password(username, new_password):
    """Alterar senha de um usuário"""
    with app.app_context():
        # Buscar usuário
        user = User.query.filter_by(username=username).first()
        
        if not user:
            print(f"❌ Usuário '{username}' não encontrado!")
            return False
        
        # Gerar hash da nova senha
        password_hash = generate_password_hash(new_password)
        
        # Atualizar senha
        user.password_hash = password_hash
        db.session.commit()
        
        print(f"✅ Senha do usuário '{username}' alterada com sucesso!")
        print(f"📧 Email: {user.email}")
        print(f"👤 Admin: {'Sim' if user.is_admin else 'Não'}")
        return True

def main():
    print("=== ALTERAÇÃO DE SENHA ===\n")
    
    # Listar usuários disponíveis
    with app.app_context():
        users = User.query.all()
        if not users:
            print("❌ Nenhum usuário encontrado no banco!")
            return
        
        print("Usuários disponíveis:")
        for user in users:
            admin_label = " (ADMIN)" if user.is_admin else ""
            print(f"  • {user.username} - {user.email}{admin_label}")
        print()
    
    # Solicitar dados
    username = input("Digite o nome do usuário: ").strip()
    if not username:
        print("❌ Nome de usuário é obrigatório!")
        return
    
    new_password = input("Digite a nova senha: ").strip()
    if not new_password:
        print("❌ Nova senha é obrigatória!")
        return
    
    if len(new_password) < 6:
        print("❌ A senha deve ter pelo menos 6 caracteres!")
        return
    
    # Confirmar alteração
    confirm = input(f"Confirma alterar senha do usuário '{username}'? (s/N): ").strip().lower()
    if confirm not in ['s', 'sim', 'y', 'yes']:
        print("❌ Operação cancelada!")
        return
    
    # Executar alteração
    success = change_user_password(username, new_password)
    
    if success:
        print(f"\n🔐 Nova senha: {new_password}")
        print("⚠️  Anote a senha em local seguro e remova este script após o uso!")

if __name__ == "__main__":
    main()