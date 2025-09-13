#!/usr/bin/env python3
"""
Script de debug para testar o endpoint /v1/student/partners
"""

import asyncio
import json
import os
import sys

# Adicionar o diretório src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import httpx
from src.auth import verify_token
from src.config import TESTING_MODE, ENVIRONMENT


async def test_token_verification():
    """Testa a verificação de token diretamente."""
    print(f"TESTING_MODE: {TESTING_MODE}")
    print(f"ENVIRONMENT: {ENVIRONMENT}")
    print()
    
    # Testar com token mock em modo de desenvolvimento
    test_token = "mock-token-for-testing"
    
    try:
        print("=== Testando verify_token diretamente ===")
        payload = await verify_token(test_token)
        print(f"Token verificado com sucesso:")
        print(f"  sub: {payload.sub}")
        print(f"  role: {payload.role}")
        print(f"  tenant: {payload.tenant}")
        print(f"  exp: {payload.exp}")
        print(f"  iat: {payload.iat}")
        print()
        
    except Exception as e:
        print(f"Erro na verificação do token: {e}")
        import traceback
        traceback.print_exc()
        print()


async def test_student_partners_with_real_request():
    """Testa o endpoint de parceiros para estudantes com requisição real."""
    base_url = "http://localhost:8080/v1"
    
    # Token de exemplo (será rejeitado, mas vamos ver a resposta)
    test_token = "mock-token-for-testing"
    
    headers = {
        "Authorization": f"Bearer {test_token}",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            # Testar endpoint de parceiros
            print("=== Testando Student Partners com token mock ===")
            partners_url = f"{base_url}/student/partners"
            partners_response = await client.get(partners_url, headers=headers)
            print(f"Partners Status: {partners_response.status_code}")
            print(f"Partners Response: {partners_response.text}")
            print()
            
        except Exception as e:
            print(f"Erro durante o teste: {e}")
            import traceback
            traceback.print_exc()


async def main():
    """Função principal de teste."""
    await test_token_verification()
    await test_student_partners_with_real_request()


if __name__ == "__main__":
    asyncio.run(main())