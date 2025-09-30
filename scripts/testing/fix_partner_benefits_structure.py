#!/usr/bin/env python3
"""
Script para corrigir a estrutura do documento de benefícios do parceiro no Firestore.

O problema identificado é que a API busca por benefits_doc.get("data", {})
mas o documento não tem um campo "data" - os benefícios estão diretamente no documento.

Este script reorganiza a estrutura para que os benefícios fiquem dentro de um campo "data".
"""

import asyncio
import json
import os
import sys
from datetime import datetime

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.db.firestore import get_database
from src.utils.logging import logger


async def fix_partner_benefits_structure():
    """Corrige a estrutura do documento de benefícios do parceiro."""

    partner_id = "PTN_T4L5678_TEC"
    tenant_id = "knn-dev-tenant"

    try:
        # Obter cliente do Firestore
        firestore_client = get_database(tenant_id)

        logger.info(f"🔧 Iniciando correção da estrutura para parceiro: {partner_id}")

        # 1. Buscar documento atual
        logger.info("📖 Buscando documento atual...")
        doc_ref = firestore_client.collection("benefits").document(partner_id)
        doc = doc_ref.get()  # Remover await - get() é síncrono

        if not doc.exists:
            logger.error(f"❌ Documento não encontrado: {partner_id}")
            return False

        current_data = doc.to_dict()
        logger.info(f"✅ Documento encontrado com {len(current_data)} campos")

        # 2. Identificar benefícios (campos que começam com BNF_)
        benefits = {}
        metadata = {}

        for key, value in current_data.items():
            if key.startswith("BNF_"):
                benefits[key] = value
                logger.info(f"📦 Benefício encontrado: {key}")
            else:
                metadata[key] = value
                logger.info(f"📋 Metadado encontrado: {key}")

        logger.info(f"✅ Encontrados {len(benefits)} benefícios e {len(metadata)} metadados")

        # 3. Criar nova estrutura
        new_structure = {
            **metadata,  # Manter metadados no nível raiz
            "data": benefits  # Colocar benefícios dentro do campo "data"
        }

        # 4. Fazer backup do documento atual
        backup_data = {
            "timestamp": datetime.now().isoformat(),
            "partner_id": partner_id,
            "tenant_id": tenant_id,
            "original_structure": current_data,
            "new_structure": new_structure
        }

        backup_filename = f"partner_benefits_backup_{partner_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        backup_path = os.path.join(os.path.dirname(__file__), backup_filename)

        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, indent=2, ensure_ascii=False, default=str)

        logger.info(f"💾 Backup salvo em: {backup_path}")

        # 5. Atualizar documento no Firestore
        logger.info("🔄 Atualizando estrutura no Firestore...")
        doc_ref.set(new_structure)  # Remover await - set() é síncrono

        logger.info("✅ Estrutura corrigida com sucesso!")

        # 6. Verificar se a correção funcionou
        logger.info("🔍 Verificando correção...")
        updated_doc = doc_ref.get()  # Remover await - get() é síncrono
        updated_data = updated_doc.to_dict()

        data_field = updated_data.get("data", {})
        benefits_count = len([k for k in data_field if k.startswith("BNF_")])

        logger.info(f"✅ Verificação: {benefits_count} benefícios encontrados no campo 'data'")

        return True

    except Exception as e:
        logger.error(f"❌ Erro ao corrigir estrutura: {str(e)}")
        return False

async def main():
    """Função principal."""
    logger.info("🚀 Iniciando correção da estrutura de benefícios do parceiro")

    success = await fix_partner_benefits_structure()

    if success:
        logger.info("🎉 Correção concluída com sucesso!")
        print("\n" + "="*80)
        print(" CORREÇÃO CONCLUÍDA COM SUCESSO")
        print("="*80)
        print("✅ Estrutura do documento corrigida")
        print("✅ Benefícios movidos para o campo 'data'")
        print("✅ Backup criado")
        print("✅ Verificação realizada")
        print("\nAgora você pode testar novamente o endpoint /partner/promotions")
    else:
        logger.error("❌ Falha na correção")
        print("\n" + "="*80)
        print(" FALHA NA CORREÇÃO")
        print("="*80)
        print("❌ Verifique os logs para mais detalhes")

if __name__ == "__main__":
    asyncio.run(main())
