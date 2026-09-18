#!/usr/bin/env python3
"""
Script para debugar a consulta do firestore_client.query_documents.
"""

import os
import sys
from pathlib import Path

# Adicionar o diretório src ao path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from firebase_admin import firestore
import firebase_admin
from firebase_admin import credentials

# Importar diretamente as funções necessárias
import os
os.environ.setdefault('CIRCUIT_BREAKER_THRESHOLD', '5')
os.environ.setdefault('CIRCUIT_BREAKER_TIMEOUT', '60')

from db.firestore import FirestoreClient


def initialize_firebase():
    """Inicializa o Firebase."""
    try:
        # Verificar se já foi inicializado
        firebase_admin.get_app()
        print("✅ Firebase já inicializado")
        return True
    except ValueError:
        # Não foi inicializado ainda
        pass

    # Tentar inicializar
    try:
        # Usar credenciais padrão do ambiente
        cred = credentials.ApplicationDefault()
        firebase_admin.initialize_app(cred)
        print("✅ Firebase inicializado com credenciais padrão")
        return True
    except Exception as e:
        print(f"❌ Erro ao inicializar Firebase: {e}")
        return False


async def debug_firestore_query():
    """Debuga a consulta do firestore_client.query_documents."""
    if not initialize_firebase():
        return False

    try:
        print("\n🔍 Debugando consulta do FirestoreClient...")

        # Teste 1: Consulta sem filtros adicionais
        print("\n1️⃣ Teste: Consulta apenas com tenant_id")
        result = await FirestoreClient.query_documents(
            collection="partners",
            tenant_id="knn-dev-tenant",
            filters=None,
            order_by=None,
            limit=20,
            offset=0
        )

        print(f"   📊 Resultado: {len(result.get('items', []))} parceiros")
        print(f"   📊 Total: {result.get('total', 0)}")

        if result.get('items'):
            print("   ✅ Primeiros 3 parceiros:")
            for i, partner in enumerate(result['items'][:3]):
                print(f"     {i+1}. {partner.get('trade_name', 'N/A')} (active: {partner.get('active', 'N/A')})")

        # Teste 2: Consulta com filtro active=True
        print("\n2️⃣ Teste: Consulta com tenant_id + active=True")
        result = await FirestoreClient.query_documents(
            collection="partners",
            tenant_id="knn-dev-tenant",
            filters=[("active", "==", True)],
            order_by=None,
            limit=20,
            offset=0
        )

        print(f"   📊 Resultado: {len(result.get('items', []))} parceiros")
        print(f"   📊 Total: {result.get('total', 0)}")

        if result.get('items'):
            print("   ✅ Primeiros 3 parceiros:")
            for i, partner in enumerate(result['items'][:3]):
                print(f"     {i+1}. {partner.get('trade_name', 'N/A')} (active: {partner.get('active', 'N/A')})")

        # Teste 3: Consulta com ordenação (simulando o endpoint)
        print("\n3️⃣ Teste: Consulta com tenant_id + active=True + ordenação")
        result = await FirestoreClient.query_documents(
            collection="partners",
            tenant_id="knn-dev-tenant",
            filters=[("active", "==", True)],
            order_by=[("trade_name", "ASCENDING")],
            limit=20,
            offset=0
        )

        print(f"   📊 Resultado: {len(result.get('items', []))} parceiros")
        print(f"   📊 Total: {result.get('total', 0)}")

        if result.get('items'):
            print("   ✅ Primeiros 3 parceiros:")
            for i, partner in enumerate(result['items'][:3]):
                print(f"     {i+1}. {partner.get('trade_name', 'N/A')} (active: {partner.get('active', 'N/A')})")

        # Teste 4: Verificar se há erro na consulta direta
        print("\n4️⃣ Teste: Consulta direta no Firestore (sem FirestoreClient)")
        db = firestore.client()
        query = db.collection('partners').where('tenant_id', '==', 'knn-dev-tenant').where('active', '==', True)
        docs = list(query.stream())

        print(f"   📊 Resultado direto: {len(docs)} parceiros")

        if docs:
            print("   ✅ Primeiros 3 parceiros:")
            for i, doc in enumerate(docs[:3]):
                data = doc.to_dict()
                print(f"     {i+1}. {data.get('trade_name', 'N/A')} (active: {data.get('active', 'N/A')})")

        return True

    except Exception as e:
        print(f"❌ Erro no debug: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import asyncio
    success = asyncio.run(debug_firestore_query())
    sys.exit(0 if success else 1)
