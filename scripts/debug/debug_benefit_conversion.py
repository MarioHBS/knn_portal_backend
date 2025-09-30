#!/usr/bin/env python3
"""
Script para debugar a conversão de benefícios e identificar onde está ocorrendo o erro de ValidationInfo.
"""

import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import traceback

from src.db.firestore import firestore_client
from src.models.benefit import BenefitDTO


async def debug_benefit_conversion():
    """Debug da conversão de benefícios."""

    partner_id = "PTN_T4L5678_TEC"
    tenant_id = "knn-dev-tenant"  # Corrigido para o tenant correto

    print(f"🔍 Debugando conversão de benefícios para parceiro: {partner_id}")
    print(f"🏢 Tenant: {tenant_id}")

    try:
        # Buscar documento do parceiro na coleção 'benefits'
        # Primeiro tentar com o formato completo
        partner_doc = await firestore_client.get_document(
            "benefits", f"{tenant_id}_{partner_id}", tenant_id=tenant_id
        )

        if not partner_doc:
            # Tentar apenas com o partner_id
            print(f"⚠️ Tentando buscar apenas com partner_id: {partner_id}")
            partner_doc = await firestore_client.get_document(
                "benefits", partner_id, tenant_id=tenant_id
            )

        if not partner_doc:
            print(
                f"❌ Documento do parceiro {partner_id} não encontrado na coleção 'benefits'"
            )

            # Listar documentos disponíveis para debug
            print("🔍 Listando documentos disponíveis na coleção 'benefits':")
            try:
                docs = await firestore_client.query_documents(
                    "benefits", [], tenant_id=tenant_id, limit=10
                )
                for doc in docs:
                    if hasattr(doc, "id"):
                        print(f"   - {doc.id}")
                    else:
                        print(f"   - {doc}")
            except Exception as list_error:
                print(f"   Erro ao listar documentos: {list_error}")
            return

        print(f"✅ Documento encontrado com {len(partner_doc)} campos")

        # Extrair benefícios ativos para estudantes
        benefit_keys = [key for key in partner_doc if key.startswith("BNF_")]
        print(f"📋 Encontrados {len(benefit_keys)} benefícios: {benefit_keys}")

        for benefit_key in benefit_keys:
            print(f"\n🔍 Processando benefício: {benefit_key}")

            try:
                benefit_data = partner_doc[benefit_key]
                system = benefit_data.get("system", {})
                status = system.get("status", "")
                audience = system.get("audience", "")

                print(f"   Status: {status}")
                print(f"   Audience: {audience} (tipo: {type(audience)})")

                if status == "active":
                    print("   ✅ Benefício ativo, tentando converter...")

                    # Tentar criar BenefitDTO
                    benefit_dto = BenefitDTO(
                        key=benefit_key,
                        benefit_data=benefit_data,
                        partner_id=partner_id,
                    )
                    print("   ✅ BenefitDTO criado com sucesso")

                    # Tentar converter para Benefit
                    benefit_obj = benefit_dto.to_benefit()
                    print("   ✅ Conversão para Benefit bem-sucedida")
                    print(f"   📊 Benefit: {benefit_obj.id} - {benefit_obj.title}")

                else:
                    print("   ⏸️ Benefício inativo, pulando...")

            except Exception as e:
                print(f"   ❌ Erro ao processar benefício {benefit_key}: {str(e)}")
                print("   🔍 Traceback completo:")
                traceback.print_exc()

    except Exception as e:
        print(f"❌ Erro geral: {str(e)}")
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(debug_benefit_conversion())
