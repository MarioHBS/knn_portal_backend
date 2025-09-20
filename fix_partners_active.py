#!/usr/bin/env python3
"""
Script para adicionar o campo 'active' aos parceiros no Firestore.
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

def fix_partners_active_field():
    """Adiciona o campo 'active' = True aos parceiros."""
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
        
        print(f"🔧 Adicionando campo 'active' para {len(partners)} parceiros...")
        
        batch = db.batch()
        updated_count = 0
        
        for partner in partners:
            partner_data = partner.to_dict()
            current_active = partner_data.get('active')
            
            # Se active não existe ou não é boolean, definir como True
            if current_active is None or not isinstance(current_active, bool):
                partner_ref = partners_ref.document(partner.id)
                batch.update(partner_ref, {'active': True})
                updated_count += 1
                print(f"  ✓ Atualizando parceiro {partner.id}: active = True")
        
        if updated_count > 0:
            # Executar as atualizações em batch
            batch.commit()
            print(f"✅ {updated_count} parceiros atualizados com sucesso!")
        else:
            print("ℹ️ Nenhum parceiro precisou ser atualizado")
            
        # Verificar os resultados
        print("\n🔍 Verificando resultados:")
        partners_updated = partners_ref.get()
        active_count = 0
        for partner in partners_updated:
            data = partner.to_dict()
            active_status = data.get('active', 'N/A')
            if active_status == True:
                active_count += 1
            print(f"  - {partner.id}: active = {active_status}")
            
        print(f"\n📊 Total de parceiros ativos: {active_count}")
            
    except Exception as e:
        print(f"❌ Erro ao corrigir campo active dos parceiros: {e}")

if __name__ == "__main__":
    print("🔧 Corrigindo campo 'active' dos parceiros...")
    fix_partners_active_field()