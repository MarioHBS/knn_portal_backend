"""
Script para corrigir o tenant_id do documento no Firestore.
O documento precisa ter tenant_id = 'knn-dev-tenant' para ser acessível.
"""

import asyncio
import os
import sys

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from src.db.firestore import get_database


async def main():
    """Corrigir tenant_id do documento"""

    # Conectar ao Firestore
    db = get_database()

    # Buscar documento específico
    partner_id = "PTN_T4L5678_TEC"

    print(f"🔧 Corrigindo tenant_id do documento: {partner_id}")

    # Buscar documento diretamente
    doc_ref = db.collection("benefits").document(partner_id)
    doc = doc_ref.get()

    if doc.exists:
        data = doc.to_dict()
        print("✅ Documento encontrado!")

        # Verificar tenant_id atual
        current_tenant = data.get("tenant_id")
        system_tenant = data.get("system", {}).get("tenant_id")

        print(f"🏢 Tenant atual direto: {current_tenant}")
        print(f"🏢 Tenant atual em system: {system_tenant}")

        # Adicionar tenant_id no nível raiz do documento
        data["tenant_id"] = "knn-dev-tenant"

        # Também adicionar em system se não existir
        if "system" not in data:
            data["system"] = {}
        data["system"]["tenant_id"] = "knn-dev-tenant"

        # Atualizar documento
        doc_ref.set(data)

        print("✅ Documento atualizado com tenant_id: knn-dev-tenant")
        print("📋 Tenant adicionado no nível raiz e em system.tenant_id")

    else:
        print(f"❌ Documento não encontrado: {partner_id}")


if __name__ == "__main__":
    asyncio.run(main())
