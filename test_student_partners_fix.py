#!/usr/bin/env python3
"""
Script para testar a correção do endpoint /student/partners

Este script testa se o endpoint agora retorna parceiros corretamente
após a correção da ordem dos parâmetros na função query_documents.
"""

import asyncio

import httpx

# Configurações
BASE_URL = "http://localhost:8000"

# Token de teste para estudante (você precisa usar um token válido)
# Este é um exemplo - substitua por um token real do seu ambiente de desenvolvimento
STUDENT_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6IjEyMzQ1Njc4OTAiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL3NlY3VyZXRva2VuLmdvb2dsZS5jb20va25uLWJlbmVmaXRzIiwiYXVkIjoia25uLWJlbmVmaXRzIiwiYXV0aF90aW1lIjoxNjk0NzA4NDAwLCJ1c2VyX2lkIjoiU1REXzEyMzQ1NiIsInN1YiI6IlNURF8xMjM0NTYiLCJpYXQiOjE2OTQ3MDg0MDAsImV4cCI6MTY5NDcxMjAwMCwiZW1haWwiOiJzdHVkZW50ZUBleGFtcGxlLmNvbSIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJmaXJlYmFzZSI6eyJpZGVudGl0aWVzIjp7ImVtYWlsIjpbInN0dWRlbnRlQGV4YW1wbGUuY29tIl19LCJzaWduX2luX3Byb3ZpZGVyIjoiY3VzdG9tIn0sInJvbGUiOiJzdHVkZW50IiwidGVuYW50Ijoia25uLWRldi10ZW5hbnQifQ.example_signature"


async def test_student_partners_endpoint():
    """
    Testa o endpoint /student/partners para verificar se a correção funcionou.
    """
    print("🧪 Testando endpoint /student/partners após correção...\n")

    headers = {
        "Authorization": f"Bearer {STUDENT_TOKEN}",
        "Content-Type": "application/json",
    }

    # Parâmetros de teste
    params = {
        "limit": 10,
        "offset": 0,
        "cat": "tecnologia",  # Categoria opcional
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            print(f"📡 Fazendo requisição para: {BASE_URL}/student/partners")
            print(f"📋 Parâmetros: {params}")
            print("🔑 Usando token de estudante\n")

            response = await client.get(
                f"{BASE_URL}/student/partners", headers=headers, params=params
            )

            print(f"📊 Status Code: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                partners = data.get("partners", [])
                total = data.get("total", 0)

                print("✅ Sucesso! Endpoint funcionando corretamente")
                print(f"📈 Total de parceiros encontrados: {total}")
                print(f"📋 Parceiros retornados nesta página: {len(partners)}")

                if partners:
                    print("\n🏢 Primeiros parceiros encontrados:")
                    for i, partner in enumerate(partners[:3], 1):
                        name = partner.get("name", "Nome não disponível")
                        category = partner.get("category", "Categoria não disponível")
                        active = partner.get("active", False)
                        print(f"  {i}. {name} - {category} (Ativo: {active})")
                else:
                    print(
                        "⚠️  Nenhum parceiro retornado (pode ser normal se não houver parceiros ativos)"
                    )

                return True

            elif response.status_code == 401:
                print("🔒 Erro 401: Token inválido ou expirado")
                print("💡 Dica: Você precisa usar um token JWT válido de estudante")
                return False

            elif response.status_code == 403:
                print("🚫 Erro 403: Acesso negado")
                print("💡 Dica: Verifique se o token tem role 'student'")
                return False

            else:
                print(f"❌ Erro {response.status_code}: {response.text}")
                return False

    except httpx.ConnectError:
        print("🔌 Erro de conexão: Servidor não está rodando")
        print("💡 Dica: Execute 'python -m uvicorn src.main:app --reload' primeiro")
        return False

    except Exception as e:
        print(f"💥 Erro inesperado: {str(e)}")
        return False


async def test_without_auth():
    """
    Testa o endpoint sem autenticação para verificar se a segurança está funcionando.
    """
    print("\n🔒 Testando endpoint sem autenticação...")

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{BASE_URL}/student/partners")

            if response.status_code == 401:
                print(
                    "✅ Segurança OK: Endpoint corretamente rejeitou requisição sem token"
                )
                return True
            else:
                print(f"⚠️  Inesperado: Status {response.status_code} (esperado 401)")
                return False

    except Exception as e:
        print(f"💥 Erro: {str(e)}")
        return False


async def main():
    """
    Função principal que executa todos os testes.
    """
    print("🚀 Iniciando testes do endpoint /student/partners\n")
    print("=" * 60)

    # Teste 1: Sem autenticação
    auth_test = await test_without_auth()

    print("\n" + "=" * 60)

    # Teste 2: Com autenticação
    endpoint_test = await test_student_partners_endpoint()

    print("\n" + "=" * 60)
    print("📋 RESUMO DOS TESTES:")
    print(f"🔒 Teste de segurança: {'✅ PASSOU' if auth_test else '❌ FALHOU'}")
    print(f"🎯 Teste do endpoint: {'✅ PASSOU' if endpoint_test else '❌ FALHOU'}")

    if auth_test and endpoint_test:
        print("\n🎉 Todos os testes passaram! A correção foi bem-sucedida.")
    elif not endpoint_test:
        print("\n⚠️  O endpoint ainda não está funcionando corretamente.")
        print("💡 Verifique se você está usando um token JWT válido.")

    print("\n📝 NOTA: Para testar completamente, você precisa:")
    print("   1. Um token JWT válido de estudante")
    print("   2. Dados de parceiros no Firestore")
    print("   3. Servidor rodando em http://localhost:8000")


if __name__ == "__main__":
    asyncio.run(main())
