#!/usr/bin/env python3
"""
Debug do problema de login
"""
from app import app, db
from models import User
from werkzeug.security import check_password_hash

def debug_login():
    with app.app_context():
        username = 'joel'
        password = 'Admin@2025!'
        
        print("=== DEBUG LOGIN ===")
        print(f"Tentando login: {username} / {password}")
        
        # Buscar usuário
        user = User.query.filter_by(username=username).first()
        
        if not user:
            print("❌ Usuário não encontrado")
            return False
            
        print(f"✓ Usuário encontrado: {user.username} ({user.email})")
        print(f"✓ Is Admin: {user.is_admin}")
        print(f"✓ Hash: {user.password_hash[:50]}...")
        
        # Testar verificação de senha com ambos os métodos
        method1 = user.check_password(password)
        method2 = check_password_hash(user.password_hash, password)
        
        print(f"✓ user.check_password(): {method1}")
        print(f"✓ check_password_hash(): {method2}")
        
        if method1 and method2:
            print("✅ Senha correta - Login deveria funcionar")
        else:
            print("❌ Problema na verificação de senha")
            
        # Testar com senha antiga
        old_check = user.check_password('123456')
        print(f"✓ Senha antiga (123456): {old_check}")
        
        return method1 and method2

if __name__ == "__main__":
    debug_login()