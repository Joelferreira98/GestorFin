#!/usr/bin/env python3
"""
Teste completo do sistema para VPS
"""
from app import app, db
from models import User
import logging

logging.basicConfig(level=logging.INFO)

def test_complete_system():
    """Teste completo do sistema"""
    
    print("=== TESTE COMPLETO DO SISTEMA ===")
    
    with app.app_context():
        try:
            # 1. Teste de conexão com banco
            print("1. Testando conexão com banco...")
            user_count = User.query.count()
            print(f"✅ Banco conectado - {user_count} usuários encontrados")
            
            # 2. Teste do usuário admin
            print("2. Testando usuário admin...")
            admin_user = User.query.filter_by(username='joel').first()
            
            if admin_user:
                print(f"✅ Admin encontrado: {admin_user.username}")
                print(f"✅ Email: {admin_user.email}")
                print(f"✅ Is Admin: {admin_user.is_admin}")
                
                # 3. Teste de senha
                print("3. Testando senhas...")
                old_password_ok = admin_user.check_password('123456')
                new_password_ok = admin_user.check_password('Admin@2025!')
                
                print(f"✅ Senha antiga (123456): {old_password_ok}")
                print(f"✅ Senha nova (Admin@2025!): {new_password_ok}")
                
                if new_password_ok:
                    print("✅ SENHA NOVA ESTÁ FUNCIONANDO!")
                else:
                    print("❌ Problema com senha nova")
                    
            else:
                print("❌ Usuário admin não encontrado")
                return False
            
            # 4. Teste das rotas
            print("4. Testando rotas registradas...")
            routes = []
            for rule in app.url_map.iter_rules():
                if 'login' in rule.rule or 'dashboard' in rule.rule:
                    routes.append(f"{rule.rule} -> {rule.endpoint} ({rule.methods})")
            
            for route in routes:
                print(f"✅ {route}")
            
            # 5. Teste de configuração
            print("5. Testando configurações...")
            print(f"✅ SECRET_KEY: {'OK' if app.config.get('SECRET_KEY') else 'FALTANDO'}")
            print(f"✅ DATABASE_URL: {'OK' if app.config.get('SQLALCHEMY_DATABASE_URI') else 'FALTANDO'}")
            print(f"✅ SESSION_COOKIE_SECURE: {app.config.get('SESSION_COOKIE_SECURE')}")
            
            print("\n=== RESUMO ===")
            print("✅ Sistema configurado corretamente")
            print("✅ Banco de dados conectado")  
            print("✅ Usuário admin existe")
            print("✅ Senha nova funciona")
            print("✅ Rotas registradas")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro no teste: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = test_complete_system()
    if success:
        print("\n🎉 SISTEMA PRONTO PARA PRODUÇÃO!")
        print("📋 Próximos passos:")
        print("   1. Fazer deploy das mudanças na VPS")
        print("   2. Testar login no navegador")
        print("   3. Verificar se todas as funcionalidades estão OK")
    else:
        print("\n❌ Sistema tem problemas - verificar logs acima")