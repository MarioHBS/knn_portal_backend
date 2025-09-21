#!/usr/bin/env python3
"""
Script para sincronizar a coleção 'users' no Firestore com Firebase Auth
e verificar consistência com documentos específicos por role.

Autor: Sistema de Sincronização
Data: 2025-09-07
Versão: 1.0
"""

import json
import os
import sys
from datetime import datetime

# Adicionar o diretório raiz ao path
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

import firebase_admin
from firebase_admin import auth, firestore


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


def load_test_entities():
    """Carrega as entidades de teste do arquivo JSON."""
    try:
        with open("credentials/temp_test_entities.json", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ Arquivo de entidades de teste não encontrado")
        return None
    except Exception as e:
        print(f"❌ Erro ao carregar entidades de teste: {e}")
        return None


def get_firestore_client():
    """Obtém o cliente do Firestore."""
    try:
        return firestore.client()
    except Exception as e:
        print(f"❌ Erro ao conectar com Firestore: {e}")
        return None


def get_auth_users():
    """Lista todos os usuários do Firebase Auth."""
    try:
        users = []
        page = auth.list_users()
        while page:
            for user in page.users:
                users.append(user)
            page = page.get_next_page()
        return users
    except Exception as e:
        print(f"❌ Erro ao listar usuários do Auth: {e}")
        return []


def validate_user_document(user_data, role):
    """Valida se um documento de usuário tem todos os campos obrigatórios."""
    required_fields = {
        "common": [
            "firebase_uid",
            "email",
            "tenant_id",
            "active",
            "created_at",
            "updated_at",
        ],
        "student": ["nome_completo", "cpf", "curso", "periodo", "status"],
        "employee": ["nome_completo", "cpf", "cargo", "departamento", "status"],
        "partner": ["nome_empresa", "cnpj", "categoria", "status"],
    }

    missing_fields = []

    # Verificar campos comuns
    for field in required_fields["common"]:
        if field not in user_data or user_data[field] is None:
            missing_fields.append(field)

    # Verificar campos específicos do role
    if role in required_fields:
        for field in required_fields[role]:
            if field not in user_data or user_data[field] is None:
                missing_fields.append(field)

    return missing_fields


def sync_users_collection(db, test_entities):
    """Sincroniza a coleção 'users' com os dados do Firebase Auth."""
    print("\n🔄 Iniciando sincronização da coleção 'users'...")

    # Obter usuários do Firebase Auth
    auth_users = get_auth_users()
    print(f"📊 Encontrados {len(auth_users)} usuários no Firebase Auth")

    # Mapear usuários por UID
    auth_users_map = {user.uid: user for user in auth_users}

    sync_results = {
        "synced": 0,
        "errors": 0,
        "inconsistencies": [],
        "missing_fields": [],
    }

    # Processar entidades de teste
    for role, entity_data in test_entities.items():
        firebase_uid = entity_data["firebase_uid"]
        entity_id = entity_data["entity_id"]
        firestore_data = entity_data["firestore_data"]

        print(f"\n🔍 Processando {role}: {entity_id}")

        # Verificar se o usuário existe no Auth
        if firebase_uid not in auth_users_map:
            sync_results["inconsistencies"].append(
                {
                    "type": "missing_auth_user",
                    "entity_id": entity_id,
                    "firebase_uid": firebase_uid,
                    "role": role,
                }
            )
            print(f"⚠️ Usuário {firebase_uid} não encontrado no Firebase Auth")
            continue

        auth_user = auth_users_map[firebase_uid]

        # Preparar documento para a coleção 'users'
        user_doc = {
            "firebase_uid": firebase_uid,
            "email": auth_user.email,
            "role": role,
            "entity_id": entity_id,
            "tenant_id": firestore_data.get("tenant_id", "knn-dev-tenant"),
            "active": firestore_data.get("active", True),
            "is_temp": firestore_data.get("is_temp", False),
            "created_by": firestore_data.get("created_by", "sync_script"),
            "created_at": firestore_data.get("created_at"),
            "updated_at": datetime.now().isoformat(),
            "last_sync": datetime.now().isoformat(),
        }

        # Adicionar campos específicos baseados no role
        if role == "student":
            user_doc.update(
                {
                    "nome_completo": firestore_data.get("nome_completo"),
                    "cpf": firestore_data.get("cpf"),
                    "curso": firestore_data.get("curso"),
                    "periodo": firestore_data.get("periodo"),
                    "semestre": firestore_data.get("semestre"),
                    "status": firestore_data.get("status"),
                }
            )
        elif role == "employee":
            user_doc.update(
                {
                    "nome_completo": firestore_data.get("nome_completo"),
                    "cpf": firestore_data.get("cpf"),
                    "cargo": firestore_data.get("cargo"),
                    "departamento": firestore_data.get("departamento"),
                    "status": firestore_data.get("status"),
                }
            )
        elif role == "partner":
            user_doc.update(
                {
                    "nome_empresa": firestore_data.get("nome_empresa"),
                    "cnpj": firestore_data.get("cnpj"),
                    "categoria": firestore_data.get("categoria"),
                    "status": firestore_data.get("status"),
                    "rating": firestore_data.get("rating"),
                    "total_beneficios": firestore_data.get("total_beneficios"),
                }
            )

        # Validar campos obrigatórios
        missing_fields = validate_user_document(user_doc, role)
        if missing_fields:
            sync_results["missing_fields"].append(
                {"entity_id": entity_id, "role": role, "missing_fields": missing_fields}
            )
            print(f"⚠️ Campos obrigatórios ausentes: {', '.join(missing_fields)}")

        # Salvar/atualizar documento na coleção 'users'
        try:
            users_ref = db.collection("users")
            users_ref.document(firebase_uid).set(user_doc, merge=True)
            sync_results["synced"] += 1
            print("✅ Documento sincronizado na coleção 'users'")

            # Verificar consistência com coleção específica
            verify_role_collection_consistency(
                db, role, entity_id, firestore_data, sync_results
            )

        except Exception as e:
            sync_results["errors"] += 1
            print(f"❌ Erro ao sincronizar documento: {e}")

    return sync_results


def verify_role_collection_consistency(
    db, role, entity_id, firestore_data, sync_results
):
    """Verifica consistência entre coleção 'users' e coleções específicas por role."""
    collection_names = {
        "student": "students",
        "employee": "employees",
        "partner": "partners",
    }

    if role not in collection_names:
        return

    collection_name = collection_names[role]

    try:
        # Verificar se o documento existe na coleção específica
        doc_ref = db.collection(collection_name).document(entity_id)
        doc = doc_ref.get()

        if not doc.exists:
            sync_results["inconsistencies"].append(
                {
                    "type": "missing_role_document",
                    "entity_id": entity_id,
                    "role": role,
                    "collection": collection_name,
                }
            )
            print(
                f"⚠️ Documento {entity_id} não encontrado na coleção {collection_name}"
            )

            # Criar documento na coleção específica
            doc_ref.set(firestore_data, merge=True)
            print(f"✅ Documento criado na coleção {collection_name}")
        else:
            # Verificar se os dados estão consistentes
            existing_data = doc.to_dict()
            key_fields = ["firebase_uid", "email", "active", "tenant_id"]

            for field in key_fields:
                if existing_data.get(field) != firestore_data.get(field):
                    sync_results["inconsistencies"].append(
                        {
                            "type": "data_mismatch",
                            "entity_id": entity_id,
                            "role": role,
                            "field": field,
                            "users_value": firestore_data.get(field),
                            "role_collection_value": existing_data.get(field),
                        }
                    )
                    print(
                        f"⚠️ Inconsistência no campo {field}: users={firestore_data.get(field)}, {collection_name}={existing_data.get(field)}"
                    )

    except Exception as e:
        print(f"❌ Erro ao verificar consistência com {collection_name}: {e}")


def generate_sync_report(sync_results):
    """Gera relatório de sincronização."""
    print("\n" + "=" * 60)
    print("📋 RELATÓRIO DE SINCRONIZAÇÃO")
    print("=" * 60)

    print(f"✅ Documentos sincronizados: {sync_results['synced']}")
    print(f"❌ Erros: {sync_results['errors']}")
    print(f"⚠️ Inconsistências encontradas: {len(sync_results['inconsistencies'])}")
    print(f"⚠️ Campos obrigatórios ausentes: {len(sync_results['missing_fields'])}")

    if sync_results["inconsistencies"]:
        print("\n🔍 INCONSISTÊNCIAS DETALHADAS:")
        for inconsistency in sync_results["inconsistencies"]:
            print(f"  - {inconsistency}")

    if sync_results["missing_fields"]:
        print("\n📝 CAMPOS OBRIGATÓRIOS AUSENTES:")
        for missing in sync_results["missing_fields"]:
            print(
                f"  - {missing['entity_id']} ({missing['role']}): {', '.join(missing['missing_fields'])}"
            )

    # Salvar relatório em arquivo
    report_data = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "synced": sync_results["synced"],
            "errors": sync_results["errors"],
            "inconsistencies_count": len(sync_results["inconsistencies"]),
            "missing_fields_count": len(sync_results["missing_fields"]),
        },
        "details": sync_results,
    }

    report_file = (
        f"reports/sync_users_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    os.makedirs("reports", exist_ok=True)

    try:
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        print(f"\n📄 Relatório salvo em: {report_file}")
    except Exception as e:
        print(f"❌ Erro ao salvar relatório: {e}")


def main():
    """Função principal."""
    print("🚀 Iniciando sincronização da coleção 'users' com Firebase Auth")
    print("=" * 60)

    # Inicializar Firebase
    if not initialize_firebase():
        print("❌ Falha na inicialização do Firebase. Abortando.")
        return

    # Carregar entidades de teste
    test_entities = load_test_entities()
    if not test_entities:
        print("❌ Não foi possível carregar as entidades de teste. Abortando.")
        return

    # Obter cliente Firestore
    db = get_firestore_client()
    if not db:
        print("❌ Não foi possível conectar ao Firestore. Abortando.")
        return

    # Executar sincronização
    sync_results = sync_users_collection(db, test_entities)

    # Gerar relatório
    generate_sync_report(sync_results)

    print("\n🎉 Sincronização concluída!")


if __name__ == "__main__":
    main()
