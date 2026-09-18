#!/usr/bin/env python3
"""
Script para investigar exclusivamente a estrutura da coleção 'benefits' no Firestore.
Analisa todos os documentos, benefícios e suas estruturas para identificar discrepâncias.
"""

import sys
from pathlib import Path

# Adicionar o diretório raiz do projeto ao Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from google.cloud import firestore  # noqa: E402

from src.utils import logger  # noqa: E402


def investigate_benefits_collection():
    """Investiga a estrutura da coleção 'benefits', tratando cada documento como um benefício."""
    try:
        logger.info("🔍 Investigando a coleção 'benefits' (cada documento é um benefício)...")

        db = firestore.Client()
        benefits_ref = db.collection("benefits")
        docs = benefits_ref.stream()

        total_benefits = 0
        active_benefits = 0
        inactive_benefits = 0
        unknown_status = 0
        benefits_data = []

        logger.info("📋 Analisando cada documento como um benefício individual...")

        for doc in docs:
            total_benefits += 1
            doc_data = doc.to_dict()
            benefit_id = doc.id
            
            title = doc_data.get("title", "N/A")
            status = doc_data.get("status", "unknown")
            tenant_id = doc_data.get("tenant_id", "NÃO DEFINIDO")

            benefit_info = {
                "id": benefit_id,
                "title": title,
                "status": status,
                "tenant_id": tenant_id,
            }
            benefits_data.append(benefit_info)

            logger.info(f"\n📄 Benefício #{total_benefits}: {benefit_id}")
            logger.info(f"   - Título: '{title}'")
            logger.info(f"   - Status: {status}")
            logger.info(f"   - Tenant ID: {tenant_id}")

            if status == "active":
                active_benefits += 1
            elif status == "inactive":
                inactive_benefits += 1
            else:
                unknown_status += 1

        logger.info("\n📊 RESUMO DA INVESTIGAÇÃO:")
        logger.info(f"   📄 Total de benefícios (documentos): {total_benefits}")
        logger.info(f"   ✅ Benefícios ativos: {active_benefits}")
        logger.info(f"   ❌ Benefícios inativos: {inactive_benefits}")
        if unknown_status > 0:
            logger.warning(f"   ❓ Benefícios com status desconhecido: {unknown_status}")

        logger.info("🏁 Investigação da coleção 'benefits' concluída!")

        return {
            "total_benefits": total_benefits,
            "active_benefits": active_benefits,
            "inactive_benefits": inactive_benefits,
            "benefits_data": benefits_data,
        }

    except Exception as e:
        logger.error(f"❌ Erro durante investigação: {str(e)}")
        raise


if __name__ == "__main__":
    result = investigate_benefits_collection()
    print("\n🎯 RESULTADO FINAL:")
    print(f"Total de benefícios: {result['total_benefits']}")
    print(f"Benefícios ativos: {result['active_benefits']}")
    print(f"Benefícios inativos: {result['inactive_benefits']}")
    print(f"Ativos: {result['active_benefits']}")
    print(f"Inativos: {result['inactive_benefits']}")
