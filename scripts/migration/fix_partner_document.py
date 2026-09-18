"""
Script para corrigir o documento do parceiro PTN_T4L5678_TEC
- Remove o documento com ID incorreto (knn-dev-tenant_PTN_T4L5678_TEC)
- Cria o documento correto com ID PTN_T4L5678_TEC e campo tenant_id
"""

import asyncio
import sys
import os
from datetime import datetime

# Adicionar o diretório raiz ao path
project_root = os.path.join(os.path.dirname(__file__), '..', '..')
sys.path.insert(0, project_root)

from src.db.firestore import db


async def fix_partner_document():
    """Corrige o documento do parceiro PTN_T4L5678_TEC"""
    
    # Verificar se o Firestore foi inicializado
    if not db:
        print("❌ Erro: Firestore não foi inicializado")
        return
    
    # Simular usuário admin
    user_payload = {
        "user_id": "admin_user",
        "tenant": "knn-dev-tenant",
        "role": "admin"
    }
    
    print("=== Verificando estrutura de documentos existentes ===")
    
    # Verificar alguns documentos existentes para entender a estrutura
    partners_ref = db.collection("partners")
    docs = partners_ref.limit(3).stream()
    
    print("Estrutura de documentos existentes:")
    for doc in docs:
        data = doc.to_dict()
        print(f"ID: {doc.id}")
        print(f"Tem tenant_id: {'tenant_id' in data}")
        if 'tenant_id' in data:
            print(f"tenant_id: {data['tenant_id']}")
        print(f"Nome: {data.get('trade_name', 'N/A')}")
        print("---")
    
    print("\n=== Verificando documento incorreto ===")
    
    # Verificar se o documento incorreto existe
    wrong_doc_id = "knn-dev-tenant_PTN_T4L5678_TEC"
    wrong_doc_ref = db.collection("partners").document(wrong_doc_id)
    wrong_doc = wrong_doc_ref.get()
    
    if wrong_doc.exists:
        print(f"✓ Documento incorreto encontrado: {wrong_doc_id}")
        wrong_data = wrong_doc.to_dict()
        print(f"Dados: {wrong_data}")
        
        # Deletar documento incorreto
        print(f"Deletando documento incorreto...")
        wrong_doc_ref.delete()
        print(f"✓ Documento {wrong_doc_id} deletado")
        
        print("\n=== Criando documento correto ===")
        
        # Criar documento correto
        correct_doc_id = "PTN_T4L5678_TEC"
        correct_doc_ref = db.collection("partners").document(correct_doc_id)
        
        # Preparar dados corretos (adicionar tenant_id)
        correct_data = wrong_data.copy()
        correct_data['tenant_id'] = user_payload['tenant']
        correct_data['updated_at'] = datetime.utcnow()
        
        # Salvar documento correto
        correct_doc_ref.set(correct_data)
        print(f"✓ Documento correto criado: {correct_doc_id}")
        print(f"✓ tenant_id adicionado: {correct_data['tenant_id']}")
        
        # Verificar se foi criado corretamente
        verification_doc = correct_doc_ref.get()
        if verification_doc.exists:
            verification_data = verification_doc.to_dict()
            print(f"\n=== Verificação final ===")
            print(f"ID do documento: {verification_doc.id}")
            print(f"tenant_id: {verification_data.get('tenant_id')}")
            print(f"Nome: {verification_data.get('trade_name')}")
            print(f"Categoria: {verification_data.get('category')}")
            print(f"Cidade: {verification_data.get('address', {}).get('city')}")
            print(f"✓ Correção realizada com sucesso!")
        else:
            print("❌ Erro: Documento correto não foi encontrado após criação")
            
    else:
        print(f"❌ Documento incorreto não encontrado: {wrong_doc_id}")
        
        # Verificar se o documento correto já existe
        correct_doc_id = "PTN_T4L5678_TEC"
        correct_doc_ref = db.collection("partners").document(correct_doc_id)
        correct_doc = correct_doc_ref.get()
        
        if correct_doc.exists:
            print(f"✓ Documento correto já existe: {correct_doc_id}")
            correct_data = correct_doc.to_dict()
            print(f"tenant_id: {correct_data.get('tenant_id')}")
            print(f"Nome: {correct_data.get('trade_name')}")
        else:
            print(f"❌ Documento correto também não existe: {correct_doc_id}")


if __name__ == "__main__":
    asyncio.run(fix_partner_document())