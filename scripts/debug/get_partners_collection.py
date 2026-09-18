#!/usr/bin/env python3
"""
Script para investigar exclusivamente a estrutura da coleção 'partners' no Firestore.
Analisa todos os documentos, parceiros e suas estruturas para identificar discrepâncias.

Versão melhorada que usa os campos corretos (trade_name, active) e PartnerDTO.
"""

import sys
from pathlib import Path
from typing import Any

from google.cloud import firestore

# Adicionar o diretório raiz do projeto ao Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.models.partner import PartnerFirestoreDTO  # noqa: E402
from src.utils import logger  # noqa: E402


def investigate_partners_collection():
    """Investiga exclusivamente a estrutura da coleção 'partners'."""
    try:
        logger.info(
            "🔍 Investigando estrutura da coleção 'partners' (versão melhorada)..."
        )

        # Inicializar cliente Firestore diretamente
        db = firestore.Client()

        # Acessar a coleção 'partners'
        partners_ref = db.collection("partners")

        # Listar todos os documentos na coleção partners
        docs = partners_ref.stream()
        doc_count = 0
        partners_data = {}
        active_count = {"true": 0, "false": 0, "missing": 0, "other": 0}
        conversion_stats = {"success": 0, "failed": 0}

        logger.info("📋 Analisando todos os documentos da coleção 'partners'...")

        for doc in docs:
            doc_count += 1
            doc_data = doc.to_dict()

            logger.info(f"\n📄 Documento #{doc_count}: {doc.id}")

            # Extrair informações usando campos corretos
            trade_name = doc_data.get("trade_name", "N/A")
            active = doc_data.get("active")
            category = doc_data.get("category", "N/A")
            tenant_id = doc_data.get("tenant_id", "N/A")
            created_at = doc_data.get("created_at", "N/A")
            updated_at = doc_data.get("updated_at", "N/A")

            # Analisar campo 'active' detalhadamente
            active_status = _analyze_active_field(active, active_count)

            logger.info(f"   📊 Nome comercial: {trade_name}")
            logger.info(
                f"   📈 Status ativo: {active} ({type(active).__name__}) -> {active_status}"
            )
            logger.info(f"   🏷️  Categoria: {category}")
            logger.info(f"   🏢 Tenant ID: {tenant_id}")

            # Testar conversão com PartnerDTO
            dto_result = _test_dto_conversion(doc_data, doc.id)
            if dto_result["success"]:
                conversion_stats["success"] += 1
                logger.info("   ✅ Conversão PartnerDTO: Sucesso")
            else:
                conversion_stats["failed"] += 1
                logger.info(f"   ❌ Conversão PartnerDTO: {dto_result['error']}")

            # Armazenar dados do parceiro
            partners_data[doc.id] = {
                "trade_name": trade_name,
                "active": active,
                "active_type": type(active).__name__,
                "active_status": active_status,
                "category": category,
                "tenant_id": tenant_id,
                "created_at": created_at,
                "updated_at": updated_at,
                "all_fields": list(doc_data.keys()),
                "dto_conversion": dto_result["success"],
            }

            # Mostrar todos os campos disponíveis
            logger.info(
                f"   📋 Campos disponíveis ({len(doc_data)}): {list(doc_data.keys())}"
            )

            # Verificar campos importantes do modelo Partner
            required_fields = [
                "id",
                "trade_name",
                "tenant_id",
                "cnpj",
                "category",
                "active",
            ]
            missing_required = [
                field for field in required_fields if field not in doc_data
            ]
            if missing_required:
                logger.info(f"   ⚠️  Campos obrigatórios ausentes: {missing_required}")

            # Verificar estruturas complexas
            complex_fields = [
                "address",
                "contact",
                "social_networks",
                "geolocation",
                "maps",
            ]
            available_complex = [field for field in complex_fields if field in doc_data]
            if available_complex:
                logger.info(f"   🏗️  Estruturas complexas: {available_complex}")

        # Resumo final detalhado
        logger.info("\n📊 RESUMO DA INVESTIGAÇÃO (MELHORADO):")
        logger.info(f"   📄 Total de documentos (parceiros): {doc_count}")
        logger.info(f"   ✅ Campo 'active' = True: {active_count['true']}")
        logger.info(f"   ❌ Campo 'active' = False: {active_count['false']}")
        logger.info(f"   ❓ Campo 'active' ausente: {active_count['missing']}")
        logger.info(f"   🔄 Campo 'active' outros valores: {active_count['other']}")

        # Estatísticas de conversão DTO
        logger.info("\n🔄 CONVERSÃO PartnerDTO:")
        logger.info(f"   ✅ Conversões bem-sucedidas: {conversion_stats['success']}")
        logger.info(f"   ❌ Conversões falharam: {conversion_stats['failed']}")

        # Análise por categoria
        categories = {}
        for _partner_id, data in partners_data.items():
            category = data["category"]
            if category not in categories:
                categories[category] = 0
            categories[category] += 1

        logger.info("\n📋 ANÁLISE POR CATEGORIA:")
        for category, count in categories.items():
            logger.info(f"   {category}: {count} parceiros")

        # Análise por tenant_id
        tenants = {}
        for _partner_id, data in partners_data.items():
            tenant = data["tenant_id"]
            if tenant not in tenants:
                tenants[tenant] = 0
            tenants[tenant] += 1

        logger.info("\n🏢 ANÁLISE POR TENANT:")
        for tenant, count in tenants.items():
            logger.info(f"   {tenant}: {count} parceiros")

        # Análise de parceiros que seriam retornados pelo endpoint
        endpoint_eligible = [
            pid
            for pid, data in partners_data.items()
            if data["active"] is True and data["tenant_id"] != "N/A"
        ]

        logger.info("\n🎯 ANÁLISE DO ENDPOINT /student/partners:")
        logger.info(
            f"   📊 Parceiros elegíveis (active=True): {len(endpoint_eligible)}"
        )
        logger.info(f"   📊 Total na coleção: {doc_count}")
        logger.info(f"   📊 Diferença: {doc_count - len(endpoint_eligible)}")

        if endpoint_eligible:
            logger.info("   ✅ Parceiros que seriam retornados:")
            for pid in endpoint_eligible:
                data = partners_data[pid]
                logger.info(f"      - {pid}: {data['trade_name']} ({data['category']})")

        # Verificar parceiros com problemas
        logger.info("\n🔍 VERIFICANDO POSSÍVEIS PROBLEMAS:")
        problems_found = False

        for partner_id, data in partners_data.items():
            issues = []

            if data["trade_name"] == "N/A" or not data["trade_name"]:
                issues.append("Nome comercial ausente")
            if data["active"] is None:
                issues.append("Campo 'active' ausente")
            elif data["active"] is not True and data["active"] is not False:
                issues.append(f"Campo 'active' com valor inválido: {data['active']}")
            if data["category"] == "N/A" or not data["category"]:
                issues.append("Categoria ausente")
            if data["tenant_id"] == "N/A" or not data["tenant_id"]:
                issues.append("Tenant ID ausente")
            if not data["dto_conversion"]:
                issues.append("Falha na conversão DTO")

            if issues:
                problems_found = True
                logger.info(f"   ⚠️  {partner_id}: {', '.join(issues)}")

        if not problems_found:
            logger.info("   ✅ Nenhum problema detectado nos parceiros!")

        logger.info("🏁 Investigação da coleção 'partners' concluída!")

        return {
            "total_documents": doc_count,
            "active_count": active_count,
            "conversion_stats": conversion_stats,
            "categories": categories,
            "tenants": tenants,
            "partners_data": partners_data,
            "endpoint_eligible_count": len(endpoint_eligible),
            "endpoint_eligible_ids": endpoint_eligible,
        }

    except Exception as e:
        logger.error(f"❌ Erro durante investigação: {str(e)}")
        raise


def _analyze_active_field(active_value: Any, active_count: dict[str, int]) -> str:
    """
    Analisa o campo 'active' e categoriza seu valor.

    Args:
        active_value: Valor do campo 'active'
        active_count: Dicionário para contagem de tipos

    Returns:
        str: Descrição do status
    """
    if active_value is None:
        active_count["missing"] += 1
        return "AUSENTE"
    elif active_value is True:
        active_count["true"] += 1
        return "ATIVO"
    elif active_value is False:
        active_count["false"] += 1
        return "INATIVO"
    else:
        active_count["other"] += 1
        return f"INVÁLIDO ({active_value})"


def _test_dto_conversion(doc_data: dict[str, Any], doc_id: str) -> dict[str, Any]:
    """
    Testa a conversão do documento usando PartnerDTO.

    Args:
        doc_data: Dados do documento Firestore
        doc_id: ID do documento

    Returns:
        dict: Resultado do teste com sucesso/erro
    """
    try:
        # Tentar conversão com PartnerDTO (passando doc_id como parâmetro)
        partner_data = PartnerFirestoreDTO.from_firestore(doc_data, doc_id)
        return {"success": True, "data": partner_data}
    except Exception as e:
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    result = investigate_partners_collection()
    print("\n🎯 RESULTADO FINAL:")
    print(f"Documentos: {result['total_documents']}")
    print(f"Ativos (True): {result['active_count']['true']}")
    print(f"Inativos (False): {result['active_count']['false']}")
    print(f"Campo ausente: {result['active_count']['missing']}")
    print(f"Valores inválidos: {result['active_count']['other']}")
    print(f"Conversões DTO bem-sucedidas: {result['conversion_stats']['success']}")
    print(f"Elegíveis para endpoint: {result['endpoint_eligible_count']}")
    print(f"Categorias: {len(result['categories'])}")
    print(f"Tenants: {len(result['tenants'])}")
