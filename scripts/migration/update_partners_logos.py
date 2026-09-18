"""
Script temporário para atualizar URLs dos logos no arquivo firestore_partners.json.
"""
import json
import sys
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.append(str(Path(__file__).parent.parent.parent))


def main():
    """Atualiza URLs dos logos no arquivo firestore_partners.json."""

    # Caminhos dos arquivos
    base_dir = Path(__file__).parent.parent.parent
    partners_file = base_dir / "data" / "firestore_export" / "firestore_partners.json"
    mapping_file = Path(__file__).parent / "logos_urls_mapping.json"

    print(f"Carregando arquivo de parceiros: {partners_file}")
    print(f"Carregando mapeamento de URLs: {mapping_file}")

    # Carregar arquivo de parceiros
    try:
        with open(partners_file, encoding="utf-8") as f:
            partners_data = json.load(f)
    except Exception as e:
        print(f"Erro ao carregar arquivo de parceiros: {e}")
        return

    # Carregar mapeamento de URLs
    try:
        with open(mapping_file, encoding="utf-8") as f:
            logo_urls = json.load(f)
    except Exception as e:
        print(f"Erro ao carregar mapeamento de URLs: {e}")
        return

    print(f"\nEncontrados {len(logo_urls)} logos disponíveis no Firebase Storage")
    print(f"Processando {len(partners_data.get('partners', {}))} parceiros no arquivo JSON")

    # Contadores para relatório
    updated_count = 0
    set_to_null_count = 0
    unchanged_count = 0

    # Atualizar URLs dos logos
    partners = partners_data.get("partners", {})

    for partner_id, partner_data in partners.items():
        current_url = partner_data.get("logo_url")

        if partner_id in logo_urls:
            # Parceiro tem logo disponível - atualizar URL
            new_url = logo_urls[partner_id]
            if current_url != new_url:
                partner_data["logo_url"] = new_url
                updated_count += 1
                print(f"✓ Atualizado {partner_id}: {new_url[:80]}...")
            else:
                unchanged_count += 1
                print(f"- Inalterado {partner_id}: URL já está correta")
        else:
            # Parceiro não tem logo disponível - definir como null
            if current_url is not None:
                partner_data["logo_url"] = None
                set_to_null_count += 1
                print(f"✗ Definido como null {partner_id}: logo não encontrado")
            else:
                unchanged_count += 1
                print(f"- Inalterado {partner_id}: já era null")

    # Salvar arquivo atualizado
    try:
        with open(partners_file, "w", encoding="utf-8") as f:
            json.dump(partners_data, f, indent=2, ensure_ascii=False)

        print("\n=== RELATÓRIO DE ATUALIZAÇÃO ===")
        print(f"URLs atualizadas: {updated_count}")
        print(f"URLs definidas como null: {set_to_null_count}")
        print(f"URLs inalteradas: {unchanged_count}")
        print(f"Total de parceiros: {len(partners)}")
        print(f"\nArquivo salvo com sucesso: {partners_file}")

    except Exception as e:
        print(f"Erro ao salvar arquivo: {e}")


if __name__ == "__main__":
    main()
