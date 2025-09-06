#!/usr/bin/env python3
"""
Script para analisar imagens de parceiros e verificar especificações.
Analisa dimensões, formato e transparência das imagens.
"""

import json
import os
from datetime import datetime

from PIL import Image


def analyze_image(image_path):
    """Analisa uma imagem e retorna suas especificações."""
    try:
        with Image.open(image_path) as img:
            # Informações básicas
            width, height = img.size
            format_type = img.format
            mode = img.mode

            # Verifica transparência
            has_transparency = False
            if mode in ("RGBA", "LA") or "transparency" in img.info:
                has_transparency = True

            # Calcula tamanho do arquivo
            file_size = os.path.getsize(image_path)

            return {
                "filename": os.path.basename(image_path),
                "width": width,
                "height": height,
                "format": format_type,
                "mode": mode,
                "has_transparency": has_transparency,
                "file_size_bytes": file_size,
                "file_size_kb": round(file_size / 1024, 2),
                "aspect_ratio": round(width / height, 2) if height > 0 else 0,
            }
    except Exception as e:
        return {"filename": os.path.basename(image_path), "error": str(e)}


def analyze_partner_images():
    """Analisa todas as imagens de parceiros."""
    images_dir = "P:\\ProjectsWEB\\PRODUCAO\\KNN PROJECT\\knn_portal_journey_club_backend\\data\\firestore_export\\partners_images"

    if not os.path.exists(images_dir):
        print(f"Diretório não encontrado: {images_dir}")
        return

    # Filtra apenas imagens de logo
    logo_files = [f for f in os.listdir(images_dir) if f.endswith("_logo.png")]

    results = {
        "analysis_date": datetime.now().isoformat(),
        "total_logo_images": len(logo_files),
        "images": [],
        "summary": {
            "png_format": 0,
            "has_transparency": 0,
            "dimensions": {},
            "file_sizes": [],
        },
    }

    print(f"Analisando {len(logo_files)} imagens de logo...\n")

    for filename in sorted(logo_files):
        image_path = os.path.join(images_dir, filename)
        analysis = analyze_image(image_path)
        results["images"].append(analysis)

        if "error" not in analysis:
            print(f"📁 {analysis['filename']}")
            print(f"   Dimensões: {analysis['width']}x{analysis['height']}px")
            print(f"   Formato: {analysis['format']} ({analysis['mode']})")
            print(f"   Transparência: {'✅' if analysis['has_transparency'] else '❌'}")
            print(f"   Tamanho: {analysis['file_size_kb']} KB")
            print(f"   Proporção: {analysis['aspect_ratio']}:1")
            print()

            # Atualiza estatísticas
            if analysis["format"] == "PNG":
                results["summary"]["png_format"] += 1
            if analysis["has_transparency"]:
                results["summary"]["has_transparency"] += 1

            # Agrupa por dimensões
            dim_key = f"{analysis['width']}x{analysis['height']}"
            if dim_key not in results["summary"]["dimensions"]:
                results["summary"]["dimensions"][dim_key] = 0
            results["summary"]["dimensions"][dim_key] += 1

            results["summary"]["file_sizes"].append(analysis["file_size_kb"])
        else:
            print(f"❌ Erro ao analisar {analysis['filename']}: {analysis['error']}")

    # Estatísticas finais
    print("\n=== RESUMO DA ANÁLISE ===")
    print(f"Total de imagens: {results['total_logo_images']}")
    print(
        f"Formato PNG: {results['summary']['png_format']}/{results['total_logo_images']}"
    )
    print(
        f"Com transparência: {results['summary']['has_transparency']}/{results['total_logo_images']}"
    )
    print("\nDimensões encontradas:")
    for dim, count in results["summary"]["dimensions"].items():
        print(f"  {dim}: {count} imagem(ns)")

    if results["summary"]["file_sizes"]:
        avg_size = sum(results["summary"]["file_sizes"]) / len(
            results["summary"]["file_sizes"]
        )
        print(f"\nTamanho médio: {avg_size:.2f} KB")
        print(f"Menor arquivo: {min(results['summary']['file_sizes'])} KB")
        print(f"Maior arquivo: {max(results['summary']['file_sizes'])} KB")

    # Salva relatório
    report_path = (
        "docs/analise_imagens_logos_"
        + datetime.now().strftime("%Y%m%d_%H%M%S")
        + ".json"
    )
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n📄 Relatório salvo em: {report_path}")
    return results


if __name__ == "__main__":
    analyze_partner_images()
