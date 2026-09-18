#!/usr/bin/env python3
"""
Script para criar índice composto no Firestore para consultas de parceiros.

O índice necessário é:
- Collection: partners
- Fields: tenant_id (Ascending), active (Ascending), trade_name (Ascending)
"""

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


def create_firestore_index():
    """Cria o índice composto necessário no Firestore."""
    if not initialize_firebase():
        return False
    
    try:
        print("\n🔍 Informações sobre o índice necessário:")
        print("   📋 Collection: partners")
        print("   📋 Fields:")
        print("     - tenant_id (Ascending)")
        print("     - active (Ascending)")
        print("     - trade_name (Ascending)")
        
        print("\n⚠️  IMPORTANTE:")
        print("   Os índices compostos no Firestore devem ser criados manualmente")
        print("   através do Console do Firebase ou usando a CLI do Firebase.")
        
        print("\n🔗 Link direto para criar o índice:")
        
        # URL gerada pelo erro anterior
        index_url = ("https://console.firebase.google.com/v1/r/project/knn-benefits/firestore/indexes?"
                    "create_composite=Ck1wcm9qZWN0cy9rbm4tYmVuZWZpdHMvZGF0YWJhc2VzLyhkZWZhdWx0KS9jb2xsZWN0aW9uR3J"
                    "vdXBzL3BhcnRuZXJzL2luZGV4ZXMvXxABGgoKBmFjdGl2ZRABGg0KCXRlbmFudF9pZBABGg4KCnRyYWRlX25hbWUQ"
                    "ARoMCghfX25hbWVfXxAB")
        
        print(f"   {index_url}")
        
        print("\n📝 Alternativamente, você pode:")
        print("   1. Acessar o Console do Firebase")
        print("   2. Ir para Firestore Database > Indexes")
        print("   3. Criar um índice composto com os campos:")
        print("      - tenant_id (Ascending)")
        print("      - active (Ascending)")
        print("      - trade_name (Ascending)")
        
        print("\n🚀 Ou usar a Firebase CLI:")
        print("   firebase firestore:indexes")
        
        # Testar a consulta que precisa do índice
        print("\n🧪 Testando a consulta que precisa do índice...")
        db = firestore.client()
        
        try:
            query = (db.collection('partners')
                    .where('tenant_id', '==', 'knn-dev-tenant')
                    .where('active', '==', True)
                    .order_by('trade_name'))
            
            docs = list(query.stream())
            print(f"   ✅ Consulta funcionou! {len(docs)} parceiros encontrados")
            return True
            
        except Exception as e:
            if "requires an index" in str(e):
                print("   ❌ Consulta falhou - índice ainda não existe")
                print("   💡 Crie o índice usando o link acima")
                return False
            else:
                print(f"   ❌ Erro inesperado: {e}")
                return False
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = create_firestore_index()
    exit(0 if success else 1)