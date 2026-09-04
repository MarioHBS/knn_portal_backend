#!/usr/bin/env python3
"""
Script para adicionar funcionário como administrador no Firebase Authentication.

Este script:
1. Cria um usuário administrador no Firebase Authentication
2. Substitui o documento na coleção 'users' com o novo UID
3. Mantém os dados do funcionário existente

Uso:
    python scripts/maintenance/add_admin_user.py
"""

import sys
from datetime import UTC, datetime
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.append(str(Path(__file__).parent.parent.parent))

from firebase_admin import auth, firestore

from src.auth import initialize_firebase


def get_employee_data(employee_id: str) -> dict | None:
    """
    Obtém os dados do funcionário a partir dos arquivos de export.

    Args:
        employee_id: ID do funcionário (ex: EMP_F0F0O069_CC)

    Returns:
        dict: Dados do funcionário ou None se não encontrado
    """
    try:
        import json

        # Caminho para o arquivo de funcionários
        employees_file = (
            Path(__file__).parent.parent.parent
            / "data"
            / "firestore_export"
            / "firestore_employees.json"
        )

        if not employees_file.exists():
            print(f"❌ Arquivo de funcionários não encontrado: {employees_file}")
            return None

        with open(employees_file, encoding="utf-8") as f:
            data = json.load(f)

        employees = data.get("employees", {})
        employee_data = employees.get(employee_id)

        if not employee_data:
            print(f"❌ Funcionário {employee_id} não encontrado nos dados")
            return None

        return employee_data

    except Exception as e:
        print(f"❌ Erro ao obter dados do funcionário: {e}")
        return None


def create_admin_user(employee_data: dict, password: str) -> str | None:
    """
    Cria usuário administrador no Firebase Authentication.

    Args:
        employee_data: Dados do funcionário
        password: Senha inicial do usuário

    Returns:
        str: UID do usuário criado ou None se erro
    """
    try:
        email = employee_data.get("email")
        name = employee_data.get("name")

        if not email:
            print("❌ Email do funcionário não encontrado")
            return None

        # Verificar se usuário já existe
        try:
            existing_user = auth.get_user_by_email(email)
            print(f"ℹ️ Usuário já existe no Firebase Auth: {existing_user.uid}")

            # Atualizar custom claims para admin
            custom_claims = {
                "role": "admin",
                "tenant": "knn-dev-tenant",
                "entity_type": "employee",
                "entity_id": employee_data.get("id"),
            }

            auth.set_custom_user_claims(existing_user.uid, custom_claims)
            print("✅ Custom claims de admin aplicadas para usuário existente")

            return existing_user.uid

        except auth.UserNotFoundError:
            # Criar novo usuário
            user = auth.create_user(
                email=email,
                password=password,
                display_name=name,
                email_verified=True,
            )
            print(f"✅ Usuário administrador criado: {user.uid}")

            # Definir custom claims
            custom_claims = {
                "role": "admin",
                "tenant": "knn-dev-tenant",
                "entity_type": "employee",
                "entity_id": employee_data.get("id"),
            }

            # Aplicar custom claims
            auth.set_custom_user_claims(user.uid, custom_claims)
            print("✅ Custom claims de admin aplicadas")

            return user.uid

    except Exception as e:
        print(f"❌ Erro ao criar usuário administrador: {e}")
        return None


def update_users_collection(old_uid: str, new_uid: str, employee_data: dict) -> bool:
    """
    Atualiza a coleção 'users' substituindo o documento antigo pelo novo UID.

    Args:
        old_uid: UID antigo do documento
        new_uid: Novo UID do Firebase Authentication
        employee_data: Dados do funcionário

    Returns:
        bool: True se sucesso, False se erro
    """
    try:
        db = firestore.client()

        # Preparar dados do novo documento
        user_data = {
            "role": "admin",
            "email": employee_data.get("email"),
            "tenant_id": "knn-dev-tenant",
            "first_access": True,
            "entity_id": employee_data.get("id"),
            "name": employee_data.get("name"),
            "id": new_uid,
            "updated_at": datetime.now(UTC),
            "created_at": datetime.now(UTC),
        }

        # Criar novo documento com o novo UID
        new_doc_ref = db.collection("users").document(new_uid)
        new_doc_ref.set(user_data)
        print(f"✅ Novo documento criado na coleção 'users': {new_uid}")

        # Remover documento antigo se for diferente
        if old_uid != new_uid:
            old_doc_ref = db.collection("users").document(old_uid)
            old_doc_ref.delete()
            print(f"✅ Documento antigo removido: {old_uid}")

        return True

    except Exception as e:
        print(f"❌ Erro ao atualizar coleção 'users': {e}")
        return False


def main():
    """Função principal do script."""
    print("🚀 Iniciando processo de adição de administrador...\n")

    # Configurações
    employee_id = "EMP_F0F0O069_CC"
    old_uid = "zRC8AsHsjlTDTHVf71AxyFmkEpx1"
    password = "Fo654321"

    try:
        # Inicializar Firebase
        print("🔧 Inicializando Firebase...")
        initialize_firebase()
        print("✅ Firebase inicializado com sucesso\n")

        # Obter dados do funcionário
        print(f"📋 Obtendo dados do funcionário {employee_id}...")
        employee_data = get_employee_data(employee_id)

        if not employee_data:
            print("❌ Não foi possível obter dados do funcionário")
            return False

        print(
            f"✅ Dados obtidos: {employee_data.get('name')} - {employee_data.get('email')}\n"
        )

        # Criar usuário administrador no Firebase Auth
        print("👤 Criando usuário administrador no Firebase Authentication...")
        new_uid = create_admin_user(employee_data, password)

        if not new_uid:
            print("❌ Falha ao criar usuário administrador")
            return False

        print(f"✅ Usuário administrador processado com UID: {new_uid}\n")

        # Atualizar coleção 'users'
        print("📝 Atualizando coleção 'users' no Firestore...")
        success = update_users_collection(old_uid, new_uid, employee_data)

        if not success:
            print("❌ Falha ao atualizar coleção 'users'")
            return False

        print("✅ Coleção 'users' atualizada com sucesso\n")

        # Resumo final
        print("🎉 PROCESSO CONCLUÍDO COM SUCESSO!")
        print(f"📧 Email: {employee_data.get('email')}")
        print(f"🔑 Senha: {password}")
        print(f"🆔 Novo UID: {new_uid}")
        print(f"👤 Nome: {employee_data.get('name')}")
        print("🏢 Função: admin")

        return True

    except Exception as e:
        print(f"❌ Erro geral no processo: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
