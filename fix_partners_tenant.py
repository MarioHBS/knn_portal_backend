#!/usr/bin/env python3
"""
Script para corrigir o tenant_id dos parceiros no Firestore.
"""

import os

import firebase_admin
from firebase_admin import credentials, firestore


def initialize_firebase():
    """Inicializa o Firebase Admin SDK."""
    try:
        if not firebase_admin._apps:
            cred_path = "credentials/default-service-account-key.json"
            if os.path.exists(cred_path):
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
                print(f"✅ Firebase inicializado com credenciais: {cred_path}")
            else:
                print(f"❌ Arquivo de credenciais não encontrado: {cred_path}")
                return False
        return True
    except Exception as e:
        print(f"❌ Erro ao inicializar Firebase: {e}")
        return False

def fix_partners_tenant_id():
    """Corrige o tenant_id dos parceiros para 'knn-dev-tenant'."""
    try:
        if not initialize_firebase():
            return

        db = firestore.client()
        print("✅ Cliente Firestore inicializado")

        # Obter todos os parceiros
        partners_ref = db.collection('partners')
        partners = partners_ref.get()

        if not partners:
            print("⚠️ Nenhum parceiro encontrado")
            return

        print(f"🔧 Corrigindo tenant_id para {len(partners)} parceiros...")

        batch = db.batch()
        updated_count = 0

        for partner in partners:
            partner_data = partner.to_dict()
            current_tenant_id = partner_data.get('tenant_id')

            # Se tenant_id está vazio ou é None, atualizar para 'knn-dev-tenant'
            if not current_tenant_id or current_tenant_id == 'N/A':
                partner_ref = partners_ref.document(partner.id)
                batch.update(partner_ref, {'tenant_id': 'knn-dev-tenant'})
                updated_count += 1
                print(f"  ✓ Atualizando parceiro {partner.id}: {partner_data.get('trade_name', 'N/A')}")

        if updated_count > 0:
            # Executar as atualizações em batch
            batch.commit()
            print(f"✅ {updated_count} parceiros atualizados com sucesso!")
        else:
            print("ℹ️ Nenhum parceiro precisou ser atualizado")

        # Verificar os resultados
        print("\n🔍 Verificando resultados:")
        partners_updated = partners_ref.get()
        for partner in partners_updated:
            data = partner.to_dict()
            print(f"  - {partner.id}: tenant_id = {data.get('tenant_id', 'N/A')}")

    except Exception as e:
        print(f"❌ Erro ao corrigir tenant_id dos parceiros: {e}")

if __name__ == "__main__":
    print("🔧 Corrigindo tenant_id dos parceiros...")
    fix_partners_tenant_id()
