#!/usr/bin/env python3
"""
Script para testar o endpoint get_benefit_details com um benefício real
"""

import json
import os
import sys

import requests

# Adicionar o diretório raiz ao path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))


def load_token():
    """Carrega o token do cache"""
    cache_file = os.path.join(os.path.dirname(__file__), "token_cache.json")
    try:
        with open(cache_file) as f:
            cache = json.load(f)
            return cache.get("jwt_token")
    except FileNotFoundError:
        print("❌ Arquivo de cache do token não encontrado")
        return None


def test_with_real_benefit():
    """Testa o endpoint get_benefit_details com um benefício real"""

    # Carregar token
    token = load_token()
    if not token:
        print("❌ Token não encontrado")
        return

    print(f"✅ Token carregado: {token[:20]}...")

    # Configurar headers
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    base_url = "http://localhost:8080"

    # 1. Primeiro, listar benefícios para encontrar um real
    print("🔍 Listando benefícios para encontrar um real...")
    list_url = f"{base_url}/v1/admin/benefits"

    try:
        response = requests.get(list_url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            print(f"📋 Estrutura da resposta: {type(data)}")

            # A resposta tem a estrutura: {"msg": "...", "data": {"items": [...], "total": X, "limit": Y, "offset": Z}}
            if "data" in data and isinstance(data["data"], dict):
                benefits_data = data["data"].get("items", [])
            else:
                benefits_data = data.get("data", [])

            print(f"📋 Tipo de benefits_data: {type(benefits_data)}")
            print(
                f"📋 Quantidade de benefícios: {len(benefits_data) if isinstance(benefits_data, list) else 'N/A'}"
            )

            if isinstance(benefits_data, list) and benefits_data:
                # Pegar o primeiro benefício da lista
                first_benefit = benefits_data[0]
                partner_id = first_benefit.get("partner_id")
                benefit_id = first_benefit.get("benefit_id")

                print("✅ Benefício encontrado:")
                print(f"   Partner ID: {partner_id}")
                print(f"   Benefit ID: {benefit_id}")
                print(f"   Título: {first_benefit.get('title', 'N/A')}")

                # 2. Agora testar o endpoint get_benefit_details
                print("\n🔍 Testando endpoint get_benefit_details...")
                detail_url = f"{base_url}/v1/admin/benefits/{partner_id}/{benefit_id}"

                print(f"🔍 URL: {detail_url}")

                detail_response = requests.get(detail_url, headers=headers)

                print(f"📊 Status Code: {detail_response.status_code}")

                if detail_response.status_code == 200:
                    print("✅ Sucesso!")
                    try:
                        detail_data = detail_response.json()
                        print(
                            f"📄 Response Data: {json.dumps(detail_data, indent=2, ensure_ascii=False)}"
                        )
                    except json.JSONDecodeError:
                        print(f"📄 Response Text: {detail_response.text}")
                else:
                    print(f"❌ Erro {detail_response.status_code}")
                    try:
                        error_data = detail_response.json()
                        print(
                            f"📄 Error Data: {json.dumps(error_data, indent=2, ensure_ascii=False)}"
                        )
                    except json.JSONDecodeError:
                        print(f"📄 Error Text: {detail_response.text}")
            else:
                print("❌ Nenhum benefício encontrado na lista ou estrutura inesperada")
        else:
            print(f"❌ Erro ao listar benefícios: {response.status_code}")

    except requests.exceptions.RequestException as e:
        print(f"❌ Erro na requisição: {e}")


if __name__ == "__main__":
    test_with_real_benefit()
