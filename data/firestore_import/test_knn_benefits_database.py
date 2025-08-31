#!/usr/bin/env python3
"""
Script para testar acesso específico ao banco 'knn-benefits' do projeto KNNBenefits.
"""

import json
import os
from pathlib import Path

import firebase_admin
from firebase_admin import credentials
from google.cloud import firestore


def test_knn_benefits_database():
    """Testa acesso ao banco 'knn-benefits' especificamente."""
    
    # Limpar variáveis de ambiente do emulador
    if "FIRESTORE_EMULATOR_HOST" in os.environ:
        del os.environ["FIRESTORE_EMULATOR_HOST"]
    if "GCLOUD_PROJECT" in os.environ:
        del os.environ["GCLOUD_PROJECT"]

    # Limpar apps existentes para evitar conflitos
    apps_to_delete = list(firebase_admin._apps.values())
    for app in apps_to_delete:
        firebase_admin.delete_app(app)

    current_dir = Path(__file__).parent
    project_id = "knn-benefits"
    database_id = "knn-benefits"  # Banco específico, não o (default)
    
    # Procurar chave de conta de serviço
    service_account_files = [
        current_dir / "knn-benefits-service-account-key.json",
        current_dir / "service-account-key.json"
    ]
    
    service_account_path = None
    for file_path in service_account_files:
        if file_path.exists():
            service_account_path = str(file_path)
            break
    
    if not service_account_path:
        print(f"❌ Nenhuma chave de conta de serviço encontrada")
        print(f"   Arquivos procurados: {[str(f) for f in service_account_files]}")
        return False

    try:
        print(f"🔑 Usando chave: {service_account_path}")
        print(f"🎯 Projeto: {project_id}")
        print(f"🗄️  Banco: {database_id}")
        print("\n" + "="*50)
        
        # Inicializar Firebase Admin (para autenticação)
        cred = credentials.Certificate(service_account_path)
        app = firebase_admin.initialize_app(cred, {"projectId": project_id})
        
        # Conectar ao banco específico 'knn-benefits' usando google-cloud-firestore
        db = firestore.Client(project=project_id, database=database_id, credentials=cred.get_credential())
        
        print(f"✅ Conectado ao banco '{database_id}' do projeto '{project_id}'")
        
        # Listar coleções
        print("\n📚 Listando coleções...")
        collections = db.collections()
        collection_names = []
        
        for collection in collections:
            collection_names.append(collection.id)
            print(f"   📁 {collection.id}")
            
            # Contar documentos na coleção (limitado a 5 para teste)
            docs = collection.limit(5).stream()
            doc_count = 0
            for doc in docs:
                doc_count += 1
            
            if doc_count > 0:
                print(f"      📄 Documentos encontrados: {doc_count}+ (amostra)")
            else:
                print(f"      📄 Nenhum documento encontrado")
        
        if not collection_names:
            print("   ⚠️  Nenhuma coleção encontrada no banco 'knn-benefits'")
            print("   💡 Isso pode ser normal se o banco ainda não foi populado")
        
        print(f"\n✅ Teste concluído com sucesso!")
        print(f"   🎯 Banco: {database_id}")
        print(f"   📊 Coleções: {len(collection_names)}")
        if collection_names:
            print(f"   📁 Lista: {', '.join(collection_names)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao acessar banco '{database_id}': {e}")
        print("\n💡 Possíveis causas:")
        print("   1. O banco 'knn-benefits' pode não existir")
        print("   2. A chave de serviço pode não ter permissão para este banco")
        print("   3. O banco pode estar em uma região diferente")
        return False


if __name__ == "__main__":
    print("🧪 Testando acesso ao banco 'knn-benefits'...")
    print("="*50)
    
    success = test_knn_benefits_database()
    
    if success:
        print("\n🎉 Acesso ao banco 'knn-benefits' confirmado!")
    else:
        print("\n❌ Falha no acesso ao banco 'knn-benefits'")
        print("\n📋 Próximos passos:")
        print("   1. Verificar se o banco 'knn-benefits' existe no Firebase Console")
        print("   2. Confirmar permissões da chave de serviço")
        print("   3. Verificar se o banco foi criado na região correta")