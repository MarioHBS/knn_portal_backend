#!/usr/bin/env python3
"""
Script para importar dados no Firestore usando chave de conta de serviço.

Uso:
1. Baixe a chave de conta de serviço do Firebase Console
2. Salve como 'service-account-key.json' neste diretório
3. Execute: python import_with_service_account.py
"""

import json
import os
import sys
from pathlib import Path

import firebase_admin
from firebase_admin import credentials
from google.cloud import firestore


def import_data_to_firestore(
    project_id: str, data_file: str, service_account_path: str = None, database_id: str = "(default)"
):
    """Importa dados para o Firestore usando conta de serviço."""

    # Limpar variáveis de ambiente do emulador
    if "FIRESTORE_EMULATOR_HOST" in os.environ:
        del os.environ["FIRESTORE_EMULATOR_HOST"]
    if "GCLOUD_PROJECT" in os.environ:
        del os.environ["GCLOUD_PROJECT"]

    # Limpar apps existentes para evitar conflitos
    apps_to_delete = list(firebase_admin._apps.values())
    for app in apps_to_delete:
        firebase_admin.delete_app(app)

    # Inicializar Firebase para o projeto específico
    try:
        if service_account_path and os.path.exists(service_account_path):
            print(f"🔑 Usando chave de conta de serviço: {service_account_path}")
            cred = credentials.Certificate(service_account_path)
            app = firebase_admin.initialize_app(cred, {"projectId": project_id})
        else:
            print("🔐 Tentando usar credenciais padrão da aplicação...")
            cred = credentials.ApplicationDefault()
            app = firebase_admin.initialize_app(cred, {"projectId": project_id})

        print(f"✅ Firebase inicializado para projeto: {project_id}, banco: {database_id}")

    except Exception as e:
        print(f"❌ Erro ao inicializar Firebase: {e}")
        print("\n💡 Soluções possíveis:")
        print("   1. Baixe a chave de conta de serviço do Firebase Console")
        print("   2. Salve como 'service-account-key.json' neste diretório")
        print("   3. Ou execute: gcloud auth application-default login")
        return False

    try:
        # Usar google-cloud-firestore para suporte a múltiplos bancos
        db = firestore.Client(project=project_id, database=database_id, credentials=cred.get_credential())

        # Carregar dados
        if not os.path.exists(data_file):
            print(f"❌ Arquivo não encontrado: {data_file}")
            return False

        with open(data_file, encoding="utf-8") as f:
            data = json.load(f)

        # Importar estudantes
        students = data.get("students", [])
        print(f"📚 Importando {len(students)} estudantes...")

        batch = db.batch()
        batch_count = 0

        for student in students:
            doc_ref = db.collection("students").document(student["id"])
            batch.set(doc_ref, student["data"])
            batch_count += 1

            if batch_count >= 500:
                batch.commit()
                print(f"   ✅ Importados {batch_count} estudantes")
                batch = db.batch()
                batch_count = 0

        if batch_count > 0:
            batch.commit()
            print(f"   ✅ Importados {batch_count} estudantes")

        # Importar funcionários
        employees = data.get("employees", [])
        print(f"👥 Importando {len(employees)} funcionários...")

        batch = db.batch()
        batch_count = 0

        for employee in employees:
            doc_ref = db.collection("employees").document(employee["id"])
            batch.set(doc_ref, employee["data"])
            batch_count += 1

            if batch_count >= 500:
                batch.commit()
                print(f"   ✅ Importados {batch_count} funcionários")
                batch = db.batch()
                batch_count = 0

        if batch_count > 0:
            batch.commit()
            print(f"   ✅ Importados {batch_count} funcionários")

        print("\n🎉 Importação concluída com sucesso!")
        print(f"   📊 Total: {len(students)} estudantes, {len(employees)} funcionários")
        return True

    except Exception as e:
        print(f"❌ Erro durante a importação: {e}")
        return False


if __name__ == "__main__":
    # Configurar chaves específicas para cada projeto
    current_dir = Path(__file__).parent
    
    # Configurar os bancos Firestore no projeto KNNBenefits
    # Existem dois bancos no mesmo projeto: (default) e knn-benefits
    projects = {
        "default": {
            "project_id": "knn-benefits",
            "database_id": "(default)",
            "service_account_files": [
                current_dir / "default-service-account-key.json",
                current_dir / "knn-benefits-service-account-key.json"
            ]
        },
        "production": {
            "project_id": "knn-benefits", 
            "database_id": "knn-benefits",
            "service_account_files": [
                current_dir / "knn-benefits-service-account-key.json",
                current_dir / "service-account-key.json"
            ]
        }
    }
    
    success_count = 0
    
    for env, config in projects.items():
        print(f"\n{'='*50}")
        print(f"🚀 Importando para {env} ({config['project_id']})")
        print(f"{'='*50}")
        
        # Procurar chave de conta de serviço específica para este projeto
        service_account_path = None
        for file_path in config['service_account_files']:
            if file_path.exists():
                service_account_path = str(file_path)
                break
        
        if not service_account_path:
            print(f"❌ Nenhuma chave de conta de serviço encontrada para {env}")
            print(f"   Arquivos procurados: {[str(f) for f in config['service_account_files']]}")
            continue
        
        data_file = f"firestore_data_{env}.json"
        
        if import_data_to_firestore(config['project_id'], data_file, service_account_path, config['database_id']):
            success_count += 1
        else:
            print(f"❌ Falha na importação para {env}")

    print(f"\n{'='*50}")
    print(f"📋 Resumo: {success_count}/{len(projects)} importações bem-sucedidas")
    print(f"{'='*50}")

    if success_count == 0:
        print("\n🔧 Para resolver problemas de autenticação:")
        print(
            "   1. Vá para Firebase Console > Configurações do projeto > Contas de serviço"
        )
        print("   2. Clique em 'Gerar nova chave privada'")
        print(
            "   3. Salve o arquivo JSON como 'service-account-key.json' neste diretório"
        )
        print("   4. Execute novamente este script")
        sys.exit(1)
