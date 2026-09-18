#!/usr/bin/env python3
"""
Debug direto do FirestoreClient para entender por que retorna 0 parceiros.
"""

import asyncio
import sys
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.auth import JWTPayload
from src.db import firestore_client


async def debug_firestore_client():
    """Debug direto do FirestoreClient."""
    print("🔍 DEBUG DIRETO DO FIRESTORE CLIENT")
    print("=" * 50)

    # Simular usuário admin
    user_payload = JWTPayload(
        sub="admin@knn.com.br",
        role="admin",
        tenant="knn-dev-tenant",
        exp=1758671888,
        iat=1758585488,
        iss="knn-portal-local",
        aud="knn-portal",
        name="Admin KNN",
    )

    print(f"👤 Usuário: {user_payload.sub}")
    print(f"🏢 Tenant: {user_payload.tenant}")
    print()

    try:
        # Teste 1: Consulta simples (sem filtros adicionais)
        print("1️⃣ Consulta simples (apenas tenant_id):")
        result1 = await firestore_client.query_documents(
            "partners",
            tenant_id=user_payload.tenant,
            filters=[],
            order_by=None,
            limit=50,
            offset=0,
        )
        print(f"   Resultado: {len(result1.get('items', []))} parceiros")
        print(f"   Estrutura: {list(result1.keys())}")

        # Teste 2: Consulta com filtro active
        print("\n2️⃣ Consulta com filtro active=True:")
        result2 = await firestore_client.query_documents(
            "partners",
            tenant_id=user_payload.tenant,
            filters=[("active", "==", True)],
            order_by=None,
            limit=50,
            offset=0,
        )
        print(f"   Resultado: {len(result2.get('items', []))} parceiros")

        # Teste 3: Consulta com ordenação (sem filtro active)
        print("\n3️⃣ Consulta com ordenação (sem filtro active):")
        result3 = await firestore_client.query_documents(
            "partners",
            tenant_id=user_payload.tenant,
            filters=[],
            order_by=[("trade_name", "ASCENDING")],
            limit=50,
            offset=0,
        )
        print(f"   Resultado: {len(result3.get('items', []))} parceiros")

        # Teste 4: Consulta completa (filtro + ordenação)
        print("\n4️⃣ Consulta completa (active=True + ordenação):")
        try:
            result4 = await firestore_client.query_documents(
                "partners",
                tenant_id=user_payload.tenant,
                filters=[("active", "==", True)],
                order_by=[("trade_name", "ASCENDING")],
                limit=50,
                offset=0,
            )
            print(f"   Resultado: {len(result4.get('items', []))} parceiros")

            # Mostrar alguns exemplos
            if result4.get("items"):
                print("   Primeiros parceiros:")
                for i, partner in enumerate(result4["items"][:3]):
                    print(
                        f"     {i+1}. {partner.get('trade_name', 'N/A')} (active: {partner.get('active', 'N/A')})"
                    )

        except Exception as e:
            print(f"   ❌ Erro: {e}")
            print(f"   Tipo: {type(e).__name__}")

        # Comparação dos resultados
        print("\n📊 RESUMO DOS RESULTADOS:")
        print(f"   • Consulta simples: {len(result1.get('items', []))} parceiros")
        print(f"   • Com filtro active: {len(result2.get('items', []))} parceiros")
        print(f"   • Com ordenação: {len(result3.get('items', []))} parceiros")

        # Verificar se há diferença nos dados retornados
        if result1.get("items") and result2.get("items"):
            print("\n🔍 ANÁLISE DOS DADOS:")
            print(
                f"   • Todos os parceiros têm active=True? {all(p.get('active') == True for p in result1['items'])}"
            )
            print(
                f"   • Parceiros com active=None: {sum(1 for p in result1['items'] if p.get('active') is None)}"
            )
            print(
                f"   • Parceiros com active=False: {sum(1 for p in result1['items'] if p.get('active') == False)}"
            )

    except Exception as e:
        print(f"❌ Erro geral: {e}")
        print(f"Tipo: {type(e).__name__}")


if __name__ == "__main__":
    asyncio.run(debug_firestore_client())
