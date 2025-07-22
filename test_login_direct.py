#!/usr/bin/env python3
"""
Teste direto do login via Flask test client
"""
from app import app, db
from models import User, UserPlan
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

def test_login():
    with app.test_client() as client:
        # Test login
        print("=== TESTING LOGIN DIRECTLY ===")
        
        response = client.post('/auth/login', data={
            'username': 'joel',
            'password': 'Admin@2025!'
        }, follow_redirects=False)
        
        print(f"Status Code: {response.status_code}")
        print(f"Location: {response.headers.get('Location')}")
        print(f"Content-Length: {len(response.data)}")
        
        if response.status_code == 302:
            print("✅ Redirect response - login likely successful")
        elif response.status_code == 200:
            print("⚠️  200 response - staying on login page")
            # Check for error messages in response
            if b'inv' in response.data.lower():
                print("❌ Contains 'inválido' - login failed")
            if b'sucesso' in response.data.lower():
                print("✅ Contains 'sucesso' - login successful")
                
        print(f"Response snippet: {response.data[:200]}...")
        
        # Test with follow redirects
        print("\n=== TESTING WITH FOLLOW REDIRECTS ===")
        response2 = client.post('/auth/login', data={
            'username': 'joel',
            'password': 'Admin@2025!'
        }, follow_redirects=True)
        
        print(f"Final Status Code: {response2.status_code}")
        print(f"Final URL: {response2.request.path if hasattr(response2, 'request') else 'Unknown'}")
        
        if b'Dashboard' in response2.data:
            print("✅ Reached Dashboard - login successful")
        elif b'Login' in response2.data:
            print("❌ Still on Login page - login failed")

if __name__ == "__main__":
    test_login()