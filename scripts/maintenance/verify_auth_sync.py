#!/usr/bin/env python3
"""
Script para verificar se os usuários do Firestore existem no Firebase Authentication.
"""

import os
import sys

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import firebase_admin
from firebase_admin import auth, credentials, firestore


def verify_auth_sync():
    """
    Verifica se todos os usuários do Firestore existem no Firebase Authentication.
    """
    try:
        # Inicializar Firebase se não estiver inicializado
        if not firebase_admin._apps:
            try:
                cred = credentials.ApplicationDefault()
                firebase_admin.initialize_app(cred)
                print("✅ Firebase inicializado com credenciais padrão")
            except Exception as e:
                print(f"⚠️  Erro com credenciais padrão: {e}")
                firebase_admin.initialize_app()
                print("✅ Firebase inicializado sem credenciais")

        db = firestore.client()
        print("✅ Cliente Firestore criado")

        print("\n=== VERIFICANDO SINCRONIZAÇÃO FIRESTORE <-> AUTHENTICATION ===")

        # Obter todos os usuários do Firestore
        users_ref = db.collection("users")
        firestore_users = users_ref.stream()

        firestore_user_list = []
        for doc in firestore_users:
            user_data = doc.to_dict()
            firestore_user_list.append(
                {
                    "uid": doc.id,
                    "name": user_data.get("name", "N/A"),
                    "email": user_data.get("e-mail", user_data.get("email", "N/A")),
                    "role": user_data.get("role", "N/A"),
                    "tenant_id": user_data.get(
                        "tenant_id", user_data.get("tenant", "N/A")
                    ),
                    "firebase_uid": user_data.get("firebase_uid", doc.id),
                }
            )

        print(f"📊 Total de usuários no Firestore: {len(firestore_user_list)}")

        # Verificar cada usuário no Firebase Authentication
        sync_results = {"synced": [], "not_in_auth": [], "auth_errors": []}

        print("\n🔍 VERIFICANDO CADA USUÁRIO NO FIREBASE AUTHENTICATION...\n")

        for user in firestore_user_list:
            uid = user["firebase_uid"] if user["firebase_uid"] != "N/A" else user["uid"]

            try:
                # Tentar obter o usuário do Firebase Authentication
                auth_user = auth.get_user(uid)

                print(f"✅ SINCRONIZADO: {uid}")
                print(f"   Nome Firestore: {user['name']}")
                print(f"   Email Firestore: {user['email']}")
                print(f"   Role: {user['role']}")
                print(f"   Tenant: {user['tenant_id']}")
                print(f"   Email Authentication: {auth_user.email}")
                print(f"   Verificado: {auth_user.email_verified}")
                print(f"   Criado em: {auth_user.user_metadata.creation_timestamp}")
                print(
                    f"   Último login: {auth_user.user_metadata.last_sign_in_timestamp}"
                )

                # Verificar se os emails coincidem
                firestore_email = user["email"]
                auth_email = auth_user.email or "N/A"

                if firestore_email != "N/A" and auth_email != "N/A":
                    if firestore_email.lower() != auth_email.lower():
                        print("   ⚠️  ATENÇÃO: Emails diferentes!")
                        print(f"      Firestore: {firestore_email}")
                        print(f"      Auth: {auth_email}")

                sync_results["synced"].append(
                    {
                        "uid": uid,
                        "firestore_data": user,
                        "auth_data": {
                            "email": auth_user.email,
                            "email_verified": auth_user.email_verified,
                            "creation_timestamp": auth_user.user_metadata.creation_timestamp,
                            "last_sign_in_timestamp": auth_user.user_metadata.last_sign_in_timestamp,
                        },
                    }
                )

            except auth.UserNotFoundError:
                print(f"❌ NÃO ENCONTRADO NO AUTHENTICATION: {uid}")
                print(f"   Nome: {user['name']}")
                print(f"   Email: {user['email']}")
                print(f"   Role: {user['role']}")
                print(
                    "   ⚠️  Este usuário existe no Firestore mas não no Authentication!"
                )

                sync_results["not_in_auth"].append(user)

            except Exception as e:
                print(f"⚠️  ERRO AO VERIFICAR: {uid}")
                print(f"   Erro: {str(e)}")
                print(f"   Nome: {user['name']}")
                print(f"   Email: {user['email']}")

                sync_results["auth_errors"].append(
                    {"uid": uid, "error": str(e), "user_data": user}
                )

            print()

        # Resumo final
        print("=" * 80)
        print("📊 RESUMO DA VERIFICAÇÃO DE SINCRONIZAÇÃO")
        print("=" * 80)

        total_users = len(firestore_user_list)
        synced_count = len(sync_results["synced"])
        not_in_auth_count = len(sync_results["not_in_auth"])
        error_count = len(sync_results["auth_errors"])

        print(f"📈 Total de usuários no Firestore: {total_users}")
        print(f"✅ Sincronizados corretamente: {synced_count}")
        print(f"❌ Não encontrados no Authentication: {not_in_auth_count}")
        print(f"⚠️  Erros durante verificação: {error_count}")

        sync_percentage = (synced_count / total_users * 100) if total_users > 0 else 0
        print(f"📊 Taxa de sincronização: {sync_percentage:.1f}%")

        if sync_percentage == 100:
            print("\n🎉 EXCELENTE! Todos os usuários estão sincronizados!")
        elif sync_percentage >= 80:
            print("\n✅ BOM! A maioria dos usuários está sincronizada.")
        else:
            print("\n⚠️  ATENÇÃO! Há problemas significativos de sincronização.")

        # Detalhes dos problemas
        if not_in_auth_count > 0:
            print("\n❌ USUÁRIOS NÃO ENCONTRADOS NO AUTHENTICATION:")
            for user in sync_results["not_in_auth"]:
                print(
                    f"   - {user['uid']}: {user['name']} ({user['email']}) - Role: {user['role']}"
                )

        if error_count > 0:
            print("\n⚠️  ERROS DURANTE VERIFICAÇÃO:")
            for error_info in sync_results["auth_errors"]:
                print(f"   - {error_info['uid']}: {error_info['error']}")

        # Recomendações
        print("\n💡 RECOMENDAÇÕES:")
        if not_in_auth_count > 0:
            print("   1. Criar usuários faltantes no Firebase Authentication")
            print("   2. Ou remover registros órfãos do Firestore")

        if error_count > 0:
            print("   3. Investigar erros de permissão ou conectividade")

        if sync_percentage == 100:
            print("   ✅ Sistema está sincronizado - nenhuma ação necessária")

        return sync_results

    except Exception as e:
        print(f"❌ Erro geral durante verificação: {e}")
        return None


if __name__ == "__main__":
    print("🔍 VERIFICAÇÃO DE SINCRONIZAÇÃO FIRESTORE <-> AUTHENTICATION")
    print("=" * 80)

    result = verify_auth_sync()

    print("\n" + "=" * 80)
    print("✅ Verificação concluída!")

    if result:
        total_synced = len(result["synced"])
        total_issues = len(result["not_in_auth"]) + len(result["auth_errors"])

        if total_issues == 0:
            print(
                f"🎉 Todos os {total_synced} usuários estão perfeitamente sincronizados!"
            )
        else:
            print(
                f"⚠️  {total_synced} usuários sincronizados, {total_issues} com problemas."
            )
    else:
        print("❌ Falha na verificação - verifique as credenciais e conectividade.")