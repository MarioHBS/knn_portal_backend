#!/usr/bin/env python3
"""
Teste do endpoint partner_details para estudantes.

Este script testa o endpoint /student/partner/{partner_id}
para verificar se o erro ValidationInfo foi corrigido.
"""

import json
from datetime import datetime

import requests

# Configurações
BACKEND_BASE_URL = "http://localhost:8080/v1"
PARTNER_ID = "PTN_T4L5678_TEC"

# Token JWT válido para estudante
JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJzdHVkZW50QGtubi5jb20uYnIiLCJyb2xlIjoic3R1ZGVudCIsInRlbmFudCI6Imtubi1kZXYtdGVuYW50IiwiZXhwIjoxNzU5Mjg2NDE3LCJpYXQiOjE3NTkyMDAwMTcsImlzcyI6Imtubi1wb3J0YWwtbG9jYWwiLCJhdWQiOiJrbm4tcG9ydGFsIiwibmFtZSI6IlN0dWRlbnQgS05OIn0.9gqhKCgO3Vo5V3FyzNOTeuRgLhOoUOuh10TNGJYtHdA"


def test_partner_details():
    """Testa o endpoint partner_details para estudantes."""
    url = f"{BACKEND_BASE_URL}/student/partners/{PARTNER_ID}"  # Corrigido: /partners/ em vez de /partner/

    headers = {
        "Authorization": f"Bearer {JWT_TOKEN}",
        "Content-Type": "application/json",
    }

    print(f"🔍 Testando endpoint: {url}")
    print(f"📋 Partner ID: {PARTNER_ID}")
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
                print(
                    f"📦 Dados retornados: {json.dumps(data, indent=2, ensure_ascii=False)}"
                )

                # Verificar se há benefícios retornados
                if "data" in data and "benefits" in data["data"]:
                    benefits_count = len(data["data"]["benefits"])
                    print(f"🎁 Total de benefícios encontrados: {benefits_count}")

                    for i, benefit in enumerate(data["data"]["benefits"], 1):
                        print(
                            f"   {i}. {benefit.get('title', 'Sem título')} - {benefit.get('benefit_id', 'Sem ID')}"
                        )
                else:
                    print("⚠️ Nenhum benefício encontrado na resposta")

            except json.JSONDecodeError:
                print("⚠️ Resposta não é um JSON válido")
        elif response.status_code == 404:
            print("❌ Endpoint não encontrado (404)")
        elif response.status_code == 401:
            print("🔐 Token inválido ou expirado (401)")
        elif response.status_code == 403:
            print("🚫 Acesso negado (403)")
        elif response.status_code == 500:
            print("💥 Erro interno do servidor (500)")
            print("🔍 Verificar logs do servidor para mais detalhes")
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
    url = "http://localhost:8080/health"

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
    print("🚀 Iniciando teste do endpoint partner_details para estudantes")
    print("=" * 60)

    # Primeiro testa se o servidor está rodando
    if test_health():
        print("\n" + "=" * 60)
        test_partner_details()
    else:
        print("❌ Servidor não está acessível. Verifique se está rodando.")

    print("\n" + "=" * 60)
    print("🏁 Teste concluído")
