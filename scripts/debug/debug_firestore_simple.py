#!/usr/bin/env python3
"""
Script simplificado para debugar consultas no Firestore.
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


def debug_firestore_query():
    """Debuga consultas no Firestore."""
    if not initialize_firebase():
        return False
    
    try:
        print("\n🔍 Debugando consultas no Firestore...")
        
        db = firestore.client()
        
        # Teste 1: Consulta apenas com tenant_id
        print("\n1️⃣ Teste: Consulta apenas com tenant_id")
        query = db.collection('partners').where('tenant_id', '==', 'knn-dev-tenant')
        docs = list(query.stream())
        
        print(f"   📊 Resultado: {len(docs)} parceiros")
        
        if docs:
            print("   ✅ Primeiros 3 parceiros:")
            for i, doc in enumerate(docs[:3]):
                data = doc.to_dict()
                print(f"     {i+1}. {data.get('trade_name', 'N/A')} (active: {data.get('active', 'N/A')})")
        
        # Teste 2: Consulta com tenant_id + active=True
        print("\n2️⃣ Teste: Consulta com tenant_id + active=True")
        query = db.collection('partners').where('tenant_id', '==', 'knn-dev-tenant').where('active', '==', True)
        docs = list(query.stream())
        
        print(f"   📊 Resultado: {len(docs)} parceiros")
        
        if docs:
            print("   ✅ Primeiros 3 parceiros:")
            for i, doc in enumerate(docs[:3]):
                data = doc.to_dict()
                print(f"     {i+1}. {data.get('trade_name', 'N/A')} (active: {data.get('active', 'N/A')})")
        
        # Teste 3: Consulta com ordenação
        print("\n3️⃣ Teste: Consulta com tenant_id + active=True + ordenação")
        try:
            query = db.collection('partners').where('tenant_id', '==', 'knn-dev-tenant').where('active', '==', True).order_by('trade_name')
            docs = list(query.stream())
            
            print(f"   📊 Resultado: {len(docs)} parceiros")
            
            if docs:
                print("   ✅ Primeiros 3 parceiros:")
                for i, doc in enumerate(docs[:3]):
                    data = doc.to_dict()
                    print(f"     {i+1}. {data.get('trade_name', 'N/A')} (active: {data.get('active', 'N/A')})")
        except Exception as e:
            print(f"   ❌ Erro na consulta com ordenação: {e}")
            print("   💡 Isso pode indicar que falta um índice composto no Firestore")
        
        # Teste 4: Verificar tipos de dados do campo active
        print("\n4️⃣ Teste: Verificar tipos de dados do campo active")
        query = db.collection('partners').where('tenant_id', '==', 'knn-dev-tenant')
        docs = list(query.stream())
        
        active_types = {}
        for doc in docs:
            data = doc.to_dict()
            active_value = data.get('active')
            active_type = type(active_value).__name__
            
            if active_type not in active_types:
                active_types[active_type] = []
            active_types[active_type].append(active_value)
        
        print("   📊 Tipos de dados encontrados no campo 'active':")
        for type_name, values in active_types.items():
            unique_values = list(set(values))
            print(f"     {type_name}: {unique_values}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no debug: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = debug_firestore_query()
    exit(0 if success else 1)