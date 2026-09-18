#!/usr/bin/env python3
"""
Script para corrigir o tenant_id nos documentos da coleção 'benefits'.
Adiciona o tenant_id 'knn-dev-tenant' aos documentos que não o possuem.
"""

import sys
from pathlib import Path

# Adicionar o diretório raiz do projeto ao Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from google.cloud import firestore  # noqa: E402

from src.utils import logger  # noqa: E402


def fix_benefits_tenant_id():
    """Corrige o tenant_id nos documentos da coleção 'benefits'."""
    try:
        logger.info("🔧 Corrigindo tenant_id na coleção 'benefits'...")

        # Inicializar cliente Firestore diretamente
        db = firestore.Client()

        # Acessar a coleção 'benefits'
        benefits_ref = db.collection("benefits")

        # Listar todos os documentos na coleção benefits
        docs = benefits_ref.stream()
        updated_count = 0
        skipped_count = 0

        logger.info("📋 Verificando documentos da coleção 'benefits'...")

        for doc in docs:
            doc_data = doc.to_dict()
            doc_id = doc.id

            # Verificar se o documento já tem tenant_id
            current_tenant_id = doc_data.get("tenant_id")

            if current_tenant_id is None:
                logger.info(f"📄 Documento {doc_id}: Adicionando tenant_id")
                
                # Adicionar tenant_id ao documento
                doc_data["tenant_id"] = "knn-dev-tenant"
                
                # Atualizar o documento no Firestore
                doc.reference.set(doc_data)
                updated_count += 1
                
                logger.info(f"   ✅ tenant_id adicionado: knn-dev-tenant")
            else:
                logger.info(f"📄 Documento {doc_id}: tenant_id já existe ({current_tenant_id})")
                skipped_count += 1

        # Resumo final
        logger.info("\n📊 RESUMO DA CORREÇÃO:")
        logger.info(f"   ✅ Documentos atualizados: {updated_count}")
        logger.info(f"   ⏭️  Documentos ignorados: {skipped_count}")
        logger.info(f"   📊 Total processado: {updated_count + skipped_count}")

        logger.info("🏁 Correção do tenant_id concluída!")

        return {
            "updated_count": updated_count,
            "skipped_count": skipped_count,
            "total_processed": updated_count + skipped_count,
        }

    except Exception as e:
        logger.error(f"❌ Erro durante correção: {str(e)}")
        raise


if __name__ == "__main__":
    result = fix_benefits_tenant_id()
    print("\n🎯 RESULTADO FINAL:")
    print(f"Atualizados: {result['updated_count']}")
    print(f"Ignorados: {result['skipped_count']}")
    print(f"Total: {result['total_processed']}")