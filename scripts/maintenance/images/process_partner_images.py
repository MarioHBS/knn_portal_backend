#!/usr/bin/env python3
"""
Script para processar imagens de parceiros:
- Redimensiona para 200x200px mantendo proporção
- Adiciona fundo transparente
- Converte para PNG com transparência
- Preserva qualidade da imagem
"""

import json
import os
from datetime import datetime

from PIL import Image


def process_image(input_path, output_path, target_size=(200, 200)):
    """Processa uma imagem aplicando as especificações necessárias."""
    try:
        with Image.open(input_path) as img:
            # Converte para RGBA se não for
            if img.mode != "RGBA":
                img = img.convert("RGBA")

            # Calcula o redimensionamento mantendo proporção
            img.thumbnail(target_size, Image.Resampling.LANCZOS)

            # Cria uma nova imagem com fundo transparente
            new_img = Image.new("RGBA", target_size, (0, 0, 0, 0))

            # Calcula posição para centralizar a imagem
            x = (target_size[0] - img.width) // 2
            y = (target_size[1] - img.height) // 2

            # Cola a imagem redimensionada no centro
            new_img.paste(img, (x, y), img if img.mode == "RGBA" else None)

            # Salva a imagem processada
            new_img.save(output_path, "PNG", optimize=True)

            return {
                "success": True,
                "original_size": f"{img.width}x{img.height}",
                "final_size": f"{new_img.width}x{new_img.height}",
                "file_size_kb": round(os.path.getsize(output_path) / 1024, 2),
            }

    except Exception as e:
        return {"success": False, "error": str(e)}


def process_all_partner_images():
    """Processa todas as imagens de logo dos parceiros."""
    input_dir = "P:\\ProjectsWEB\\PRODUCAO\\KNN PROJECT\\knn_portal_journey_club_backend\\data\\firestore_export\\partners_images"
    output_dir = "P:\\ProjectsWEB\\PRODUCAO\\KNN PROJECT\\knn_portal_journey_club_backend\\statics\\logos\\processed"

    # Cria diretório de saída se não existir
    os.makedirs(output_dir, exist_ok=True)

    # Filtra apenas imagens de logo
    logo_files = [f for f in os.listdir(input_dir) if f.endswith("_logo.png")]

    results = {
        "processing_date": datetime.now().isoformat(),
        "total_images": len(logo_files),
        "processed_images": [],
        "summary": {"successful": 0, "failed": 0, "total_size_kb": 0},
    }

    print(f"Processando {len(logo_files)} imagens de logo...\n")

    for filename in sorted(logo_files):
        input_path = os.path.join(input_dir, filename)

        # Remove o sufixo _logo do nome do arquivo de saída
        output_filename = filename.replace("_logo.png", ".png")
        output_path = os.path.join(output_dir, output_filename)

        print(f"📷 Processando {filename}...")

        result = process_image(input_path, output_path)
        result["input_filename"] = filename
        result["output_filename"] = output_filename

        if result["success"]:
            print(
                f"   ✅ Sucesso: {result['original_size']} → {result['final_size']} ({result['file_size_kb']} KB)"
            )
            results["summary"]["successful"] += 1
            results["summary"]["total_size_kb"] += result["file_size_kb"]
        else:
            print(f"   ❌ Erro: {result['error']}")
            results["summary"]["failed"] += 1

        results["processed_images"].append(result)
        print()

    # Estatísticas finais
    print("\n=== RESUMO DO PROCESSAMENTO ===")
    print(f"Total de imagens: {results['total_images']}")
    print(f"Processadas com sucesso: {results['summary']['successful']}")
    print(f"Falharam: {results['summary']['failed']}")
    print(f"Tamanho total: {results['summary']['total_size_kb']:.2f} KB")

    if results["summary"]["successful"] > 0:
        avg_size = (
            results["summary"]["total_size_kb"] / results["summary"]["successful"]
        )
        print(f"Tamanho médio por imagem: {avg_size:.2f} KB")

    # Salva relatório
    report_path = (
        "docs/processamento_imagens_"
        + datetime.now().strftime("%Y%m%d_%H%M%S")
        + ".json"
    )
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n📄 Relatório salvo em: {report_path}")
    print(f"📁 Imagens processadas salvas em: {output_dir}")

    return results


if __name__ == "__main__":
    process_all_partner_images()
