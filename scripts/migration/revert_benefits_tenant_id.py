#!/usr/bin/env python3
"""
Script para reverter as alterações do tenant_id duplicado nos benefícios.
Remove o campo tenant_id que foi adicionado incorretamente, mantendo apenas system.tenant_id.

Data: 2025-01-29
Autor: Sistema
"""

import os
import sys
from datetime import datetime

# Adicionar o diretório raiz ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.db.firestore import get_database
from google.cloud import firestore


def revert_benefits_tenant_id():
    """Remove o campo tenant_id duplicado dos documentos de benefícios."""
    
    print("🔄 Iniciando reversão do tenant_id duplicado nos benefícios...")
    print(f"⏰ Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Obter cliente Firestore
        db = get_database()
        if not db:
            raise Exception("Firestore não inicializado")
        
        # Obter todos os documentos da coleção benefits
        collection_ref = db.collection('benefits')
        docs = collection_ref.stream()
        
        updated_count = 0
        skipped_count = 0
        
        for doc in docs:
            doc_data = doc.to_dict()
            doc_id = doc.id
            
            # Verificar se o documento tem o campo tenant_id duplicado
            if 'tenant_id' in doc_data:
                print(f"📝 Removendo tenant_id duplicado do documento: {doc_id}")
                
                # Remover o campo tenant_id duplicado
                doc_ref = collection_ref.document(doc_id)
                doc_ref.update({
                    'tenant_id': firestore.DELETE_FIELD
                })
                
                updated_count += 1
                
                # Verificar se system.tenant_id existe
                system_data = doc_data.get('system', {})
                if 'tenant_id' in system_data:
                    print(f"✅ Mantido system.tenant_id: {system_data['tenant_id']}")
                else:
                    print(f"⚠️  ATENÇÃO: system.tenant_id não encontrado no documento {doc_id}")
            else:
                print(f"⏭️  Documento {doc_id} não possui tenant_id duplicado - ignorado")
                skipped_count += 1
        
        print(f"\n🎉 Reversão concluída!")
        print(f"📊 Documentos atualizados: {updated_count}")
        print(f"📊 Documentos ignorados: {skipped_count}")
        
    except Exception as e:
        print(f"❌ Erro durante a reversão: {str(e)}")
        raise


if __name__ == "__main__":
    revert_benefits_tenant_id()