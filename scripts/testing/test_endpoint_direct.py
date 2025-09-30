#!/usr/bin/env python3
"""
Teste direto do endpoint get_benefit_details.

Este script testa diretamente o endpoint /admin/benefits/{partner_id}/{benefit_id}
para verificar se está funcionando corretamente.
"""

import json
from datetime import datetime

import requests

# Configurações
BACKEND_BASE_URL = "http://localhost:8080/v1"
PARTNER_ID = "PTN_T4L5678_TEC"
BENEFIT_ID = "BNF_4A9B21_DC"

# Token JWT válido (deve ser renovado se expirado)
JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbkBrbm4uY29tLmJyIiwicm9sZSI6ImFkbWluIiwidGVuYW50Ijoia25uLWRldi10ZW5hbnQiLCJleHAiOjE3NTkyODYyNjQsImlhdCI6MTc1OTE5OTg2NCwiaXNzIjoia25uLXBvcnRhbC1sb2NhbCIsImF1ZCI6Imtubi1wb3J0YWwiLCJuYW1lIjoiQWRtaW4gS05OIn0.5_IHaT3QZIvFUAbi4vc_aF7xH3jwbyecjqp5lFQRCTY"


def test_endpoint():
    """Testa o endpoint get_benefit_details."""
    url = f"{BACKEND_BASE_URL}/admin/benefits/{PARTNER_ID}/{BENEFIT_ID}"

    headers = {
        "Authorization": f"Bearer {JWT_TOKEN}",
        "Content-Type": "application/json"
    }

    print(f"🔍 Testando endpoint: {url}")
    print(f"📋 Partner ID: {PARTNER_ID}")
    print(f"🎁 Benefit ID: {BENEFIT_ID}")
    print(f"⏰ Timestamp: {datetime.now().isoformat()}")
    print("-" * 60)

    try:
        response = requests.get(url, headers=headers, timeout=10)

        print(f"📊 Status Code: {response.status_code}")
        print(f"📝 Response Headers: {dict(response.headers)}")
        print(f"📄 Response Content: {response.text}")

        if response.status_code == 200:
            print("✅ Sucesso! Endpoint funcionando corretamente.")
            try:
                data = response.json()
                print(f"📦 Dados retornados: {json.dumps(data, indent=2, ensure_ascii=False)}")
            except json.JSONDecodeError:
                print("⚠️ Resposta não é um JSON válido")
        elif response.status_code == 404:
            print("❌ Endpoint não encontrado (404)")
        elif response.status_code == 401:
            print("🔐 Token inválido ou expirado (401)")
        elif response.status_code == 403:
            print("🚫 Acesso negado (403)")
        else:
            print(f"⚠️ Status inesperado: {response.status_code}")

    except requests.exceptions.ConnectionError:
        print("❌ Erro de conexão - servidor não está rodando?")
    except requests.exceptions.Timeout:
        print("⏰ Timeout na requisição")
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")


def test_health():
    """Testa o endpoint de health para verificar se o servidor está rodando."""
    url = "http://localhost:8080/health"  # Sem o prefixo /v1

    print(f"🏥 Testando health check: {url}")

    try:
        response = requests.get(url, timeout=5)
        print(f"📊 Health Status: {response.status_code}")
        print(f"📄 Health Response: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Health check falhou: {e}")
        return False


if __name__ == "__main__":
    print("🚀 Iniciando teste direto do endpoint get_benefit_details")
    print("=" * 60)

    # Primeiro testa se o servidor está rodando
    if test_health():
        print("\n" + "=" * 60)
        test_endpoint()
    else:
        print("❌ Servidor não está acessível. Verifique se está rodando.")

    print("\n" + "=" * 60)
    print("🏁 Teste concluído")
