#!/usr/bin/env python3
"""
Script para debugar incompatibilidade de tenant_id entre JWT e Firestore.

Este script vai:
1. Fazer login real e capturar o JWT
2. Decodificar o JWT para extrair o tenant_id
3. Consultar parceiros no Firestore e verificar seus tenant_ids
4. Comparar e identificar a incompatibilidade
"""

import asyncio
import os
import sys
from datetime import datetime

import jwt
import requests

# Adicionar o diretório src ao path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from src.db.firestore import FirestoreClient


async def debug_tenant_mismatch():
    """Debug da incompatibilidade de tenant_id."""
    print("=== DEBUG TENANT MISMATCH ===")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()

    # 1. Fazer login real
    print("1. Fazendo login real...")
    login_url = "http://localhost:8080/v1/users/login"
    login_data = {"username": "aluno.teste@journeyclub.com.br", "password": "Tp654321"}

    try:
        response = requests.post(login_url, json=login_data, timeout=10)
        print(f"Status do login: {response.status_code}")

        if response.status_code != 200:
            print(f"Erro no login: {response.text}")
            return

        login_result = response.json()
        token = login_result.get("access_token")

        if not token:
            print("Token não encontrado na resposta do login")
            return

        print("✅ Login realizado com sucesso")
        print()

    except Exception as e:
        print(f"❌ Erro no login: {e}")
        return

    # 2. Decodificar JWT (sem verificar assinatura para debug)
    print("2. Decodificando JWT...")
    try:
        # Decodificar sem verificar assinatura para debug
        decoded_token = jwt.decode(token, options={"verify_signature": False})
        jwt_tenant = decoded_token.get("tenant", "N/A")
        jwt_role = decoded_token.get("role", "N/A")
        jwt_sub = decoded_token.get("sub", "N/A")

        print(f"JWT tenant_id: '{jwt_tenant}'")
        print(f"JWT role: '{jwt_role}'")
        print(f"JWT sub: '{jwt_sub}'")
        print()

    except Exception as e:
        print(f"❌ Erro ao decodificar JWT: {e}")
        return

    # 3. Consultar parceiros no Firestore
    print("3. Consultando parceiros no Firestore...")
    try:
        # Inicializar cliente Firestore
        firestore_client = FirestoreClient()

        # Buscar todos os parceiros (sem filtro de tenant)
        result = await firestore_client.query_documents(
            "partners",
            tenant_id=None,  # Sem filtro de tenant para ver todos
            filters=None,
            limit=50,
        )

        partners = result.get("items", [])
        print(f"Total de parceiros encontrados: {len(partners)}")

        # Analisar tenant_ids dos parceiros
        tenant_counts = {}
        for partner in partners:
            partner_tenant = partner.get("tenant_id", "N/A")
            tenant_counts[partner_tenant] = tenant_counts.get(partner_tenant, 0) + 1

        print("\nDistribuição de tenant_ids nos parceiros:")
        for tenant_id, count in tenant_counts.items():
            print(f"  '{tenant_id}': {count} parceiros")
        print()

    except Exception as e:
        print(f"❌ Erro ao consultar Firestore: {e}")
        return

    # 4. Testar endpoint com JWT real
    print("4. Testando endpoint student/partners com JWT real...")
    try:
        partners_url = "http://localhost:8080/v1/student/partners"
        headers = {"Authorization": f"Bearer {token}"}

        response = requests.get(partners_url, headers=headers, timeout=10)
        print(f"Status do endpoint: {response.status_code}")

        if response.status_code == 200:
            endpoint_result = response.json()
            partners_count = len(endpoint_result.get("data", []))
            print(f"Parceiros retornados pelo endpoint: {partners_count}")
        else:
            print(f"Erro no endpoint: {response.text}")
        print()

    except Exception as e:
        print(f"❌ Erro ao testar endpoint: {e}")
        return

    # 5. Análise e recomendações
    print("5. Análise e Recomendações:")
    print("=" * 50)

    if jwt_tenant in tenant_counts:
        matching_partners = tenant_counts[jwt_tenant]
        print(f"✅ JWT tenant '{jwt_tenant}' encontrado no Firestore")
        print(f"   Parceiros com este tenant: {matching_partners}")
    else:
        print(f"❌ JWT tenant '{jwt_tenant}' NÃO encontrado no Firestore")
        print("   Possíveis soluções:")
        print("   1. Corrigir tenant_id dos parceiros no Firestore")
        print("   2. Verificar configuração do JWT no backend")
        print("   3. Atualizar dados do usuário no Firebase Auth")

    print()
    print("Tenant_ids disponíveis no Firestore:")
    for tenant_id in tenant_counts:
        print(f"  - '{tenant_id}'")


if __name__ == "__main__":
    asyncio.run(debug_tenant_mismatch())
