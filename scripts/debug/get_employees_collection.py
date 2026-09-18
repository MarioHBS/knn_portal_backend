#!/usr/bin/env python3
"""
Script para investigar exclusivamente a estrutura da coleção 'employees' no Firestore.
Analisa todos os documentos, funcionários e suas estruturas para identificar discrepâncias.
"""

import sys
from pathlib import Path

from google.cloud import firestore

from src.utils import logger

# Adicionar o diretório raiz do projeto ao Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def investigate_employees_collection():
    """Investiga exclusivamente a estrutura da coleção 'employees'."""
    try:
        logger.info("🔍 Investigando estrutura da coleção 'employees'...")

        # Inicializar cliente Firestore diretamente
        db = firestore.Client()

        # Acessar a coleção 'employees'
        employees_ref = db.collection("employees")

        # Listar todos os documentos na coleção employees
        docs = employees_ref.stream()
        doc_count = 0
        employees_data = {}
        status_count = {"active": 0, "inactive": 0, "unknown": 0}
        role_count = {}

        logger.info("📋 Analisando todos os documentos da coleção 'employees'...")

        for doc in docs:
            doc_count += 1
            doc_data = doc.to_dict()

            logger.info(f"\n📄 Documento #{doc_count}: {doc.id}")

            # Extrair informações principais do funcionário
            name = doc_data.get("name", "N/A")
            email = doc_data.get("email", "N/A")
            status = doc_data.get("status", "unknown")
            role = doc_data.get("role", "N/A")
            partner_id = doc_data.get("partner_id", "N/A")
            tenant_id = doc_data.get("tenant_id", "N/A")
            created_at = doc_data.get("created_at", "N/A")
            updated_at = doc_data.get("updated_at", "N/A")

            # Contar status
            if status in status_count:
                status_count[status] += 1
            else:
                status_count["unknown"] += 1

            # Contar roles
            if role not in role_count:
                role_count[role] = 0
            role_count[role] += 1

            logger.info(f"   👤 Nome: {name}")
            logger.info(f"   📧 Email: {email}")
            logger.info(f"   📈 Status: {status}")
            logger.info(f"   🎭 Role: {role}")
            logger.info(f"   🏢 Partner ID: {partner_id}")
            logger.info(f"   🏷️  Tenant ID: {tenant_id}")

            # Armazenar dados do funcionário
            employees_data[doc.id] = {
                "name": name,
                "email": email,
                "status": status,
                "role": role,
                "partner_id": partner_id,
                "tenant_id": tenant_id,
                "created_at": created_at,
                "updated_at": updated_at,
                "all_fields": list(doc_data.keys()),
            }

            # Mostrar todos os campos disponíveis
            logger.info(
                f"   📋 Campos disponíveis: {employees_data[doc.id]['all_fields']}"
            )

            # Verificar se há campos específicos importantes
            important_fields = [
                "phone",
                "department",
                "hire_date",
                "permissions",
                "last_login",
            ]
            available_important = [
                field for field in important_fields if field in doc_data
            ]
            if available_important:
                logger.info(
                    f"   ⭐ Campos importantes presentes: {available_important}"
                )

        # Resumo final
        logger.info("\n📊 RESUMO DA INVESTIGAÇÃO:")
        logger.info(f"   📄 Total de documentos (funcionários): {doc_count}")
        logger.info(f"   ✅ Funcionários ativos: {status_count['active']}")
        logger.info(f"   ❌ Funcionários inativos: {status_count['inactive']}")
        logger.info(f"   ❓ Status desconhecido: {status_count['unknown']}")

        # Análise por role
        logger.info("\n🎭 ANÁLISE POR ROLE:")
        for role, count in role_count.items():
            logger.info(f"   {role}: {count} funcionários")

        # Análise por partner_id
        partners = {}
        for _employee_id, data in employees_data.items():
            partner = data["partner_id"]
            if partner not in partners:
                partners[partner] = 0
            partners[partner] += 1

        logger.info("\n🏢 ANÁLISE POR PARCEIRO:")
        for partner, count in partners.items():
            logger.info(f"   {partner}: {count} funcionários")

        # Análise por tenant_id
        tenants = {}
        for _employee_id, data in employees_data.items():
            tenant = data["tenant_id"]
            if tenant not in tenants:
                tenants[tenant] = 0
            tenants[tenant] += 1

        logger.info("\n🏷️  ANÁLISE POR TENANT:")
        for tenant, count in tenants.items():
            logger.info(f"   {tenant}: {count} funcionários")

        # Verificar funcionários com problemas
        logger.info("\n🔍 VERIFICANDO POSSÍVEIS PROBLEMAS:")
        problems_found = False

        for employee_id, data in employees_data.items():
            issues = []

            if data["name"] == "N/A" or not data["name"]:
                issues.append("Nome ausente")
            if data["email"] == "N/A" or not data["email"]:
                issues.append("Email ausente")
            elif "@" not in data["email"]:
                issues.append("Email inválido")
            if data["status"] == "unknown":
                issues.append("Status desconhecido")
            if data["role"] == "N/A" or not data["role"]:
                issues.append("Role ausente")
            if data["partner_id"] == "N/A" or not data["partner_id"]:
                issues.append("Partner ID ausente")
            if data["tenant_id"] == "N/A" or not data["tenant_id"]:
                issues.append("Tenant ID ausente")

            if issues:
                problems_found = True
                logger.info(f"   ⚠️  {employee_id}: {', '.join(issues)}")

        if not problems_found:
            logger.info("   ✅ Nenhum problema detectado nos funcionários!")

        logger.info("🏁 Investigação da coleção 'employees' concluída!")

        return {
            "total_documents": doc_count,
            "status_count": status_count,
            "role_count": role_count,
            "partners": partners,
            "tenants": tenants,
            "employees_data": employees_data,
        }

    except Exception as e:
        logger.error(f"❌ Erro durante investigação: {str(e)}")
        raise


if __name__ == "__main__":
    result = investigate_employees_collection()
    print("\n🎯 RESULTADO FINAL:")
    print(f"Documentos: {result['total_documents']}")
    print(f"Ativos: {result['status_count']['active']}")
    print(f"Inativos: {result['status_count']['inactive']}")
    print(f"Roles: {len(result['role_count'])}")
    print(f"Parceiros: {len(result['partners'])}")
    print(f"Tenants: {len(result['tenants'])}")
