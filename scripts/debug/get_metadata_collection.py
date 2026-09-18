#!/usr/bin/env python3
"""
Script para investigar a estrutura da coleção 'metadata' no Firestore.

Objetivos:
- Listar todos os documentos da coleção 'metadata'
- Identificar se o documento é global (ex.: 'student_info') ou por-tenant (ex.: '<tenant>_student_info')
- Detectar o esquema utilizado: novo (totals.quantity + last_updated ISO) vs legado (data.quantity + data.last_updated)
- Verificar presença de janelas (windows) e atributos complementares (roles, categories, etc.)
- Apontar inconsistências e sugerir melhorias
"""

import sys
from pathlib import Path
from typing import Any

from google.cloud import firestore

# Adicionar o diretório raiz do projeto ao Python path (antes dos imports do projeto)
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


# Import robusto do logger (fallback simples caso pacote src não seja resolvido)
try:
    from src.utils import logger
except Exception:
    import logging as _logging

    _logging.basicConfig(
        level=_logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )

    class _SimpleLogger:
        def info(self, msg):
            _logging.info(msg)

        def error(self, msg):
            _logging.error(msg)

    logger = _SimpleLogger()


LEGACY_DOC_NAMES = {
    "student_info",
    "employee_info",
    "partner_info",
    "benefit_info",
    "course_info",
}


def _classify_doc_id(doc_id: str, expected_tenant_id: str) -> dict[str, Any]:
    """Classifica o ID do documento como global ou por-tenant."""
    # Check if it's a tenant-specific document
    if doc_id.startswith(f"{expected_tenant_id}_"):
        # Extract the base name after the tenant_id and underscore
        base_name = doc_id[len(f"{expected_tenant_id}_") :]
        if base_name in LEGACY_DOC_NAMES:
            return {
                "is_tenant_specific": True,
                "tenant_id": expected_tenant_id,
                "doc_name": base_name,
            }

    # If it doesn't match the tenant-specific pattern, or base_name is not in LEGACY_DOC_NAMES
    # Consider it a global document, or a document with an unrecognized pattern
    return {
        "is_tenant_specific": False,
        "tenant_id": None,
        "doc_name": doc_id,  # Keep the full doc_id as doc_name if not recognized
    }


def _last_updated_info(doc_data: dict[str, Any]) -> dict[str, Any]:
    """Extrai informações sobre last_updated (novo esquema)."""
    lu_new = doc_data.get("last_updated")

    def _type_of(value: Any) -> str:
        if value is None:
            return "none"
        if isinstance(value, str):
            return "string"
        try:
            import datetime as _dt  # noqa: WPS433

            if isinstance(value, _dt.datetime):
                return "datetime"
        except Exception:
            pass
        return type(value).__name__

    return {
        "last_updated": lu_new,
        "source": "new" if lu_new is not None else "none",
        "type": _type_of(lu_new),
    }


def investigate_metadata_collection(tenant_id_param: str):
    """Investiga a estrutura da coleção 'metadata'."""
    try:
        logger.info("🔍 Investigando estrutura da coleção 'metadata'...")

        db = firestore.Client()
        meta_ref = db.collection("metadata")
        docs = meta_ref.stream()

        doc_count = 0
        summary = {
            "total_docs": 0,
            "by_type": {},  # Mantido para compatibilidade com logs existentes, mas será menos detalhado
            "grouped_by_tenant_and_type": {},  # Nova estrutura para agrupamento
            "tenant_specific_count": 0,
            "global_count": 0,
            "schema": {
                "has_total": 0,  # possui 'total' no nível raiz
                "legacy_data": 0,  # possui 'data.quantity'
                "both": 0,
                "none": 0,
            },
            "windows_present": 0,
            "issues": [],
            "attributes": {
                "roles_docs": 0,
                "categories_docs": 0,
                "role_distribution_docs": 0,
            },
            "docs": {},
        }

        logger.info("📋 Analisando todos os documentos da coleção 'metadata'...")

        for doc in docs:
            doc_count += 1
            doc_data: dict[str, Any] = doc.to_dict() or {}
            doc_id = doc.id
            issues = []  # Inicializa issues para cada documento

            classification = _classify_doc_id(doc_id, tenant_id_param)
            is_tenant = classification["is_tenant_specific"]
            doc_name = classification["doc_name"]
            tenant_id = classification["tenant_id"]
            print(
                f"DEBUG: After classification: doc_id={doc_id}, is_tenant={is_tenant}, doc_name={doc_name}, tenant_id={tenant_id}"
            )

            # Agrupamento por tenant e tipo
            group_key = tenant_id if is_tenant else "GLOBAL"
            summary["grouped_by_tenant_and_type"].setdefault(group_key, {})
            summary["grouped_by_tenant_and_type"][group_key].setdefault(doc_name, 0)
            summary["grouped_by_tenant_and_type"][group_key][doc_name] += 1

            # Campos obrigatórios
            total = doc_data.get("total")
            has_total = total is not None and isinstance(total, int | float)
            tenant_id_from_doc = doc_data.get("tenant_id")
            lu_info = _last_updated_info(doc_data)

            # Esquemas
            data_field = doc_data.get("data") or {}
            data_quantity = data_field.get("quantity")
            has_legacy = data_quantity is not None

            if has_total and has_legacy:
                summary["schema"]["both"] += 1
            elif has_total:
                summary["schema"]["has_total"] += 1
            elif has_legacy:
                summary["schema"]["legacy_data"] += 1
            else:
                summary["schema"]["none"] += 1

            # Validação de tenant_id
            if tenant_id_from_doc is None:
                issues.append("Campo 'tenant_id' ausente no documento")
            elif tenant_id_from_doc != tenant_id:
                issues.append(
                    f"Inconsistência de tenant_id: chave='{tenant_id}', documento='{tenant_id_from_doc}'"
                )

            # windows
            windows = doc_data.get("windows") or {}
            if isinstance(windows, dict) and windows:
                summary["windows_present"] += 1

            # atributos complementares
            roles = doc_data.get("roles") or data_field.get("roles") or []
            categories = (
                doc_data.get("categories") or data_field.get("categories") or []
            )
            role_dist = (
                doc_data.get("role_distribution")
                or data_field.get("role_distribution")
                or {}
            )

            if roles:
                summary["attributes"]["roles_docs"] += 1
            if categories:
                summary["attributes"]["categories_docs"] += 1
            if role_dist:
                summary["attributes"]["role_distribution_docs"] += 1

            # last_updated
            lu_info = _last_updated_info(doc_data)

            # contagem por tipo
            summary["by_type"].setdefault(doc_name, 0)
            summary["by_type"][doc_name] += 1

            if is_tenant:
                summary["tenant_specific_count"] += 1
            else:
                summary["global_count"] += 1

            # Detecção de problemas
            issues = []
            if not has_total and not has_legacy:
                issues.append(
                    "Documento sem contador detectado (nem total nem data.quantity)"
                )
            if has_legacy and not has_total:
                issues.append(
                    "Documento em esquema LEGADO; sugerido migrar para total + last_updated ISO"
                )
            if lu_info["source"] == "none":
                issues.append("Campo last_updated ausente")
            elif lu_info["type"] not in {"string", "datetime"}:
                issues.append(f"Formato de last_updated incomum: {lu_info['type']}")
            if doc_name not in LEGACY_DOC_NAMES:
                issues.append(
                    "doc_name não reconhecido; validar convenção de nomes e suporte em MetricsService"
                )

            # Registrar dados detalhados
            summary["docs"][doc_id] = {
                "tenant_id": tenant_id,
                "doc_name": doc_name,
                "is_tenant_specific": is_tenant,
                "schema": "new" if has_total else ("legacy" if has_legacy else "none"),
                "total": total,
                "data_quantity": data_quantity,
                "windows_keys": list(windows.keys())
                if isinstance(windows, dict)
                else [],
                "last_updated": lu_info,
                "roles_count": len(roles) if isinstance(roles, list) else 0,
                "categories_count": len(categories)
                if isinstance(categories, list)
                else 0,
                "role_distribution_keys": list(role_dist.keys())
                if isinstance(role_dist, dict)
                else [],
                "all_fields": list(doc_data.keys()),
                "issues": issues,
            }

            # Log amigável
            logger.info(
                {
                    "event": "📄 Documento metadata",
                    "id": doc_id,
                    "tenant_id": tenant_id or "GLOBAL",
                    "name": doc_name,
                    "schema": summary["docs"][doc_id]["schema"],
                    "total": total,
                    "data_quantity": data_quantity,
                    "windows": summary["docs"][doc_id]["windows_keys"],
                    "last_updated": summary["docs"][doc_id]["last_updated"],
                    "attrs": {
                        "roles_count": summary["docs"][doc_id]["roles_count"],
                        "categories_count": summary["docs"][doc_id]["categories_count"],
                    },
                    "issues": issues,
                }
            )

            for issue in issues:
                summary["issues"].append({"doc_id": doc_id, "issue": issue})

        # Resumo final
        summary["total_docs"] = doc_count

        logger.info("\n📊 RESUMO DA INVESTIGAÇÃO METADATA:")
        logger.info(
            {
                "event": "Resumo",
                "total_docs": summary["total_docs"],
                "global_docs": summary["global_count"],
                "tenant_docs": summary["tenant_specific_count"],
                "by_type": summary["by_type"],
                "grouped_by_tenant_and_type": summary[
                    "grouped_by_tenant_and_type"
                ],  # Adicionado ao log
                "schema": summary["schema"],
                "windows_present": summary["windows_present"],
                "attrs": summary["attributes"],
                "issues_count": len(summary["issues"]),
            }
        )

        # Recomendações com base na análise
        recommendations = []

        if summary["schema"]["legacy_data"] > 0:
            recommendations.append(
                "Migrar documentos LEGADOS para o novo esquema (total + last_updated ISO)."
            )
            recommendations.append(
                "Criar script de backfill: copiar data.quantity -> total e data.last_updated -> last_updated."
            )

        if summary["schema"]["none"] > 0:
            recommendations.append(
                "Inicializar documentos sem contadores com total = 0 e last_updated = now ISO."
            )

        if summary["global_count"] > 0 and summary["tenant_specific_count"] == 0:
            recommendations.append(
                "Padronizar uso por-tenant: utilizar IDs <tenant_id>_<doc_name> para suportar multi-tenancy."
            )

        if summary["windows_present"] == 0:
            recommendations.append(
                "Adicionar janelas (windows: 24h, 7d, 30d) quando possível para análises temporais."
            )

        # Observação importante sobre leitura dos contadores
        recommendations.append(
            "Ajustar MetricsService.get_aggregated_counters para fazer fallback em data.quantity (legado), caso não exista total."
        )

        logger.info({"event": "💡 Recomendações", "items": recommendations})

        return {"summary": summary, "recommendations": recommendations}

    except Exception as e:
        logger.error(f"❌ Erro durante investigação de metadata: {str(e)}")
        raise


if __name__ == "__main__":
    # tenant_id pode ser passado como argumento de linha de comando
    # Ex: python investigate_metadata_collection.py --tenant_id knn-dev-tenant
    default_tenant_id = "knn-dev-tenant"
    tenant_id_arg = next(
        (arg.split("=")[1] for arg in sys.argv if arg.startswith("--tenant_id=")),
        default_tenant_id,
    )

    result = investigate_metadata_collection(tenant_id_arg)
    summary = result["summary"]
    recs = result["recommendations"]

    print("\n🎯 RESULTADO FINAL METADATA:")
    print(f"Documentos: {summary['total_docs']}")
    print(f"Docs globais: {summary['global_count']}")
    print(f"Docs por-tenant: {summary['tenant_specific_count']}")
    print("Tipos:", summary["by_type"])

    # Mapeamento de nomes de documentos para português
    doc_name_mapping = {
        "benefit_info": "Benefício",
        "employee_info": "Funcionário",
        "partner_info": "Parceiro",
        "student_info": "Aluno",
        # Adicione outros mapeamentos conforme necessário
    }

    print("\nAgrupado por Tenant e Tipo:")  # Novo cabeçalho
    for tenant, types in summary["grouped_by_tenant_and_type"].items():
        print(f" - {tenant}:")
        for doc_type in types:
            # Encontrar o documento correspondente para obter last_updated e total
            # Isso assume que há apenas um documento por doc_type para um dado tenant
            # ou que queremos o primeiro encontrado.
            found_doc_id = None
            for doc_id, doc_details in summary["docs"].items():
                if (
                    doc_details["tenant_id"] == tenant
                    and doc_details["doc_name"] == doc_type
                    or tenant == "GLOBAL"
                    and not doc_details["is_tenant_specific"]
                    and doc_details["doc_name"] == doc_type
                ):
                    found_doc_id = doc_id
                    break

            if found_doc_id:
                doc_info = summary["docs"][found_doc_id]
                translated_doc_name = doc_name_mapping.get(doc_type, doc_type)
                last_updated_value = doc_info["last_updated"]["last_updated"]
                total_value = doc_info["total"]
                print(
                    f"  * {translated_doc_name} {{last_updated: {last_updated_value}, total: {total_value}}}"
                )
            else:
                translated_doc_name = doc_name_mapping.get(doc_type, doc_type)
                print(f"  * {translated_doc_name} {{last_updated: N/A, total: N/A}}")
    print("Esquema:", summary["schema"])
    print(f"Windows presentes em {summary['windows_present']} docs")
    print(f"Issues: {len(summary['issues'])}")
    print("\n💡 Recomendações:")
    for r in recs:
        print(f" - {r}")
