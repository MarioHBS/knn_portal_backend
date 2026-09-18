"""
Script temporário para obter URLs corretas dos logos no Firebase Storage.
"""
import asyncio
import json
import sys
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.utils.logos_service import LogosService


async def main():
    """Obtém URLs corretas dos logos disponíveis."""
    service = LogosService()

    try:
        print("Buscando logos disponíveis no Firebase Storage...")
        logos = await service.list_available_logos(force_refresh=True)

        print(f"\n=== ENCONTRADOS {len(logos)} LOGOS ===\n")

        # Criar dicionário com mapeamento partner_id -> URL
        logo_urls = {}

        for logo in logos:
            partner_id = logo["partner_id"]
            url = logo["url"]
            logo_urls[partner_id] = url

            print(f"Partner ID: {partner_id}")
            print(f"URL: {url}")
            print("---")

        # Salvar mapeamento em arquivo JSON
        output_file = Path(__file__).parent / "logos_urls_mapping.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(logo_urls, f, indent=2, ensure_ascii=False)

        print(f"\nMapeamento salvo em: {output_file}")
        print(f"Total de logos: {len(logo_urls)}")

    except Exception as e:
        print(f"Erro ao buscar logos: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
