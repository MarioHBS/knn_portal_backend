#!/usr/bin/env python3
"""
Script para verificar a coleção 'users' no Firestore.

Autor: Sistema de Verificação
Data: 2025-09-07
Versão: 1.0
"""

import os
import sys

# Adicionar o diretório raiz ao path
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

import firebase_admin
from firebase_admin import firestore


def initialize_firebase():
    """Inicializa o Firebase Admin SDK."""
    try:
        # Tentar usar credenciais do arquivo
        credentials_path = "credentials/default-service-account-key.json"
        if os.path.exists(credentials_path):
            cred = firebase_admin.credentials.Certificate(credentials_path)
            firebase_admin.initialize_app(cred)
            print(
                f"✅ Firebase inicializado com credenciais do arquivo: {credentials_path}"
            )
            return True
    except Exception as e:
        print(f"⚠️ Erro ao inicializar com credenciais do arquivo: {e}")

    try:
        # Tentar usar credenciais padrão do sistema
        firebase_admin.initialize_app()
        print("✅ Firebase inicializado com credenciais padrão do sistema")
        return True
    except Exception as e:
        print(f"❌ Erro ao inicializar Firebase: {e}")
        return False


def verify_users_collection():
    """Verifica a coleção 'users' no Firestore."""
    try:
        db = firestore.client()
        users_ref = db.collection("users")

        print("\n🔍 Verificando coleção 'users'...")

        # Listar todos os documentos
        docs = users_ref.stream()
        users_data = []

        for doc in docs:
            user_data = doc.to_dict()
            user_data["document_id"] = doc.id
            users_data.append(user_data)

        print(f"📊 Encontrados {len(users_data)} documentos na coleção 'users'")

        if users_data:
            print("\n📋 DOCUMENTOS ENCONTRADOS:")
            print("=" * 80)

            for user in users_data:
                print(f"\n🆔 Document ID: {user['document_id']}")
                print(f"👤 Firebase UID: {user.get('firebase_uid', 'N/A')}")
                print(f"📧 Email: {user.get('email', 'N/A')}")
                print(f"🎭 Role: {user.get('role', 'N/A')}")
                print(f"🏢 Entity ID: {user.get('entity_id', 'N/A')}")
                print(f"🏠 Tenant ID: {user.get('tenant_id', 'N/A')}")
                print(f"✅ Active: {user.get('active', 'N/A')}")
                print(f"🧪 Is Temp: {user.get('is_temp', 'N/A')}")
                print(f"📅 Created At: {user.get('created_at', 'N/A')}")
                print(f"🔄 Last Sync: {user.get('last_sync', 'N/A')}")

                # Campos específicos por role
                role = user.get("role")
                if role == "student":
                    print(f"👨‍🎓 Nome: {user.get('nome_completo', 'N/A')}")
                    print(f"📚 Curso: {user.get('curso', 'N/A')}")
                    print(f"🕐 Período: {user.get('periodo', 'N/A')}")
                    print(f"📊 Status: {user.get('status', 'N/A')}")
                elif role == "employee":
                    print(f"👨‍💼 Nome: {user.get('nome_completo', 'N/A')}")
                    print(f"💼 Cargo: {user.get('cargo', 'N/A')}")
                    print(f"🏢 Departamento: {user.get('departamento', 'N/A')}")
                    print(f"📊 Status: {user.get('status', 'N/A')}")
                elif role == "partner":
                    print(f"🏢 Empresa: {user.get('nome_empresa', 'N/A')}")
                    print(f"🏷️ Categoria: {user.get('categoria', 'N/A')}")
                    print(f"⭐ Rating: {user.get('rating', 'N/A')}")
                    print(f"📊 Status: {user.get('status', 'N/A')}")

                print("-" * 80)

        # Verificar coleções específicas
        print("\n🔍 Verificando coleções específicas por role...")

        collections_to_check = ["students", "employees", "partners"]
        for collection_name in collections_to_check:
            try:
                collection_ref = db.collection(collection_name)
                docs = list(collection_ref.stream())
                print(f"📊 Coleção '{collection_name}': {len(docs)} documentos")

                if docs:
                    for doc in docs[:3]:  # Mostrar apenas os primeiros 3
                        data = doc.to_dict()
                        print(
                            f"  - {doc.id}: {data.get('nome_completo', data.get('nome_empresa', 'N/A'))}"
                        )
                    if len(docs) > 3:
                        print(f"  ... e mais {len(docs) - 3} documentos")
            except Exception as e:
                print(f"❌ Erro ao verificar coleção '{collection_name}': {e}")

        return users_data

    except Exception as e:
        print(f"❌ Erro ao verificar coleção 'users': {e}")
        return []


def main():
    """Função principal."""
    print("🔍 Verificando coleção 'users' no Firestore")
    print("=" * 50)

    # Inicializar Firebase
    if not initialize_firebase():
        print("❌ Falha na inicialização do Firebase. Abortando.")
        return

    # Verificar coleção users
    users_data = verify_users_collection()

    print(f"\n🎉 Verificação concluída! Encontrados {len(users_data)} usuários.")


if __name__ == "__main__":
    main()