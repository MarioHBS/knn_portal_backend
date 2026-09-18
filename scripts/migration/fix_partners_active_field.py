#!/usr/bin/env python3
"""
Script para corrigir o campo 'active' dos parceiros no Firestore.
"""

import os
import sys
from pathlib import Path

# Adicionar o diretório src ao path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from firebase_admin import firestore
import firebase_admin
from firebase_admin import credentials


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


def fix_partners_active_field():
    """Corrige o campo 'active' dos parceiros no Firestore."""
    if not initialize_firebase():
        return False
    
    try:
        db = firestore.client()
        print("✅ Cliente Firestore inicializado")
        
        # Obter todos os parceiros
        print("\n🔍 Verificando parceiros...")
        partners_ref = db.collection('partners')
        all_partners = list(partners_ref.stream())
        
        print(f"📊 Total de parceiros encontrados: {len(all_partners)}")
        
        if len(all_partners) == 0:
            print("⚠️ Nenhum parceiro encontrado")
            return True
        
        # Verificar quais precisam de correção
        partners_to_fix = []
        for partner in all_partners:
            data = partner.to_dict()
            active_field = data.get('active')
            
            # Se o campo 'active' não existe ou é None, precisa ser corrigido
            if active_field is None:
                partners_to_fix.append({
                    'id': partner.id,
                    'trade_name': data.get('trade_name', 'N/A'),
                    'current_active': active_field
                })
        
        print(f"\n🔧 Parceiros que precisam de correção: {len(partners_to_fix)}")
        
        if len(partners_to_fix) == 0:
            print("✅ Todos os parceiros já têm o campo 'active' definido")
            return True
        
        # Mostrar parceiros que serão corrigidos
        print("\n📋 Parceiros que serão corrigidos:")
        for partner in partners_to_fix:
            print(f"  - {partner['trade_name']} (active: {partner['current_active']} → True)")
        
        # Confirmar antes de fazer as alterações
        print(f"\n⚠️  Isso irá definir o campo 'active' como True para {len(partners_to_fix)} parceiros.")
        response = input("Deseja continuar? (s/N): ").strip().lower()
        
        if response not in ['s', 'sim', 'y', 'yes']:
            print("❌ Operação cancelada pelo usuário")
            return False
        
        # Fazer as correções em batch
        print("\n🔧 Aplicando correções...")
        batch = db.batch()
        
        for partner in partners_to_fix:
            partner_ref = partners_ref.document(partner['id'])
            batch.update(partner_ref, {'active': True})
        
        # Executar o batch
        batch.commit()
        print(f"✅ {len(partners_to_fix)} parceiros atualizados com sucesso!")
        
        # Verificar os resultados
        print("\n🔍 Verificando resultados...")
        updated_partners = list(partners_ref.stream())
        
        active_count = 0
        for partner in updated_partners:
            data = partner.to_dict()
            if data.get('active') is True:
                active_count += 1
        
        print(f"📊 Parceiros com active=True: {active_count}/{len(updated_partners)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao corrigir dados: {e}")
        return False


if __name__ == "__main__":
    success = fix_partners_active_field()
    sys.exit(0 if success else 1)