#!/usr/bin/env python3
"""
Script para testar conexão com Firebase Storage e Firestore
antes de fazer upload das imagens.
"""

import os
import sys
from pathlib import Path

# Adiciona o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

try:
    import firebase_admin
    from firebase_admin import credentials, storage, firestore
    print("✅ Firebase Admin SDK importado com sucesso")
except ImportError as e:
    print(f"❌ Erro ao importar Firebase Admin SDK: {e}")
    sys.exit(1)

def test_firebase_initialization():
    """Testa inicialização do Firebase."""
    try:
        # Verifica se já foi inicializado
        try:
            app = firebase_admin.get_app()
            print("✅ Firebase já inicializado")
            return True
        except ValueError:
            pass
        
        # Tenta inicializar com credenciais padrão
        try:
            cred = credentials.ApplicationDefault()
            firebase_admin.initialize_app(cred, {
                'storageBucket': 'knn-benefits-default.appspot.com'
            })
            print("✅ Firebase inicializado com credenciais padrão")
            return True
        except Exception as e:
            print(f"❌ Erro ao inicializar com credenciais padrão: {e}")
            
        # Tenta inicializar sem credenciais específicas
        try:
            firebase_admin.initialize_app()
            print("✅ Firebase inicializado sem credenciais específicas")
            return True
        except Exception as e:
            print(f"❌ Erro ao inicializar Firebase: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Erro geral na inicialização: {e}")
        return False

def test_storage_access():
    """Testa acesso ao Firebase Storage."""
    try:
        bucket = storage.bucket()
        print(f"✅ Acesso ao Storage obtido: {bucket.name}")
        
        # Testa listagem de arquivos (limitada)
        try:
            blobs = list(bucket.list_blobs(max_results=1))
            print(f"✅ Listagem de arquivos funcionando ({len(blobs)} arquivo(s) encontrado(s))")
        except Exception as e:
            print(f"⚠️  Listagem limitada: {e}")
            
        return True
    except Exception as e:
        print(f"❌ Erro ao acessar Storage: {e}")
        return False

def test_firestore_access():
    """Testa acesso ao Firestore."""
    try:
        db = firestore.client()
        print("✅ Cliente Firestore criado")
        
        # Testa leitura de uma coleção
        try:
            partners_ref = db.collection('partners')
            # Tenta obter apenas 1 documento para testar
            docs = list(partners_ref.limit(1).stream())
            print(f"✅ Acesso à coleção 'partners' funcionando ({len(docs)} documento(s) encontrado(s))")
            
            if docs:
                doc = docs[0]
                print(f"   Exemplo de documento: {doc.id}")
                data = doc.to_dict()
                if 'nome' in data:
                    print(f"   Nome: {data['nome']}")
                    
        except Exception as e:
            print(f"⚠️  Erro ao acessar coleção partners: {e}")
            
        return True
    except Exception as e:
        print(f"❌ Erro ao acessar Firestore: {e}")
        return False

def check_environment():
    """Verifica variáveis de ambiente relacionadas ao Firebase."""
    print("\n=== VERIFICAÇÃO DO AMBIENTE ===")
    
    # Verifica variáveis de ambiente
    env_vars = [
        'GOOGLE_APPLICATION_CREDENTIALS',
        'FIREBASE_PROJECT_ID',
        'GCLOUD_PROJECT'
    ]
    
    for var in env_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: não definida")
    
    # Verifica arquivos de credenciais conhecidos
    print("\n=== ARQUIVOS DE CREDENCIAIS ===")
    
    cred_files = [
        "data/firestore_import/default-service-account-key.json",
        "data/firestore_import/knn-benefits-service-account-key.json",
        "credentials/firebase-admin-key.json"
    ]
    
    for cred_file in cred_files:
        if os.path.exists(cred_file):
            print(f"✅ {cred_file}: encontrado")
        else:
            print(f"❌ {cred_file}: não encontrado")

def main():
    """Função principal de teste."""
    print("🔥 TESTE DE CONEXÃO FIREBASE\n")
    
    # Verifica ambiente
    check_environment()
    
    print("\n=== TESTE DE CONEXÃO ===")
    
    # Testa inicialização
    if not test_firebase_initialization():
        print("\n❌ Falha na inicialização do Firebase")
        print("\n💡 SOLUÇÕES POSSÍVEIS:")
        print("1. Configure GOOGLE_APPLICATION_CREDENTIALS com caminho para arquivo de credenciais")
        print("2. Execute 'gcloud auth application-default login' se tiver gcloud instalado")
        print("3. Obtenha arquivo de credenciais do Firebase Console")
        return False
    
    # Testa Storage
    print("\n--- Testando Firebase Storage ---")
    storage_ok = test_storage_access()
    
    # Testa Firestore
    print("\n--- Testando Firestore ---")
    firestore_ok = test_firestore_access()
    
    # Resultado final
    print("\n=== RESULTADO FINAL ===")
    if storage_ok and firestore_ok:
        print("✅ Todos os testes passaram! Pronto para fazer upload das imagens.")
        return True
    else:
        print("❌ Alguns testes falharam. Verifique as configurações antes de prosseguir.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)