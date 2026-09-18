#!/usr/bin/env python3
"""
Script para investigar a estrutura real do documento no Firestore
e verificar problemas com tenant_id na busca de benefícios.
"""

import sys
from pathlib import Path

from google.cloud import firestore

from src.db.firestore import firestore_client
from src.utils import logger

# Adicionar o diretório raiz do projeto ao Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


async def investigate_firestore_structure():
    """Investiga a estrutura real do documento no Firestore."""
    try:
        logger.info("🔍 Investigando estrutura do Firestore...")

        # Inicializar cliente Firestore diretamente
        db = firestore.Client()

        # 1. Listar todas as coleções disponíveis
        logger.info("📁 Listando coleções disponíveis...")
        collections = db.collections()
        collection_names = [col.id for col in collections]
        logger.info(f"Coleções encontradas: {collection_names}")

        # 2. Verificar a coleção 'benefits'
        if "benefits" in collection_names:
            logger.info("📋 Investigando coleção 'benefits'...")
            benefits_ref = db.collection("benefits")

            # Listar todos os documentos na coleção benefits
            docs = benefits_ref.stream()
            doc_count = 0

            for doc in docs:
                doc_count += 1
                logger.info(f"📄 Documento ID: {doc.id}")

                # Se for o documento do parceiro que estamos procurando
                if doc.id == "PTN_T4L5678_TEC":
                    logger.info("🎯 Encontrado documento do parceiro PTN_T4L5678_TEC!")
                    doc_data = doc.to_dict()

                    # Verificar estrutura do documento
                    logger.info("📊 Estrutura do documento:")
                    for key, value in doc_data.items():
                        if isinstance(value, dict):
                            logger.info(f"  - {key}: [dict com {len(value)} chaves]")
                            if key.startswith("BNF_"):
                                logger.info(f"    Benefício {key}:")
                                for sub_key, sub_value in value.items():
                                    logger.info(
                                        f"      - {sub_key}: {type(sub_value).__name__}"
                                    )
                        else:
                            logger.info(f"  - {key}: {type(value).__name__} = {value}")

                    # Verificar se o benefício BNF_89A7FE_DC existe
                    if "BNF_89A7FE_DC" in doc_data:
                        logger.info("✅ Benefício BNF_89A7FE_DC encontrado!")
                        benefit_data = doc_data["BNF_89A7FE_DC"]
                        logger.info(f"📋 Estrutura do benefício: {benefit_data}")
                    else:
                        logger.warning("❌ Benefício BNF_89A7FE_DC NÃO encontrado!")
                        logger.info(
                            f"Benefícios disponíveis: {[k for k in doc_data if k.startswith('BNF_')]}"
                        )

                # Mostrar apenas os primeiros 5 documentos para não sobrecarregar
                if doc_count >= 5:
                    logger.info(
                        f"... (mostrando apenas os primeiros 5 de {doc_count}+ documentos)"
                    )
                    break

            logger.info(f"📊 Total de documentos na coleção 'benefits': {doc_count}")

        # 3. Testar busca com tenant_id
        logger.info("🔑 Testando busca com tenant_id...")

        # Tentar diferentes tenant_ids
        test_tenants = [None, "default", "knn-benefits", ""]

        for tenant in test_tenants:
            try:
                logger.info(f"🧪 Testando tenant_id: {tenant}")
                doc = await firestore_client.get_document(
                    "benefits", "PTN_T4L5678_TEC", tenant
                )
                if doc:
                    logger.info(f"✅ Documento encontrado com tenant_id: {tenant}")
                    logger.info(f"📋 Chaves do documento: {list(doc.keys())}")
                    if "BNF_89A7FE_DC" in doc:
                        logger.info(
                            "✅ Benefício BNF_89A7FE_DC encontrado neste tenant!"
                        )
                else:
                    logger.info(f"❌ Documento NÃO encontrado com tenant_id: {tenant}")
            except Exception as e:
                logger.error(f"❌ Erro ao buscar com tenant_id {tenant}: {str(e)}")

        logger.info("🏁 Investigação concluída!")

    except Exception as e:
        logger.error(f"❌ Erro durante investigação: {str(e)}")
        raise


if __name__ == "__main__":
    import asyncio

    asyncio.run(investigate_firestore_structure())
