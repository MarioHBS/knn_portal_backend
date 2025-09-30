#!/usr/bin/env python3
"""
Debug da estrutura dos benefícios no Firestore
"""

import sys
from pathlib import Path

# Adicionar o diretório src ao path
current_dir = Path(__file__).parent
src_path = current_dir / "src"
sys.path.insert(0, str(src_path))

from db.firestore import db


def debug_benefit_structure():
    """Debug da estrutura dos benefícios no Firestore."""
    try:
        # Buscar o parceiro específico
        partner_id = "PTN_T4L5678_TEC"

        print(f"🔍 Debugando benefícios para parceiro: {partner_id}")

        # Primeiro, tentar buscar como documento direto na coleção benefits
        benefits_ref = db.collection("benefits")
        partner_doc_ref = benefits_ref.document(partner_id)
        partner_doc = partner_doc_ref.get()

        if partner_doc.exists:
            print("✅ Documento encontrado na coleção benefits")
            data = partner_doc.to_dict()

            # Procurar por chaves que começam com BNF_
            benefit_keys = [key for key in data if key.startswith("BNF_")]
            print(
                f"📊 Encontradas {len(benefit_keys)} chaves de benefícios: {benefit_keys}"
            )

            # Examinar estrutura de cada benefício
            for i, benefit_key in enumerate(benefit_keys[:2]):  # Apenas os primeiros 2
                benefit_data = data[benefit_key]
                print(f"\n--- Benefício {i+1} (Chave: {benefit_key}) ---")

                # Verificar estrutura system
                if "system" in benefit_data:
                    system = benefit_data["system"]
                    print(f"System type: {system.get('type', 'N/A')}")
                    print(f"System status: {system.get('status', 'N/A')}")
                    print(f"System audience: {system.get('audience', 'N/A')}")
                else:
                    print("❌ Campo 'system' não encontrado")

                # Verificar estrutura configuration
                if "configuration" in benefit_data:
                    config = benefit_data["configuration"]
                    print(f"Config value_type: {config.get('value_type', 'N/A')}")
                    print(f"Config value: {config.get('value', 'N/A')}")
                else:
                    print("❌ Campo 'configuration' não encontrado")

                # Verificar audience no nível raiz
                if "audience" in benefit_data:
                    audience = benefit_data["audience"]
                    print(f"Root audience: {audience} (tipo: {type(audience)})")

                # Mostrar estrutura completa (limitada)
                print("📋 Estrutura completa:")
                for key, value in benefit_data.items():
                    if isinstance(value, dict):
                        print(f"  {key}: dict com {len(value)} campos")
                        if key in ["system", "configuration"]:
                            for subkey, subvalue in value.items():
                                print(
                                    f"    {subkey}: {type(subvalue).__name__} = {subvalue}"
                                )
                    elif isinstance(value, list):
                        print(f"  {key}: list com {len(value)} itens = {value}")
                    else:
                        print(f"  {key}: {type(value).__name__} = {value}")
        else:
            print(f"❌ Documento {partner_id} não encontrado na coleção benefits")

            # Verificar se existem benefícios em geral
            all_benefits = benefits_ref.limit(3).get()
            print(
                f"\n🔍 Verificando benefícios em geral: {len(all_benefits)} encontrados"
            )

            if all_benefits:
                sample_doc = all_benefits[0]
                sample_data = sample_doc.to_dict()
                print(f"📋 Estrutura de exemplo (ID: {sample_doc.id}):")

                # Procurar por chaves que começam com BNF_
                benefit_keys = [
                    key for key in sample_data if key.startswith("BNF_")
                ]
                if benefit_keys:
                    sample_benefit = sample_data[benefit_keys[0]]
                    print(f"🔍 Estrutura do benefício {benefit_keys[0]}:")
                    for key, value in sample_benefit.items():
                        if isinstance(value, dict):
                            print(f"  {key}: dict com {len(value)} campos")
                            for subkey, subvalue in value.items():
                                print(
                                    f"    {subkey}: {type(subvalue).__name__} = {subvalue}"
                                )
                        elif isinstance(value, list):
                            print(f"  {key}: list com {len(value)} itens = {value}")
                        else:
                            print(f"  {key}: {type(value).__name__} = {value}")

    except Exception as e:
        print(f"❌ Erro ao debugar estrutura dos benefícios: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    debug_benefit_structure()
