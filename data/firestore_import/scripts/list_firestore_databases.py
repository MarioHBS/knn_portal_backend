#!/usr/bin/env python3
"""
Script para listar os bancos de dados Firestore disponíveis
"""

import os

import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud import firestore as gcs_firestore
from google.oauth2 import service_account


def test_firestore_connection(project_id, service_account_path):
    """
    Testa a conexão com o Firestore e verifica se consegue acessar o banco

    Args:
        project_id (str): ID do projeto Firebase/GCP
        service_account_path (str): Caminho para o arquivo de chave da conta de serviço

    Returns:
        dict: Informações sobre a conexão e banco de dados
    """
    try:
        print(f"🔍 Testando conexão Firestore para o projeto: {project_id}")
        print(f"🔑 Usando chave: {os.path.basename(service_account_path)}")
        print("=" * 60)

        # Método 1: Usando Firebase Admin SDK
        try:
            # Limpar apps existentes
            import contextlib

            with contextlib.suppress(ValueError):
                firebase_admin.delete_app(firebase_admin.get_app())

            cred = credentials.Certificate(service_account_path)
            app = firebase_admin.initialize_app(cred, {"projectId": project_id})

            db = firestore.client()

            # Tentar listar coleções (isso confirma que temos acesso)
            collections = db.collections()
            collection_names = []

            print("📚 Coleções encontradas:")
            for collection in collections:
                collection_names.append(collection.id)
                print(f"   - {collection.id}")

            if not collection_names:
                print(
                    "   (Nenhuma coleção encontrada - banco vazio ou sem permissões de leitura)"
                )

            result = {
                "status": "success",
                "project_id": project_id,
                "database_id": "(default)",  # Firebase Admin sempre usa o banco padrão
                "collections": collection_names,
                "method": "Firebase Admin SDK",
            }

            firebase_admin.delete_app(app)
            return result

        except Exception as firebase_error:
            print(f"❌ Erro com Firebase Admin SDK: {str(firebase_error)}")

            # Método 2: Usando Google Cloud Firestore diretamente
            try:
                credentials_obj = service_account.Credentials.from_service_account_file(
                    service_account_path,
                    scopes=["https://www.googleapis.com/auth/cloud-platform"],
                )

                client = gcs_firestore.Client(
                    project=project_id, credentials=credentials_obj
                )

                # Tentar listar coleções
                collections = client.collections()
                collection_names = []

                print("📚 Coleções encontradas (Google Cloud SDK):")
                for collection in collections:
                    collection_names.append(collection.id)
                    print(f"   - {collection.id}")

                if not collection_names:
                    print(
                        "   (Nenhuma coleção encontrada - banco vazio ou sem permissões de leitura)"
                    )

                return {
                    "status": "success",
                    "project_id": project_id,
                    "database_id": "(default)",
                    "collections": collection_names,
                    "method": "Google Cloud SDK",
                }

            except Exception as gcs_error:
                print(f"❌ Erro com Google Cloud SDK: {str(gcs_error)}")

                return {
                    "status": "error",
                    "project_id": project_id,
                    "firebase_error": str(firebase_error),
                    "gcs_error": str(gcs_error),
                }

    except Exception as e:
        print(f"❌ Erro geral: {str(e)}")
        return {"status": "error", "project_id": project_id, "error": str(e)}


def main():
    """
    Função principal - testa conexão com Firestore para ambos os projetos
    """
    # Configurações dos projetos
    projects = [
        {
            "name": "knn-portal-dev (Default)",
            "project_id": "knn-portal-dev",
            "service_account": "default-service-account-key.json",
        },
        {
            "name": "knn-benefits (Production)",
            "project_id": "knn-benefits",
            "service_account": "knn-benefits-service-account-key.json",
        },
    ]

    all_results = {}

    for project in projects:
        print(f"\n{'='*80}")
        print(f"🚀 PROJETO: {project['name']}")
        print(f"{'='*80}")

        service_account_path = os.path.join(
            os.path.dirname(__file__), project["service_account"]
        )

        if not os.path.exists(service_account_path):
            print(f"❌ Arquivo de chave não encontrado: {service_account_path}")
            all_results[project["project_id"]] = {
                "status": "error",
                "error": "Arquivo de chave não encontrado",
            }
            continue

        result = test_firestore_connection(project["project_id"], service_account_path)
        all_results[project["project_id"]] = result

        if result["status"] == "success":
            print("✅ Conexão bem-sucedida!")
            print(f"   📊 Banco: {result['database_id']}")
            print(f"   📚 Coleções: {len(result['collections'])}")
            print(f"   🔧 Método: {result['method']}")
        else:
            print("❌ Falha na conexão")

    # Resumo final
    print(f"\n{'='*80}")
    print("📋 RESUMO FINAL - BANCOS DE DADOS FIRESTORE")
    print(f"{'='*80}")

    for project_id, result in all_results.items():
        if result["status"] == "success":
            print(f"✅ {project_id}:")
            print(f"   📊 Banco de dados: {result['database_id']}")
            print(
                f"   📚 Coleções ({len(result['collections'])}): {', '.join(result['collections']) if result['collections'] else 'Nenhuma'}"
            )
            print(f"   🔧 Método de acesso: {result['method']}")
        else:
            print(f"❌ {project_id}: Falha na conexão")
            if "error" in result:
                print(f"   🚫 Erro: {result['error']}")
            if "firebase_error" in result:
                print(f"   🔥 Firebase: {result['firebase_error']}")
            if "gcs_error" in result:
                print(f"   ☁️  GCS: {result['gcs_error']}")
        print()

    # Informações adicionais sobre bancos de dados Firestore
    print("ℹ️  INFORMAÇÕES SOBRE BANCOS DE DADOS FIRESTORE:")
    print(
        "   • Cada projeto Firebase/GCP tem um banco Firestore padrão chamado '(default)'"
    )
    print(
        "   • É possível criar bancos adicionais, mas isso requer configuração específica"
    )
    print(
        "   • O banco '(default)' é criado automaticamente quando você usa o Firestore"
    )
    print(
        "   • As coleções listadas são as que existem no banco e são acessíveis com as credenciais fornecidas"
    )

    print("\n✅ Análise de bancos de dados concluída!")


if __name__ == "__main__":
    main()
