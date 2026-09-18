#!/usr/bin/env python3
"""
Script para depurar a estrutura real dos dados no Firestore
"""

import json
import os
import sys
import asyncio

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.db.firestore import get_database

async def main():
    """Verificar estrutura real dos dados no Firestore"""
    
    # Conectar ao Firestore
    db = get_database()
    
    # Buscar um documento específico
    partner_id = "PTN_T4L5678_TEC"
    
    print(f"🔍 Buscando documento: {partner_id}")
    
    # Buscar documento diretamente
    doc_ref = db.collection("benefits").document(partner_id)
    doc = doc_ref.get()
    
    if doc.exists:
        data = doc.to_dict()
        print(f"✅ Documento encontrado!")
        print(f"📋 Chaves do documento: {list(data.keys())}")
        
        # Imprimir estrutura completa
        print(f"\n📄 Estrutura completa:")
        print(json.dumps(data, indent=2, ensure_ascii=False, default=str))
        
        # Verificar se tem campo 'data'
        if 'data' in data:
            print(f"\n🔍 Campo 'data' encontrado!")
            data_content = data['data']
            print(f"📋 Tipo do campo 'data': {type(data_content)}")
            
            if isinstance(data_content, dict):
                print(f"📋 Chaves dentro de 'data': {list(data_content.keys())}")
                
                # Procurar por benefícios
                benefit_keys = [k for k in data_content.keys() if k.startswith('BNF_')]
                print(f"📋 Benefícios encontrados: {benefit_keys}")
        else:
            print(f"\n❌ Campo 'data' NÃO encontrado!")
            
            # Procurar benefícios diretamente no documento
            benefit_keys = [k for k in data.keys() if k.startswith('BNF_')]
            print(f"📋 Benefícios encontrados diretamente: {benefit_keys}")
            
    else:
        print(f"❌ Documento não encontrado!")
        
        # Listar todos os documentos da coleção
        print(f"\n🔍 Listando todos os documentos da coleção 'benefits':")
        collection_ref = db.collection("benefits")
        docs = collection_ref.stream()
        
        for doc in docs:
            print(f"  - {doc.id}")

if __name__ == "__main__":
    asyncio.run(main())