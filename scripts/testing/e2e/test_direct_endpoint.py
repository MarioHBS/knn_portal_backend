"""
Script para testar diretamente o endpoint get_benefit_details com IDs conhecidos.
"""

import requests


def test_direct_endpoint():
    """Testa diretamente o endpoint get_benefit_details."""
    try:
        # Carregar token
        with open("access_token.txt") as f:
            token = f.read().strip()

        print(f"✅ Token carregado: {token[:50]}...")

        # Configurar headers
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        # IDs conhecidos do debug anterior
        partner_id = "PTN_T4L5678_TEC"
        benefit_id = "BNF_FD7025_DC"

        # URL do endpoint
        url = f"http://localhost:8080/v1/admin/benefits/{partner_id}/{benefit_id}"

        print(f"🔍 Testando endpoint: {url}")
        print(f"🔍 Partner ID: {partner_id}")
        print(f"🔍 Benefit ID: {benefit_id}")

        # Fazer requisição
        response = requests.get(url, headers=headers)

        print(f"📊 Status Code: {response.status_code}")
        print(f"📊 Response Headers: {dict(response.headers)}")

        if response.status_code == 200:
            data = response.json()
            print("✅ Sucesso! Dados do benefício:")
            print("📋 Resposta completa:")
            import json

            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            print(f"❌ Erro: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Detalhes: {error_data}")
            except:
                print(f"   Resposta: {response.text}")

    except Exception as e:
        print(f"❌ Erro no teste: {e}")


if __name__ == "__main__":
    test_direct_endpoint()
