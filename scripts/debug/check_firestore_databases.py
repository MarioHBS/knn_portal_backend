#!/usr/bin/env python3
"""
Script para verificar em qual banco Firestore estão os dados do parceiro PTN_T4L5678_TEC.
"""

import os
import sys

# Adicionar o diretório raiz do projeto ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Importar cliente Firestore do projeto
from src.db.firestore import get_database
from src.config import FIRESTORE_DATABASES_LIST


def check_firestore_databases():
    """Verifica em qual banco Firestore estão os dados do parceiro."""
    
    partner_id = "PTN_T4L5678_TEC"
    
    print(f"🔍 Procurando parceiro {partner_id} nos bancos Firestore disponíveis:")
    print(f"📋 Bancos configurados: {FIRESTORE_DATABASES_LIST}")
    print("-" * 60)
    
    for database_name in FIRESTORE_DATABASES_LIST:
        try:
            print(f"\n🗄️  Verificando banco: {database_name}")
            
            # Conectar ao banco específico
            db = get_database(database_name)
            
            # Buscar documento do parceiro
            partner_ref = db.collection('partners').document(partner_id)
            partner_doc = partner_ref.get()
            
            if partner_doc.exists:
                partner_data = partner_doc.to_dict()
                benefits = partner_data.get('benefits', {})
                
                print(f"   ✅ ENCONTRADO no banco {database_name}!")
                print(f"   📊 Total de benefícios: {len(benefits)}")
                
                if benefits:
                    print(f"   🎫 Benefícios encontrados:")
                    for benefit_id, benefit_data in list(benefits.items())[:3]:  # Mostrar apenas os 3 primeiros
                        title = benefit_data.get('title', 'Sem título')
                        status = benefit_data.get('status', 'N/A')
                        system_data = benefit_data.get('system', {})
                        tenant_id = system_data.get('tenant_id')
                        print(f"      - {benefit_id}: {title} (Status: {status}, Tenant: {tenant_id})")
                    
                    if len(benefits) > 3:
                        print(f"      ... e mais {len(benefits) - 3} benefícios")
                
                return database_name
            else:
                print(f"   ❌ Não encontrado no banco {database_name}")
                
        except Exception as e:
            print(f"   ⚠️  Erro ao verificar banco {database_name}: {e}")
    
    print(f"\n❌ Parceiro {partner_id} não foi encontrado em nenhum banco!")
    return None


if __name__ == "__main__":
    found_database = check_firestore_databases()
    
    if found_database:
        print(f"\n💡 Use o banco '{found_database}' para acessar os dados do parceiro.")
    else:
        print(f"\n💡 Verifique se o parceiro existe ou se há outros bancos configurados.")