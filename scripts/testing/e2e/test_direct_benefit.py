#!/usr/bin/env python3
"""
Script para testar diretamente o endpoint get_benefit_details
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


def test_benefit_endpoint():
    """Testa o endpoint get_benefit_details diretamente"""

    # Carregar token
    token = load_token()
    if not token:
        print("❌ Token não encontrado")
        return

    print(f"✅ Token carregado: {token[:20]}...")

    # Configurar a requisição
    base_url = "http://localhost:8080"
    partner_id = "PTN_T4L5678_TEC"
    benefit_id = "BNF_4A9B21_DC"

    url = f"{base_url}/v1/admin/benefits/{partner_id}/{benefit_id}"

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    print(f"🔍 Testando URL: {url}")
    print(f"📋 Headers: {headers}")

    try:
        # Fazer a requisição
        response = requests.get(url, headers=headers)

        print(f"📊 Status Code: {response.status_code}")
        print(f"📋 Response Headers: {dict(response.headers)}")

        if response.status_code == 200:
            print("✅ Sucesso!")
            try:
                data = response.json()
                print(
                    f"📄 Response Data: {json.dumps(data, indent=2, ensure_ascii=False)}"
                )
            except json.JSONDecodeError:
                print(f"📄 Response Text: {response.text}")
        else:
            print(f"❌ Erro {response.status_code}")
            try:
                error_data = response.json()
                print(
                    f"📄 Error Data: {json.dumps(error_data, indent=2, ensure_ascii=False)}"
                )
            except json.JSONDecodeError:
                print(f"📄 Error Text: {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"❌ Erro na requisição: {e}")


if __name__ == "__main__":
    test_benefit_endpoint()
