#!/usr/bin/env python3
"""
Test session configuration
"""
from app import app
import os

def test_session():
    print("=== SESSION CONFIGURATION ===")
    print(f"SECRET_KEY: {bool(app.config.get('SECRET_KEY'))}")
    print(f"SECRET_KEY length: {len(app.config.get('SECRET_KEY', ''))}")
    print(f"SESSION_COOKIE_SECURE: {app.config.get('SESSION_COOKIE_SECURE')}")
    print(f"SESSION_COOKIE_HTTPONLY: {app.config.get('SESSION_COOKIE_HTTPONLY')}")
    print(f"SESSION_COOKIE_SAMESITE: {app.config.get('SESSION_COOKIE_SAMESITE')}")
    
    print("\n=== ENVIRONMENT ===")
    print(f"SESSION_SECRET env: {bool(os.environ.get('SESSION_SECRET'))}")
    
    print("\n=== APP CONFIG ===")
    for key in sorted(app.config.keys()):
        if 'SESSION' in key or 'SECRET' in key or 'COOKIE' in key:
            value = app.config[key]
            if isinstance(value, str) and len(value) > 20:
                print(f"{key}: {value[:20]}...")
            else:
                print(f"{key}: {value}")

if __name__ == "__main__":
    test_session()