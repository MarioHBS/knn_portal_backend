#!/usr/bin/env python3
"""
Script para analisar a estrutura de imagens dos parceiros
Analisa os dados dos partners e a estrutura atual de imagens
"""

import json
from datetime import datetime
from pathlib import Path


def load_partners_data(file_path):
    """Carrega dados dos partners do arquivo JSON"""
    try:
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"❌ Erro ao carregar arquivo: {e}")
        return None


def extract_partners_info(data):
    """Extrai informações dos partners"""
    partners = []

    for key, value in data.items():
        if key.startswith("__collection__/partners/PTN_"):
            partner_id = key.split("/")[-1]
            partner_data = value.get("data", {})

            partners.append(
                {
                    "id": partner_id,
                    "name": partner_data.get("name", ""),
                    "category": partner_data.get("category", ""),
                    "cnpj": partner_data.get("cnpj", ""),
                    "active": partner_data.get("active", False),
                    "instagram": partner_data.get("social_networks", {}).get(
                        "instagram"
                    ),
                    "facebook": partner_data.get("social_networks", {}).get("facebook"),
                    "website": partner_data.get("social_networks", {}).get("website"),
                }
            )

    return partners


def analyze_existing_images(images_dir):
    """Analisa imagens existentes no diretório"""
    images_path = Path(images_dir)
    existing_images = {}

    if images_path.exists():
        for file in images_path.iterdir():
            if file.is_file() and file.suffix.lower() in [
                ".png",
                ".jpg",
                ".jpeg",
                ".webp",
                ".svg",
            ]:
                # Extrai o ID do partner do nome do arquivo
                filename = file.stem
                parts = filename.split("_")
                if len(parts) >= 3:
                    partner_id = "_".join(parts[:3])  # PTN_XXXXXX_XXX
                    image_type = "_".join(parts[3:]) if len(parts) > 3 else "unknown"

                    if partner_id not in existing_images:
                        existing_images[partner_id] = []
                    existing_images[partner_id].append(
                        {
                            "type": image_type,
                            "filename": file.name,
                            "size": file.stat().st_size,
                            "extension": file.suffix,
                        }
                    )

    return existing_images


def generate_recommendations(partners, existing_images):
    """Gera recomendações para organização das imagens"""
    recommendations = {
        "structure": {
            "naming_convention": "PTN_XXXXXX_XXX_[tipo].[extensão]",
            "recommended_types": [
                "logo",  # Logo principal do parceiro
                "fachada",  # Foto da fachada/estabelecimento
                "banner",  # Banner promocional
                "card",  # Imagem para card/listagem
                "thumb",  # Thumbnail pequena
            ],
            "recommended_formats": {
                "logo": ["PNG", "SVG"],
                "fachada": ["JPG", "WEBP"],
                "banner": ["JPG", "WEBP", "PNG"],
                "card": ["JPG", "WEBP"],
                "thumb": ["JPG", "WEBP"],
            },
            "recommended_sizes": {
                "logo": "200x200px (quadrado)",
                "fachada": "800x600px (4:3)",
                "banner": "1200x400px (3:1)",
                "card": "400x300px (4:3)",
                "thumb": "150x150px (quadrado)",
            },
        },
        "missing_images": [],
        "existing_analysis": [],
        "categories_analysis": {},
    }

    # Analisa imagens existentes
    for partner_id, images in existing_images.items():
        partner_info = next((p for p in partners if p["id"] == partner_id), None)
        if partner_info:
            recommendations["existing_analysis"].append(
                {
                    "partner_id": partner_id,
                    "partner_name": partner_info["name"],
                    "category": partner_info["category"],
                    "images_count": len(images),
                    "image_types": [img["type"] for img in images],
                    "total_size_kb": sum(img["size"] for img in images) // 1024,
                }
            )

    # Identifica partners sem imagens
    for partner in partners:
        if partner["active"] and partner["id"] not in existing_images:
            recommendations["missing_images"].append(
                {
                    "partner_id": partner["id"],
                    "partner_name": partner["name"],
                    "category": partner["category"],
                    "priority": "high"
                    if partner["category"] in ["Educação", "Tecnologia"]
                    else "medium",
                }
            )

    # Análise por categoria
    categories = {}
    for partner in partners:
        if partner["active"]:
            cat = partner["category"]
            if cat not in categories:
                categories[cat] = {"total": 0, "with_images": 0, "partners": []}
            categories[cat]["total"] += 1
            categories[cat]["partners"].append(partner["name"])
            if partner["id"] in existing_images:
                categories[cat]["with_images"] += 1

    for _cat, info in categories.items():
        info["coverage_percentage"] = (
            (info["with_images"] / info["total"]) * 100 if info["total"] > 0 else 0
        )

    recommendations["categories_analysis"] = categories

    return recommendations


def generate_report(partners, existing_images, recommendations):
    """Gera relatório detalhado"""
    report = []
    report.append("# 📸 ANÁLISE DE IMAGENS DOS PARCEIROS")
    report.append("=" * 50)
    report.append(f"Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")

    # Estatísticas gerais
    report.append("## 📊 ESTATÍSTICAS GERAIS")
    report.append(
        f"- Total de partners ativos: {len([p for p in partners if p['active']])}"
    )
    report.append(f"- Partners com imagens: {len(existing_images)}")
    report.append(f"- Partners sem imagens: {len(recommendations['missing_images'])}")
    report.append(
        f"- Total de arquivos de imagem: {sum(len(imgs) for imgs in existing_images.values())}"
    )
    report.append("")

    # Estrutura recomendada
    report.append("## 🏗️ ESTRUTURA RECOMENDADA")
    report.append("")
    report.append("### Convenção de Nomenclatura:")
    report.append(f"`{recommendations['structure']['naming_convention']}`")
    report.append("")
    report.append("### Tipos de Imagem Recomendados:")
    for img_type in recommendations["structure"]["recommended_types"]:
        formats = ", ".join(
            recommendations["structure"]["recommended_formats"][img_type]
        )
        size = recommendations["structure"]["recommended_sizes"][img_type]
        report.append(f"- **{img_type}**: {formats} - {size}")
    report.append("")

    # Análise por categoria
    report.append("## 📈 ANÁLISE POR CATEGORIA")
    for category, info in recommendations["categories_analysis"].items():
        report.append("")
        report.append(f"### {category}")
        report.append(f"- Total de partners: {info['total']}")
        report.append(f"- Com imagens: {info['with_images']}")
        report.append(f"- Cobertura: {info['coverage_percentage']:.1f}%")
        report.append(f"- Partners: {', '.join(info['partners'])}")
    report.append("")

    # Imagens existentes
    if recommendations["existing_analysis"]:
        report.append("## ✅ IMAGENS EXISTENTES")
        for analysis in recommendations["existing_analysis"]:
            report.append("")
            report.append(f"### {analysis['partner_name']} ({analysis['partner_id']})")
            report.append(f"- Categoria: {analysis['category']}")
            report.append(f"- Quantidade de imagens: {analysis['images_count']}")
            report.append(f"- Tipos: {', '.join(analysis['image_types'])}")
            report.append(f"- Tamanho total: {analysis['total_size_kb']} KB")

    # Partners sem imagens
    if recommendations["missing_images"]:
        report.append("")
        report.append("## ❌ PARTNERS SEM IMAGENS")
        high_priority = [
            p for p in recommendations["missing_images"] if p["priority"] == "high"
        ]
        medium_priority = [
            p for p in recommendations["missing_images"] if p["priority"] == "medium"
        ]

        if high_priority:
            report.append("")
            report.append("### 🔴 Alta Prioridade")
            for partner in high_priority:
                report.append(
                    f"- **{partner['partner_name']}** ({partner['partner_id']}) - {partner['category']}"
                )

        if medium_priority:
            report.append("")
            report.append("### 🟡 Média Prioridade")
            for partner in medium_priority:
                report.append(
                    f"- **{partner['partner_name']}** ({partner['partner_id']}) - {partner['category']}"
                )

    # Recomendações de implementação
    report.append("")
    report.append("## 💡 RECOMENDAÇÕES DE IMPLEMENTAÇÃO")
    report.append("")
    report.append("### 1. Organização de Arquivos")
    report.append("- Manter estrutura atual: `/data/firestore_export/partners_images/`")
    report.append("- Seguir convenção de nomenclatura rigorosamente")
    report.append("- Criar subpastas por categoria se necessário")
    report.append("")
    report.append("### 2. Otimização de Imagens")
    report.append("- Comprimir imagens para web (WEBP quando possível)")
    report.append("- Manter logos em PNG/SVG para transparência")
    report.append("- Redimensionar para tamanhos recomendados")
    report.append("")
    report.append("### 3. Backup e Versionamento")
    report.append("- Fazer backup das imagens originais")
    report.append("- Versionar imagens quando houver atualizações")
    report.append("- Documentar alterações")
    report.append("")
    report.append("### 4. Integração com Sistema")
    report.append("- Criar endpoint para servir imagens")
    report.append("- Implementar cache para otimização")
    report.append("- Adicionar fallback para imagens não encontradas")

    return "\n".join(report)


def main():
    """Função principal"""
    print("🔍 ANALISANDO ESTRUTURA DE IMAGENS DOS PARCEIROS")
    print("=" * 55)

    # Caminhos
    base_dir = Path(__file__).parent.parent.parent
    json_file = (
        base_dir / "data" / "firestore_export" / "firestore_employees_partners.json"
    )
    images_dir = base_dir / "data" / "firestore_export" / "partners_images"

    print(f"📁 Arquivo JSON: {json_file}")
    print(f"📁 Diretório de imagens: {images_dir}")
    print()

    # Carrega dados
    print("📊 Carregando dados dos partners...")
    data = load_partners_data(json_file)
    if not data:
        return

    # Extrai informações dos partners
    partners = extract_partners_info(data)
    print(f"✅ {len(partners)} partners encontrados")

    # Analisa imagens existentes
    print("🖼️ Analisando imagens existentes...")
    existing_images = analyze_existing_images(images_dir)
    print(f"✅ {len(existing_images)} partners com imagens")

    # Gera recomendações
    print("💡 Gerando recomendações...")
    recommendations = generate_recommendations(partners, existing_images)

    # Gera relatório
    print("📄 Gerando relatório...")
    report = generate_report(partners, existing_images, recommendations)

    # Salva relatório
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = base_dir / "docs" / f"analise_imagens_parceiros_{timestamp}.md"

    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"📄 Relatório salvo: {report_file}")
    print()
    print("🎉 ANÁLISE CONCLUÍDA!")

    # Mostra resumo
    print("\n📋 RESUMO EXECUTIVO:")
    print(f"- Partners ativos: {len([p for p in partners if p['active']])}")
    print(f"- Com imagens: {len(existing_images)}")
    print(f"- Sem imagens: {len(recommendations['missing_images'])}")
    print(
        f"- Cobertura geral: {(len(existing_images) / len([p for p in partners if p['active']]) * 100):.1f}%"
    )


if __name__ == "__main__":
    main()
