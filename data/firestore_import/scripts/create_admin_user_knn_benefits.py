#!/usr/bin/env python3
"""
Script para criar usuário administrador no projeto knn-benefits.
Este é o projeto onde temos credenciais válidas.
"""

import json

import firebase_admin
from firebase_admin import auth, credentials

# Configurações
FIREBASE_CREDENTIALS_PATH = "data/firestore_import/default-service-account-key.json"
ADMIN_EMAIL = "developer.mario.santos@gmail.com"
ADMIN_PASSWORD = "Admin123!@#"


def create_admin_user():
    """Cria usuário administrador no projeto knn-benefits."""

    print("🚀 Criando usuário administrador no projeto knn-benefits...\n")

    try:
        # 1. Configurar Firebase
        if not firebase_admin._apps:
            cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
            app = firebase_admin.initialize_app(cred)
            print(f"✅ Firebase inicializado para projeto: {app.project_id}")

        # 2. Verificar se usuário já existe
        try:
            existing_user = auth.get_user_by_email(ADMIN_EMAIL)
            print(f"ℹ️ Usuário já existe: {existing_user.uid}")
            user = existing_user
        except auth.UserNotFoundError:
            # 3. Criar usuário administrador
            user = auth.create_user(
                email=ADMIN_EMAIL,
                password=ADMIN_PASSWORD,
                display_name="Mario Santos (Admin)",
                email_verified=True,
            )
            print(f"✅ Usuário criado: {user.uid}")

        # 4. Definir custom claims
        custom_claims = {
            "role": "admin",
            "tenant": "knn-dev-tenant",
            "permissions": {
                "read_all": True,
                "write_all": True,
                "manage_users": True,
                "view_metrics": True,
            },
        }

        # 5. Aplicar custom claims
        auth.set_custom_user_claims(user.uid, custom_claims)
        print("✅ Custom claims aplicadas")

        # 6. Verificar custom claims
        updated_user = auth.get_user(user.uid)
        claims = updated_user.custom_claims or {}
        print(f"✅ Custom claims verificadas: {json.dumps(claims, indent=2)}")

        # 7. Criar token personalizado para teste
        custom_token = auth.create_custom_token(user.uid, custom_claims)
        if isinstance(custom_token, bytes):
            custom_token = custom_token.decode("utf-8")

        print("\n🎯 Usuário administrador configurado com sucesso!")
        print(f"   - Email: {ADMIN_EMAIL}")
        print(f"   - UID: {user.uid}")
        print("   - Projeto: knn-benefits")
        print(f"   - Role: {claims.get('role')}")
        print(f"   - Tenant: {claims.get('tenant')}")
        print(f"   - Token (primeiros 50 chars): {custom_token[:50]}...")

        # 8. Salvar informações do usuário
        user_info = {
            "email": ADMIN_EMAIL,
            "uid": user.uid,
            "project_id": "knn-benefits",
            "role": claims.get("role"),
            "tenant": claims.get("tenant"),
            "custom_token": custom_token,
            "permissions": claims.get("permissions", {}),
        }

        with open("admin_user_knn_benefits.json", "w", encoding="utf-8") as f:
            json.dump(user_info, f, indent=2, ensure_ascii=False)

        print("\n💾 Informações salvas em: admin_user_knn_benefits.json")

        return user_info

    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback

        print(f"Stack trace: {traceback.format_exc()}")
        return None


if __name__ == "__main__":
    create_admin_user()
