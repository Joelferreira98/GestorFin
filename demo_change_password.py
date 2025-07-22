#!/usr/bin/env python3
"""
Exemplo de alteração de senha
"""
from werkzeug.security import generate_password_hash
from app import app, db
from models import User

def demo_change_password():
    """Demonstrar como alterar senha"""
    with app.app_context():
        # Buscar usuário admin
        user = User.query.filter_by(username='joel').first()
        
        if not user:
            print("Usuário joel não encontrado!")
            return
        
        print(f"Usuário encontrado: {user.username} ({user.email})")
        print(f"Senha atual hash: {user.password_hash[:50]}...")
        
        # Exemplo: Nova senha forte
        new_password = "Admin@2025!"
        
        # Gerar hash da nova senha
        new_hash = generate_password_hash(new_password)
        
        print(f"\nNova senha: {new_password}")
        print(f"Novo hash: {new_hash}")
        
        # Para aplicar, descomente as linhas abaixo:
        # user.password_hash = new_hash
        # db.session.commit()
        # print("✅ Senha alterada com sucesso!")
        
        print("\n=== COMANDOS SQL EQUIVALENTES ===")
        print(f"UPDATE users SET password_hash = '{new_hash}' WHERE username = 'joel';")

if __name__ == "__main__":
    demo_change_password()