#!/usr/bin/env python3
"""
Script de teste para Evolution API
Usado para debuggar problemas de conexão
"""

import requests
import json
import sys

def test_evolution_api():
    # Configurações do teste
    api_url = "https://evoapi.gestorstm.online"
    api_key = "f6c5b1b1a891fd02"
    
    print("=== TESTE EVOLUTION API ===")
    print(f"URL: {api_url}")
    print(f"API Key: {api_key}")
    print("-" * 50)
    
    # Teste 1: Fetch Instances (método atual)
    print("1. Testando fetchInstances (método atual)...")
    try:
        response = requests.get(
            f"{api_url}/instance/fetchInstances",
            headers={
                'apikey': api_key
            },
            timeout=10
        )
        
        print(f"   Status: {response.status_code}")
        print(f"   Headers da resposta: {dict(response.headers)}")
        print(f"   Resposta: {response.text}")
        
    except Exception as e:
        print(f"   Erro: {e}")
    
    print()
    
    # Teste 2: Com Content-Type
    print("2. Testando com Content-Type...")
    try:
        response = requests.get(
            f"{api_url}/instance/fetchInstances",
            headers={
                'apikey': api_key,
                'Content-Type': 'application/json'
            },
            timeout=10
        )
        
        print(f"   Status: {response.status_code}")
        print(f"   Resposta: {response.text}")
        
    except Exception as e:
        print(f"   Erro: {e}")
    
    print()
    
    # Teste 3: Authorization header
    print("3. Testando com Authorization header...")
    try:
        response = requests.get(
            f"{api_url}/instance/fetchInstances",
            headers={
                'Authorization': f'Bearer {api_key}'
            },
            timeout=10
        )
        
        print(f"   Status: {response.status_code}")
        print(f"   Resposta: {response.text}")
        
    except Exception as e:
        print(f"   Erro: {e}")
    
    print()
    
    # Teste 4: API Key como Authorization
    print("4. Testando Authorization com API Key...")
    try:
        response = requests.get(
            f"{api_url}/instance/fetchInstances",
            headers={
                'Authorization': api_key
            },
            timeout=10
        )
        
        print(f"   Status: {response.status_code}")
        print(f"   Resposta: {response.text}")
        
    except Exception as e:
        print(f"   Erro: {e}")
    
    print()
    
    # Teste 5: Como query parameter
    print("5. Testando como query parameter...")
    try:
        response = requests.get(
            f"{api_url}/instance/fetchInstances?apikey={api_key}",
            timeout=10
        )
        
        print(f"   Status: {response.status_code}")
        print(f"   Resposta: {response.text}")
        
    except Exception as e:
        print(f"   Erro: {e}")
    
    print()
    
    # Teste 6: Diferentes endpoints
    print("6. Testando endpoint alternativo...")
    try:
        response = requests.get(
            f"{api_url}/instance/list",
            headers={
                'apikey': api_key
            },
            timeout=10
        )
        
        print(f"   Status: {response.status_code}")
        print(f"   Resposta: {response.text}")
        
    except Exception as e:
        print(f"   Erro: {e}")
    
    print("\n=== FIM DOS TESTES ===")

if __name__ == "__main__":
    test_evolution_api()