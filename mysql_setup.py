#!/usr/bin/env python3
"""
Script para configurar banco MySQL para FinanceiroMax
"""
import os
import sys
from urllib.parse import quote_plus
import mysql.connector
from mysql.connector import Error

def create_database_and_user():
    """Cria o banco de dados e usuário MySQL"""
    
    # Configurações
    root_password = input("Digite a senha root do MySQL: ")
    db_name = input("Nome do banco de dados (padrão: financeiro_max): ") or "financeiro_max"
    db_user = input("Nome do usuário do banco (padrão: financeiro_user): ") or "financeiro_user"
    db_password = input("Senha do usuário do banco: ")
    
    if not db_password:
        print("Senha é obrigatória!")
        return False
    
    try:
        # Conectar como root
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password=root_password
        )
        
        cursor = connection.cursor()
        
        # Criar banco de dados
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        print(f"✓ Banco de dados '{db_name}' criado/verificado")
        
        # Criar usuário
        cursor.execute(f"CREATE USER IF NOT EXISTS '{db_user}'@'localhost' IDENTIFIED BY '{db_password}'")
        print(f"✓ Usuário '{db_user}' criado/verificado")
        
        # Conceder privilégios
        cursor.execute(f"GRANT ALL PRIVILEGES ON {db_name}.* TO '{db_user}'@'localhost'")
        cursor.execute("FLUSH PRIVILEGES")
        print(f"✓ Privilégios concedidos ao usuário '{db_user}'")
        
        # Testar conexão com novo usuário
        test_connection = mysql.connector.connect(
            host='localhost',
            database=db_name,
            user=db_user,
            password=db_password
        )
        test_connection.close()
        print("✓ Conexão testada com sucesso")
        
        # Gerar DATABASE_URL
        encoded_password = quote_plus(db_password)
        database_url = f"mysql+pymysql://{db_user}:{encoded_password}@localhost/{db_name}"
        
        print("\n" + "="*50)
        print("CONFIGURAÇÃO CONCLUÍDA")
        print("="*50)
        print(f"Adicione esta linha ao seu arquivo .env:")
        print(f"DATABASE_URL={database_url}")
        print("="*50)
        
        return True
        
    except Error as e:
        print(f"Erro MySQL: {e}")
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def test_connection():
    """Testa a conexão com o banco"""
    database_url = input("Digite a DATABASE_URL para testar: ")
    
    try:
        # Extrair informações da URL
        if not database_url.startswith('mysql+pymysql://'):
            print("URL deve começar com mysql+pymysql://")
            return False
        
        # Usar SQLAlchemy para testar
        from sqlalchemy import create_engine
        
        engine = create_engine(database_url, echo=False)
        with engine.connect() as connection:
            result = connection.execute("SELECT 1")
            print("✓ Conexão com banco de dados bem-sucedida!")
            return True
            
    except Exception as e:
        print(f"Erro na conexão: {e}")
        return False

def main():
    print("=== Configuração MySQL para FinanceiroMax ===\n")
    
    while True:
        print("Escolha uma opção:")
        print("1. Criar banco e usuário")
        print("2. Testar conexão")
        print("3. Sair")
        
        choice = input("\nOpção: ").strip()
        
        if choice == '1':
            create_database_and_user()
        elif choice == '2':
            test_connection()
        elif choice == '3':
            print("Saindo...")
            break
        else:
            print("Opção inválida!")
        
        print("\n" + "-"*50 + "\n")

if __name__ == '__main__':
    main()