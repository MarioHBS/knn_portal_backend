#!/usr/bin/env python3
"""
Script para arquivar relatórios antigos

Este script move relatórios com mais de 30 dias do diretório /reports/
para o diretório /docs/archive/ para manter a organização.

Autor: Sistema de Manutenção
Data: 2025-08-09
"""

import shutil
from datetime import datetime, timedelta
from pathlib import Path


def archive_old_reports(days_threshold: int = 30):
    """
    Move relatórios antigos para o diretório de arquivo

    Args:
        days_threshold: Número de dias para considerar um relatório como antigo
    """
    # Diretórios
    reports_dir = Path(
        "p:/ProjectsWEB/PRODUCAO/KNN PROJECT/knn_portal_journey_club_backend/reports"
    )
    archive_dir = Path(
        "p:/ProjectsWEB/PRODUCAO/KNN PROJECT/knn_portal_journey_club_backend/docs/archive"
    )

    # Criar diretório de arquivo se não existir
    archive_dir.mkdir(parents=True, exist_ok=True)

    # Data limite
    cutoff_date = datetime.now() - timedelta(days=days_threshold)

    # Contadores
    moved_count = 0
    total_count = 0

    print(f"🗂️  Arquivando relatórios com mais de {days_threshold} dias...")
    print(f"📅 Data limite: {cutoff_date.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📁 Origem: {reports_dir}")
    print(f"📁 Destino: {archive_dir}")
    print("-" * 60)

    # Verificar se o diretório de relatórios existe
    if not reports_dir.exists():
        print(f"❌ Diretório de relatórios não encontrado: {reports_dir}")
        return

    # Processar arquivos de relatório
    for file_path in reports_dir.iterdir():
        if file_path.is_file() and (
            file_path.suffix in [".md", ".json", ".txt", ".html"]
            and any(
                keyword in file_path.name.lower()
                for keyword in ["report", "relatorio", "migration", "test_", "upload_"]
            )
        ):
            total_count += 1

            # Verificar data de modificação
            file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)

            if file_mtime < cutoff_date:
                try:
                    # Mover arquivo para o diretório de arquivo
                    destination = archive_dir / file_path.name

                    # Se arquivo já existe no destino, adicionar timestamp
                    if destination.exists():
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        stem = destination.stem
                        suffix = destination.suffix
                        destination = archive_dir / f"{stem}_{timestamp}{suffix}"

                    shutil.move(str(file_path), str(destination))
                    moved_count += 1

                    print(f"✅ Movido: {file_path.name} -> {destination.name}")

                except Exception as e:
                    print(f"❌ Erro ao mover {file_path.name}: {e}")
            else:
                print(
                    f"⏭️  Mantido: {file_path.name} (modificado em {file_mtime.strftime('%Y-%m-%d')})"
                )

    print("-" * 60)
    print("📊 Resumo:")
    print(f"   • Total de relatórios encontrados: {total_count}")
    print(f"   • Relatórios arquivados: {moved_count}")
    print(f"   • Relatórios mantidos: {total_count - moved_count}")

    if moved_count > 0:
        print(
            f"\n✨ Arquivamento concluído! {moved_count} relatórios foram movidos para {archive_dir}"
        )
    else:
        print("\n💡 Nenhum relatório antigo encontrado para arquivar.")


def main():
    """
    Função principal
    """
    print("🗃️  Script de Arquivamento de Relatórios")
    print("=" * 60)

    try:
        archive_old_reports()
    except KeyboardInterrupt:
        print("\n⚠️  Operação cancelada pelo usuário.")
    except Exception as e:
        print(f"\n❌ Erro durante o arquivamento: {e}")


if __name__ == "__main__":
    main()
