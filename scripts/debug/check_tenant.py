"""
Script para verificar o tenant_id do documento no Firestore.
"""

import sys
import os
import asyncio

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.db.firestore import get_database

async def main():
    """Verificar tenant_id do documento"""
    
    # Conectar ao Firestore
    db = get_database()
    
    # Buscar documento específico
    partner_id = "PTN_T4L5678_TEC"
    
    print(f"🔍 Buscando documento: {partner_id}")
    
    # Buscar documento diretamente
    doc_ref = db.collection("benefits").document(partner_id)
    doc = doc_ref.get()
    
    if doc.exists:
        data = doc.to_dict()
        print(f"✅ Documento encontrado!")
        
        # Verificar tenant_id em diferentes locais
        system_tenant = data.get("system", {}).get("tenant_id")
        direct_tenant = data.get("tenant_id")
        
        print(f"🏢 Tenant em system.tenant_id: {system_tenant}")
        print(f"🏢 Tenant direto: {direct_tenant}")
        
        # Verificar se algum benefício tem tenant_id
        for key, value in data.items():
            if key.startswith("BNF_") and isinstance(value, dict):
                benefit_system_tenant = value.get("system", {}).get("tenant_id")
                benefit_direct_tenant = value.get("tenant_id")
                print(f"🎁 Benefício {key}:")
                print(f"   - system.tenant_id: {benefit_system_tenant}")
                print(f"   - tenant_id direto: {benefit_direct_tenant}")
                break  # Só mostrar o primeiro benefício
        
        print(f"\n🔑 Token usa tenant: 'knn'")
        print(f"📋 Documento precisa ter tenant_id correspondente para acesso")
        
    else:
        print(f"❌ Documento não encontrado: {partner_id}")

if __name__ == "__main__":
    asyncio.run(main())