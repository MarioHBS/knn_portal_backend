#!/usr/bin/env python3
"""
Script gerado automaticamente para importar dados no Firestore.

Uso:
1. Configure as credenciais do Firebase
2. Execute: python import_to_firestore.py
"""

import json
import os

import firebase_admin
from firebase_admin import credentials, firestore


def import_data_to_firestore(project_id: str, data_file: str, use_emulator: bool = True):
    """Importa dados para o Firestore."""
    # Configurar emulador se solicitado
    if use_emulator:
        os.environ["FIRESTORE_EMULATOR_HOST"] = "localhost:8082"
        os.environ["GCLOUD_PROJECT"] = project_id
        print("🔧 Usando emulador do Firestore em localhost:8082")

    # Inicializar Firebase
    if not firebase_admin._apps:
        try:
            if use_emulator:
                # Para emulador, usar credenciais mock
                import google.auth.credentials
                mock_credentials = google.auth.credentials.AnonymousCredentials()
                firebase_admin.initialize_app(
                    credential=mock_credentials,
                    options={"projectId": project_id}
                )
            else:
                cred = credentials.ApplicationDefault()
                firebase_admin.initialize_app(cred, {"projectId": project_id})
        except Exception as e:
            print(f"⚠️  Erro ao inicializar Firebase: {e}")
            print("💡 Tentando usar modo de teste local...")
            # Fallback para modo de teste
            try:
                import google.auth.credentials
                mock_credentials = google.auth.credentials.AnonymousCredentials()
                firebase_admin.initialize_app(
                    credential=mock_credentials,
                    options={"projectId": project_id}
                )
            except Exception:
                firebase_admin.initialize_app(options={"projectId": project_id})

    db = firestore.client()

    # Carregar dados
    with open(data_file, encoding='utf-8') as f:
        data = json.load(f)

    # Importar estudantes
    students = data.get('students', [])
    print(f"Importando {len(students)} estudantes...")

    batch = db.batch()
    batch_count = 0

    for student in students:
        doc_ref = db.collection('students').document(student['id'])
        batch.set(doc_ref, student['data'])
        batch_count += 1

        if batch_count >= 500:
            batch.commit()
            batch = db.batch()
            batch_count = 0

    if batch_count > 0:
        batch.commit()

    # Importar funcionários
    employees = data.get('employees', [])
    print(f"Importando {len(employees)} funcionários...")

    batch = db.batch()
    batch_count = 0

    for employee in employees:
        doc_ref = db.collection('employees').document(employee['id'])
        batch.set(doc_ref, employee['data'])
        batch_count += 1

        if batch_count >= 500:
            batch.commit()
            batch = db.batch()
            batch_count = 0

    if batch_count > 0:
        batch.commit()

    print(f"Importação concluída: {len(students)} estudantes, {len(employees)} funcionários")

if __name__ == "__main__":
    import sys

    # Verificar se deve usar emulador ou credenciais reais (padrão)
    use_emulator = False
    if len(sys.argv) > 1 and sys.argv[1] == "--emulator":
        use_emulator = True
        print("🧪 Usando emulador local do Firestore (modo de teste)")
    else:
        print("🔐 Usando credenciais reais do Firebase")
        print("💡 Para usar emulador, execute: python import_to_firestore.py --emulator")

    # Configurar os projetos
    projects = {
        "default": "knn-portal-dev",
        "production": "knn-benefits"
    }

    for env, project_id in projects.items():
        print(f"\n=== Importando para {env} ({project_id}) ===")
        try:
            import_data_to_firestore(project_id, f"firestore_data_{env}.json", use_emulator)
        except Exception as e:
            print(f"❌ Erro na importação para {env}: {str(e)}")
            if not use_emulator:
                print("💡 Tente executar sem --real para usar o emulador local")
