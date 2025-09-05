#!/usr/bin/env python3
"""
Script para adicionar dados de parceiros ao arquivo firestore_employees_partners.json
Converte os dados do arquivo dados_parceiros_teste.json para o formato Firestore
"""

import json
from datetime import datetime
from pathlib import Path


def add_partners_to_firestore():
    """Adiciona dados de parceiros ao arquivo firestore_employees_partners.json"""

    # Caminhos dos arquivos
    partners_source_file = Path("sources/dados_parceiros_teste.json")
    firestore_file = Path("data/firestore_employees_partners.json")
    backup_file = Path("data/firestore_employees_partners_backup.json")

    # Verificar se os arquivos existem
    if not partners_source_file.exists():
        print(f"Erro: Arquivo {partners_source_file} não encontrado")
        return

    if not firestore_file.exists():
        print(f"Erro: Arquivo {firestore_file} não encontrado")
        return

    print("Carregando arquivo de parceiros...")
    with open(partners_source_file, encoding="utf-8") as f:
        partners_data = json.load(f)

    print("Carregando arquivo firestore_employees_partners.json...")
    with open(firestore_file, encoding="utf-8") as f:
        firestore_data = json.load(f)

    # Criar backup
    print(f"Criando backup em {backup_file}...")
    with open(backup_file, "w", encoding="utf-8") as f:
        json.dump(firestore_data, f, ensure_ascii=False, indent=2)

    # Obter dados dos parceiros
    partners = partners_data.get("partners", {})

    if not partners:
        print("Nenhum parceiro encontrado nos dados")
        return

    print(f"Processando {len(partners)} parceiros...")

    # Adicionar coleção de parceiros se não existir
    if "__collection__/partners" not in firestore_data:
        firestore_data["__collection__/partners"] = {}

    # Timestamp atual
    current_time = datetime.now().isoformat()

    # Converter cada parceiro para o formato Firestore
    partners_added = 0
    for partner_id, partner_info in partners.items():
        firestore_key = f"__collection__/partners/{partner_id}"

        # Verificar se o parceiro já existe
        if firestore_key in firestore_data:
            print(f"Parceiro {partner_id} já existe, pulando...")
            continue

        # Converter estrutura para formato Firestore
        firestore_partner = {
            "data": {
                "id": partner_id,
                "tenant_id": "knn-dev-tenant",
                "name": partner_info.get("name", ""),
                "benefit": partner_info.get("benefit", ""),
                "cnpj": partner_info.get("cnpj", ""),
                "category": partner_info.get("category", ""),
                "address": {
                    "zip": partner_info.get("address", {}).get("zip", ""),
                    "street": partner_info.get("address", {}).get("street", ""),
                    "neighborhood": partner_info.get("address", {}).get(
                        "neighborhood", ""
                    ),
                    "city": partner_info.get("address", {}).get("city", ""),
                    "state": partner_info.get("address", {}).get("state", ""),
                },
                "contact": {
                    "phone": partner_info.get("contact", {}).get("phone", ""),
                    "whatsapp": partner_info.get("contact", {}).get("whatsapp", ""),
                    "email": partner_info.get("contact", {}).get("email", ""),
                },
                "social_networks": {
                    "instagram": partner_info.get("social_networks", {}).get(
                        "instagram", ""
                    ),
                    "facebook": partner_info.get("social_networks", {}).get(
                        "facebook", ""
                    ),
                    "website": partner_info.get("social_networks", {}).get(
                        "website", ""
                    ),
                },
                "maps": {
                    "google": partner_info.get("maps", {}).get("google", ""),
                    "waze": partner_info.get("maps", {}).get("waze", ""),
                },
                "active": True,
                "created_at": current_time,
                "updated_at": current_time,
            }
        }

        # Adicionar ao firestore_data
        firestore_data[firestore_key] = firestore_partner
        partners_added += 1
        print(f"Adicionado parceiro: {partner_info.get('name', partner_id)}")

    # Salvar arquivo atualizado
    print(f"Salvando arquivo atualizado com {partners_added} novos parceiros...")
    with open(firestore_file, "w", encoding="utf-8") as f:
        json.dump(firestore_data, f, ensure_ascii=False, indent=2)

    # Relatório final
    print("\n=== RELATÓRIO DE ADIÇÃO DE PARCEIROS ===")
    print(f"Arquivo fonte: {partners_source_file}")
    print(f"Arquivo destino: {firestore_file}")
    print(f"Backup criado: {backup_file}")
    print(f"Parceiros processados: {len(partners)}")
    print(f"Parceiros adicionados: {partners_added}")

    # Verificar tamanhos dos arquivos
    original_size = firestore_file.stat().st_size / 1024  # KB
    backup_size = backup_file.stat().st_size / 1024  # KB

    print("\n=== TAMANHOS DOS ARQUIVOS ===")
    print(f"Arquivo original (backup): {backup_size:.2f} KB")
    print(f"Arquivo atualizado: {original_size:.2f} KB")
    print(f"Diferença: +{original_size - backup_size:.2f} KB")

    return {
        "partners_processed": len(partners),
        "partners_added": partners_added,
        "backup_created": str(backup_file),
        "file_updated": str(firestore_file),
    }


if __name__ == "__main__":
    add_partners_to_firestore()
