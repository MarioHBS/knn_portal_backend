#!/usr/bin/env python3
"""
Script para criar entidades temporárias de teste no Firebase.
Cria um Aluno, um Funcionário e um Parceiro com credenciais de autenticação.
Senha padrão: Tp654321
"""

import json
import os
from datetime import UTC, datetime
from typing import Any

import firebase_admin
from firebase_admin import auth, credentials, firestore

# Configurações
FIREBASE_CREDENTIALS_PATH = "credentials/default-service-account-key.json"
FIREBASE_PROJECT_ID = "knn-benefits"
TEST_PASSWORD = "Tp654321"
TENANT_ID = "knn-dev-tenant"

# Dados das entidades temporárias
TEST_ENTITIES = {
    "student": {
        "email": "aluno.teste@journeyclub.com.br",
        "display_name": "João Silva Santos",
        "role": "student",
        "data": {
            "nome_completo": "João Silva Santos",
            "email": "aluno.teste@journeyclub.com.br",
            "telefone": "(11) 99999-1111",
            "cep": "01310-100",
            "endereco": "Av. Paulista, 1000",
            "cidade": "São Paulo",
            "estado": "SP",
            "curso": "Engenharia de Software",
            "periodo": "Noturno",
            "semestre": 4,
            "status": "ativo",
            "data_nascimento": "2000-05-15",
            "cpf": "123.456.789-00",
            "rg": "12.345.678-9",
            "nome_responsavel": "",
            "tenant_id": TENANT_ID,
            "active": True,
        },
    },
    "employee": {
        "email": "funcionario.teste@journeyclub.com.br",
        "display_name": "Maria Oliveira Costa",
        "role": "employee",
        "data": {
            "nome_completo": "Maria Oliveira Costa",
            "email": "funcionario.teste@journeyclub.com.br",
            "telefone": "(11) 99999-2222",
            "cep": "04038-001",
            "endereco": "Rua Vergueiro, 500",
            "cidade": "São Paulo",
            "estado": "SP",
            "cargo": "Coordenadora Acadêmica",
            "departamento": "Educação",
            "salario": 8500.00,
            "data_admissao": "2022-03-01",
            "status": "ativo",
            "cpf": "987.654.321-00",
            "rg": "98.765.432-1",
            "tenant_id": TENANT_ID,
            "active": True,
        },
    },
    "partner": {
        "email": "parceiro.teste@journeyclub.com.br",
        "display_name": "TechSolutions Ltda",
        "role": "partner",
        "data": {
            "nome_empresa": "TechSolutions Ltda",
            "email": "parceiro.teste@journeyclub.com.br",
            "telefone": "(11) 99999-3333",
            "cnpj": "12.345.678/0001-90",
            "cep": "01414-001",
            "endereco": "Rua Augusta, 1000",
            "cidade": "São Paulo",
            "estado": "SP",
            "categoria": "Tecnologia",
            "descricao": "Empresa especializada em soluções tecnológicas para educação",
            "website": "https://techsolutions.com.br",
            "rating": 4.5,
            "total_beneficios": 25,
            "status": "ativo",
            "tenant_id": TENANT_ID,
            "active": True,
        },
    },
}


def initialize_firebase():
    """Inicializa o Firebase Admin SDK"""
    try:
        # Tenta usar credenciais do arquivo primeiro
        if os.path.exists(FIREBASE_CREDENTIALS_PATH):
            cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
            app = firebase_admin.initialize_app(
                cred, {"projectId": FIREBASE_PROJECT_ID}
            )
            print(
                f"✅ Firebase inicializado com credenciais do arquivo: {FIREBASE_CREDENTIALS_PATH}"
            )
        else:
            # Tenta usar credenciais padrão (variável de ambiente ou gcloud)
            try:
                cred = credentials.ApplicationDefault()
                app = firebase_admin.initialize_app(
                    cred, {"projectId": FIREBASE_PROJECT_ID}
                )
                print("✅ Firebase inicializado com credenciais padrão do sistema")
            except Exception as default_error:
                print(f"❌ Erro com credenciais padrão: {str(default_error)}")
                print(
                    f"💡 Dica: Configure a variável GOOGLE_APPLICATION_CREDENTIALS ou coloque o arquivo em: {FIREBASE_CREDENTIALS_PATH}"
                )
                raise FileNotFoundError(
                    f"Credenciais não encontradas. Arquivo: {FIREBASE_CREDENTIALS_PATH} não existe e credenciais padrão falharam."
                ) from default_error

        print(
            f"✅ Firebase inicializado com sucesso para o projeto: {FIREBASE_PROJECT_ID}"
        )
        return app

    except Exception as e:
        print(f"❌ Erro ao inicializar Firebase: {str(e)}")
        raise


def generate_entity_id(role: str) -> str:
    """Gera ID único para a entidade baseado no padrão do sistema."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    role_prefixes = {
        "student": "STD_TEST",
        "employee": "EMP_TEST",
        "partner": "PTR_TEST"
    }
    prefix = role_prefixes.get(role, "USR_TEST")
    return f"{prefix}_{timestamp}"


def create_firebase_user(
    entity_type: str, entity_data: dict[str, Any], firebase_available: bool = True
) -> dict[str, Any]:
    """Cria usuário no Firebase Authentication."""
    try:
        # Verificar se usuário já existe
        try:
            existing_user = auth.get_user_by_email(entity_data["email"])
            print(f"ℹ️ Usuário {entity_type} já existe: {existing_user.uid}")
            user = existing_user
        except auth.UserNotFoundError:
            # Criar novo usuário
            user = auth.create_user(
                email=entity_data["email"],
                password=TEST_PASSWORD,
                display_name=entity_data["display_name"],
                email_verified=True,
            )
            print(f"✅ Usuário {entity_type} criado: {user.uid}")

        # Definir custom claims
        custom_claims = {
            "role": entity_data["role"],
            "tenant": TENANT_ID,
            "entity_type": entity_type,
            "created_by": "temp_test_script",
            "is_temp": True,
        }

        # Aplicar custom claims
        auth.set_custom_user_claims(user.uid, custom_claims)
        print(f"✅ Custom claims aplicadas para {entity_type}")

        # Criar token personalizado
        custom_token = auth.create_custom_token(user.uid, custom_claims)
        if isinstance(custom_token, bytes):
            custom_token = custom_token.decode("utf-8")

        return {
            "uid": user.uid,
            "email": entity_data["email"],
            "role": entity_data["role"],
            "custom_token": custom_token,
            "custom_claims": custom_claims,
        }

    except Exception as e:
        print(f"❌ Erro ao criar usuário {entity_type}: {e}")
        raise


def create_firestore_document(
    entity_type: str,
    entity_id: str,
    entity_data: dict[str, Any],
    user_info: dict[str, Any],
):
    """Cria documento no Firestore."""
    try:
        db = firestore.client()

        # Preparar dados do documento
        doc_data = entity_data["data"].copy()
        doc_data.update(
            {
                "id": entity_id,
                "tenant_id": TENANT_ID,
                "firebase_uid": user_info["uid"],
                "created_at": datetime.now(UTC),
                "updated_at": datetime.now(UTC),
                "is_temp": True,
                "created_by": "temp_test_script",
            }
        )

        # Determinar coleção
        collection_name = (
            f"{entity_type}s" if entity_type != "employee" else "employees"
        )

        # Criar documento
        doc_ref = db.collection(collection_name).document(entity_id)
        doc_ref.set(doc_data)

        print(f"✅ Documento {entity_type} criado no Firestore: {entity_id}")
        return doc_data

    except Exception as e:
        print(f"❌ Erro ao criar documento {entity_type}: {e}")
        raise


def create_test_entities():
    """Cria todas as entidades temporárias de teste."""
    print("🚀 Criando entidades temporárias de teste...\n")

    try:
        # Verifica se pode conectar ao Firebase
        firebase_available = False
        try:
            app = initialize_firebase()
            firebase_available = True
        except Exception as firebase_error:
            print(f"⚠️  Firebase não disponível: {str(firebase_error)}")
            print(
                "📝 Criando dados de teste em modo simulação (apenas estrutura local)"
            )

        created_entities = {}

        # Criar cada entidade
        for entity_type, entity_data in TEST_ENTITIES.items():
            print(f"\n📝 Criando {entity_type}...")

            # Gerar ID único
            entity_id = generate_entity_id(entity_data["role"])

            if firebase_available:
                # Criar usuário no Firebase Auth
                user_info = create_firebase_user(entity_type, entity_data)

                # Criar documento no Firestore
                doc_data = create_firestore_document(
                    entity_type, entity_id, entity_data, user_info
                )

                # Armazenar informações
                created_entities[entity_type] = {
                    "entity_id": entity_id,
                    "firebase_uid": user_info["uid"],
                    "email": entity_data["email"],
                    "password": TEST_PASSWORD,
                    "role": entity_data["role"],
                    "custom_token": user_info["custom_token"],
                    "firestore_data": doc_data,
                }
            else:
                # Modo simulação - apenas estrutura local
                created_entities[entity_type] = {
                    "entity_id": entity_id,
                    "firebase_uid": f"simulated_uid_{entity_id}",
                    "email": entity_data["email"],
                    "password": TEST_PASSWORD,
                    "role": entity_data["role"],
                    "custom_token": f"simulated_token_{entity_id}",
                    "firestore_data": {
                        **entity_data["data"],
                        "id": entity_id,
                        "tenant_id": TENANT_ID,
                        "firebase_uid": f"simulated_uid_{entity_id}",
                        "created_at": datetime.now(UTC).isoformat(),
                        "updated_at": datetime.now(UTC).isoformat(),
                        "is_temp": True,
                        "created_by": "temp_test_script",
                        "simulation_mode": True,
                    },
                }

        # Salvar informações em arquivo
        output_file = "credentials/temp_test_entities.json"
        os.makedirs("credentials", exist_ok=True)

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(created_entities, f, indent=2, ensure_ascii=False, default=str)

        print(f"\n💾 Informações salvas em: {output_file}")

        # Exibir resumo
        if firebase_available:
            print("\n🎯 Entidades temporárias criadas com sucesso no Firebase!")
        else:
            print("\n🎯 Estrutura de dados de teste criada em modo simulação!")
            print(
                "💡 Para conectar ao Firebase, configure as credenciais conforme o README"
            )

        print("\n📋 Resumo das credenciais:")

        for entity_type, info in created_entities.items():
            print(f"\n{entity_type.upper()}:")
            print(f"   - Email: {info['email']}")
            print(f"   - Senha: {info['password']}")
            print(f"   - Role: {info['role']}")
            print(f"   - ID Firestore: {info['entity_id']}")
            print(f"   - UID Firebase: {info['firebase_uid']}")
            if firebase_available:
                print(
                    f"   - Token (primeiros 50 chars): {info['custom_token'][:50]}..."
                )
            else:
                print(f"   - Token: {info['custom_token']} (simulado)")

        print(f"\n⚠️ IMPORTANTE: Todas as entidades usam a senha: {TEST_PASSWORD}")
        if firebase_available:
            print("⚠️ Estas são entidades temporárias para teste - remova após uso!")
        else:
            print(
                "⚠️ Dados criados em modo simulação - configure Firebase para uso real!"
            )

        return created_entities

    except Exception as e:
        print(f"❌ Erro geral: {e}")
        import traceback

        print(f"Stack trace: {traceback.format_exc()}")
        return None


if __name__ == "__main__":
    create_test_entities()
