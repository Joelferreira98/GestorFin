#!/usr/bin/env python3
"""
Gerar hash de senha para inserção manual no banco
Uso: python generate_hash.py
"""
from werkzeug.security import generate_password_hash
import sys

def main():
    if len(sys.argv) != 2:
        password = input("Digite a senha: ")
    else:
        password = sys.argv[1]
    
    if not password:
        print("Erro: senha não pode ser vazia")
        return
    
    # Gerar hash (mesmo método usado pelo sistema)
    password_hash = generate_password_hash(password)
    
    print(f"Senha: {password}")
    print(f"Hash: {password_hash}")
    print()
    print("SQL para atualizar:")
    print(f"UPDATE users SET password_hash = '{password_hash}' WHERE username = 'USUARIO';")

if __name__ == "__main__":
    main()