#!/usr/bin/env python3
"""
Script para investigar exclusivamente a estrutura da coleção 'students' no Firestore.
Analisa todos os documentos, estudantes e suas estruturas para identificar discrepâncias.
"""

import sys
from datetime import UTC, datetime
from pathlib import Path

from google.cloud import firestore

from src.utils import logger

# Adicionar o diretório raiz do projeto ao Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def investigate_students_collection():
    """Investiga exclusivamente a estrutura da coleção 'students'."""
    try:
        logger.info("🔍 Investigando estrutura da coleção 'students'...")

        # Inicializar cliente Firestore diretamente
        db = firestore.Client()

        # Acessar a coleção 'students'
        students_ref = db.collection("students")

        # Listar todos os documentos na coleção students
        docs = students_ref.stream()
        doc_count = 0
        students_data = {}
        status_count = {"active": 0, "inactive": 0, "unknown": 0}
        course_count = {}
        age_groups = {"menor_idade": 0, "maior_idade": 0, "sem_idade": 0}

        logger.info("📋 Analisando todos os documentos da coleção 'students'...")

        for doc in docs:
            doc_count += 1
            doc_data = doc.to_dict()

            logger.info(f"\n📄 Documento #{doc_count}: {doc.id}")

            # Extrair informações principais do estudante
            name = doc_data.get("name", "N/A")
            email = doc_data.get("contact", {}).get("email", "N/A")
            status = doc_data.get("status", "unknown")
            curso = doc_data.get("book", "N/A")
            # CPF não existe para aluno, removido da investigação
            data_nascimento = doc_data.get("data_nascimento", "N/A")

            guardian_data = doc_data.get("guardian")
            if guardian_data is None:
                nome_responsavel = None
                email_responsavel = None
            else:
                nome_responsavel = guardian_data.get("name", "N/A")
                email_responsavel = guardian_data.get("email", "N/A")
            telefone = doc_data.get("telefone", "N/A")
            cep = doc_data.get("cep", "N/A")
            tenant_id = doc_data.get("tenant_id", "N/A")
            created_at = doc_data.get("created_at", "N/A")
            updated_at = doc_data.get("updated_at", "N/A")
            active_until = doc_data.get("active_until", None)

            # Contar status
            # Lógica de status ativo/inativo baseada em active_until
            if isinstance(active_until, datetime):
                if datetime.now(UTC) <= active_until:
                    status_count["active"] += 1
                    status = "active"
                else:
                    status_count["inactive"] += 1
                    status = "inactive"
            else:
                status_count["unknown"] += 1
                status = "unknown"

            # Contar cursos
            if curso not in course_count:
                course_count[curso] = 0
            course_count[curso] += 1

            # Verificar idade (se menor de idade tem responsável)
            if nome_responsavel != "N/A" and nome_responsavel:
                age_groups["menor_idade"] += 1
            else:
                age_groups["maior_idade"] += 1

            logger.info(f"   👤 Nome: {name}")
            logger.info(f"   📧 Email: {email}")
            logger.info(f"   📈 Status: {status}")
            logger.info(f"   🎓 Curso: {curso}")
            # CPF removido da exibição
            logger.info(f"   📅 Data Nascimento: {data_nascimento}")
            if nome_responsavel is not None:
                logger.info(f"   👨‍👩‍👧‍👦 Responsável: {nome_responsavel}")
            logger.info(f"   📞 Telefone: {telefone}")
            logger.info(f"   📮 CEP: {cep}")
            logger.info(f"   🏷️  Tenant ID: {tenant_id}")

            # Armazenar dados do estudante
            students_data[doc.id] = {
                "name": name,
                "email": email,
                "status": status,
                "curso": curso,
                # "cpf": cpf, # CPF removido do armazenamento
                "data_nascimento": data_nascimento,
                "nome_responsavel": nome_responsavel,
                "email_responsavel": email_responsavel,  # Adicionado
                "telefone": telefone,
                "cep": cep,
                "tenant_id": tenant_id,
                "created_at": created_at,
                "updated_at": updated_at,
                "active_until": active_until,
                "all_fields": list(doc_data.keys()),
            }

            # Mostrar todos os campos disponíveis
            logger.info(
                f"   📋 Campos disponíveis: {students_data[doc.id]['all_fields']}"
            )

            # Verificar se há campos específicos importantes
            important_fields = [
                "endereco",
                "cidade",
                "estado",
                "matricula",
                "periodo",
                "turma",
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
        logger.info(f"   📄 Total de documentos (estudantes): {doc_count}")
        logger.info(f"   ✅ Estudantes ativos: {status_count['active']}")
        logger.info(f"   ❌ Estudantes inativos: {status_count['inactive']}")
        logger.info(f"   ❓ Status desconhecido: {status_count['unknown']}")

        # Análise por curso
        logger.info("\n🎓 ANÁLISE POR CURSO:")
        for curso, count in course_count.items():
            logger.info(f"   {curso}: {count} estudantes")

        # Análise por faixa etária
        logger.info("\n👶 ANÁLISE POR FAIXA ETÁRIA:")
        logger.info(f"   Menores de idade: {age_groups['menor_idade']}")
        logger.info(f"   Maiores de idade: {age_groups['maior_idade']}")
        # Removido "Sem data de nascimento" pois a lógica agora é baseada em 'guardian'

        # Análise por tenant_id
        tenants = {}
        for _student_id, data in students_data.items():
            tenant = data["tenant_id"]
            if tenant not in tenants:
                tenants[tenant] = 0
            tenants[tenant] += 1

        logger.info("\n🏷️  ANÁLISE POR TENANT:")
        for tenant, count in tenants.items():
            logger.info(f"   {tenant}: {count} estudantes")

        # Verificar estudantes com problemas
        logger.info("\n🔍 VERIFICANDO POSSÍVEIS PROBLEMAS:")
        problems_found = False

        for student_id, data in students_data.items():
            issues = []

            if data["name"] is None or data["name"] == "N/A" or not data["name"]:
                issues.append("Nome ausente")
            if data["email"] is None or data["email"] == "N/A" or not data["email"]:
                # Se o email estiver ausente, mas tiver responsável, não é um problema crítico
                if data["email_responsavel"] is None or not data["email_responsavel"]:
                    issues.append("Email ausente")
            elif data["email"] is not None and "@" not in data["email"]:
                issues.append("Email inválido")
            if data["status"] == "unknown":
                issues.append("Status desconhecido (active_until inválido)")
            if data["curso"] is None or data["curso"] == "N/A" or not data["curso"]:
                issues.append("Curso ausente")
            # CPF removido da verificação de problemas
            if (
                data["tenant_id"] is None
                or data["tenant_id"] == "N/A"
                or not data["tenant_id"]
            ):
                issues.append("Tenant ID ausente")

            # Verificar regra de negócio: menor de idade deve ter responsável
            # A lógica de menor de idade agora é baseada diretamente em 'nome_responsavel'
            if (data["nome_responsavel"] is not None and data["nome_responsavel"]) and (
                data["email"] is None or not data["email"]
            ):
                issues.append(
                    "Menor de idade com responsável, mas sem email de contato"
                )

            # Verificar formato do CEP brasileiro
            if (
                data["cep"] != "N/A"
                and data["cep"]
                and not (len(data["cep"]) == 9 and "-" in data["cep"])
            ):
                issues.append("CEP em formato inválido")

            if issues:
                problems_found = True
                logger.info(f"   ⚠️  {student_id}: {', '.join(issues)}")

        if not problems_found:
            logger.info("   ✅ Nenhum problema detectado nos estudantes!")

        logger.info("🏁 Investigação da coleção 'students' concluída!")

        return {
            "total_documents": doc_count,
            "status_count": status_count,
            "course_count": course_count,
            "age_groups": age_groups,
            "tenants": tenants,
            "students_data": students_data,
        }

    except Exception as e:
        logger.error(f"❌ Erro durante investigação: {str(e)}")
        raise


if __name__ == "__main__":
    result = investigate_students_collection()
    print("\n🎯 RESULTADO FINAL:")
    print(f"Documentos: {result['total_documents']}")
    print(f"Ativos: {result['status_count']['active']}")
    print(f"Inativos: {result['status_count']['inactive']}")
    print(f"Cursos: {len(result['course_count'])}")
    print(f"Menores de idade: {result['age_groups']['menor_idade']}")
    print(f"Maiores de idade: {result['age_groups']['maior_idade']}")
    print(f"Tenants: {len(result['tenants'])}")
