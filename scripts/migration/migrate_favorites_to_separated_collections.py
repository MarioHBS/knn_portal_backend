#!/usr/bin/env python3
"""
Script de migração para converter favoritos da coleção única 'favorites'
para coleções separadas 'students_fav' e 'employees_fav'.

Este script:
1. Lê todos os documentos da coleção 'favorites'
2. Agrupa os favoritos por student_id e employee_id
3. Cria documentos nas novas coleções students_fav e employees_fav
4. Opcionalmente remove a coleção antiga após confirmação

Uso:
    python scripts/migration/migrate_favorites_to_separated_collections.py [--dry-run] [--remove-old]

Argumentos:
    --dry-run: Executa sem fazer alterações, apenas mostra o que seria feito
    --remove-old: Remove a coleção 'favorites' após a migração (requer confirmação)
"""

import argparse
import asyncio
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

# Adicionar o diretório raiz ao path para importar módulos do projeto
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.db import firestore_client
from src.utils import logger


class FavoritesMigrator:
    """Classe responsável pela migração dos favoritos."""

    def __init__(self, dry_run: bool = False):
        """
        Inicializa o migrador.

        Args:
            dry_run: Se True, apenas simula a migração sem fazer alterações
        """
        self.dry_run = dry_run
        self.stats = {
            "total_favorites": 0,
            "students_with_favorites": 0,
            "employees_with_favorites": 0,
            "migrated_students": 0,
            "migrated_employees": 0,
            "errors": 0,
        }

    async def get_all_favorites(self) -> list[dict[str, Any]]:
        """
        Obtém todos os documentos da coleção 'favorites'.

        Returns:
            Lista de documentos de favoritos
        """
        logger.info("Obtendo todos os favoritos da coleção 'favorites'...")

        try:
            result = await firestore_client.query_documents(
                collection="favorites",
                filters=[],
                limit=10000,  # Limite alto para pegar todos
            )

            favorites = result.get("items", [])
            self.stats["total_favorites"] = len(favorites)

            logger.info(f"Encontrados {len(favorites)} favoritos na coleção original")
            return favorites

        except Exception as e:
            logger.error(f"Erro ao obter favoritos: {e}")
            raise

    def group_favorites_by_user(
        self, favorites: list[dict[str, Any]]
    ) -> tuple[dict, dict]:
        """
        Agrupa os favoritos por student_id e employee_id.

        Args:
            favorites: Lista de documentos de favoritos

        Returns:
            Tupla com (students_favorites, employees_favorites)
        """
        students_favorites = defaultdict(list)
        employees_favorites = defaultdict(list)

        for favorite in favorites:
            student_id = favorite.get("student_id")
            employee_id = favorite.get("employee_id")
            partner_id = favorite.get("partner_id")

            if not partner_id:
                logger.warning(
                    f"Favorito sem partner_id encontrado: {favorite.get('id')}"
                )
                continue

            if student_id:
                students_favorites[student_id].append(partner_id)
            elif employee_id:
                employees_favorites[employee_id].append(partner_id)
            else:
                logger.warning(
                    f"Favorito sem student_id nem employee_id: {favorite.get('id')}"
                )

        self.stats["students_with_favorites"] = len(students_favorites)
        self.stats["employees_with_favorites"] = len(employees_favorites)

        logger.info(
            f"Agrupados favoritos para {len(students_favorites)} estudantes e {len(employees_favorites)} funcionários"
        )

        return dict(students_favorites), dict(employees_favorites)

    async def migrate_students_favorites(
        self, students_favorites: dict[str, list[str]]
    ) -> None:
        """
        Migra os favoritos dos estudantes para a coleção students_fav.

        Args:
            students_favorites: Dicionário com student_id -> lista de partner_ids
        """
        logger.info(f"Migrando favoritos de {len(students_favorites)} estudantes...")

        for student_id, partner_ids in students_favorites.items():
            try:
                # Remover duplicatas e manter ordem
                unique_partner_ids = list(dict.fromkeys(partner_ids))

                document_data = {
                    "id": student_id,
                    "favorites": unique_partner_ids,
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                }

                if self.dry_run:
                    logger.info(
                        f"[DRY-RUN] Criaria documento students_fav/{student_id} com {len(unique_partner_ids)} favoritos"
                    )
                else:
                    await firestore_client.create_document(
                        collection="students_fav",
                        data=document_data,
                        document_id=student_id,
                    )
                    logger.info(
                        f"Migrado estudante {student_id} com {len(unique_partner_ids)} favoritos"
                    )

                self.stats["migrated_students"] += 1

            except Exception as e:
                logger.error(f"Erro ao migrar favoritos do estudante {student_id}: {e}")
                self.stats["errors"] += 1

    async def migrate_employees_favorites(
        self, employees_favorites: dict[str, list[str]]
    ) -> None:
        """
        Migra os favoritos dos funcionários para a coleção employees_fav.

        Args:
            employees_favorites: Dicionário com employee_id -> lista de partner_ids
        """
        logger.info(f"Migrando favoritos de {len(employees_favorites)} funcionários...")

        for employee_id, partner_ids in employees_favorites.items():
            try:
                # Remover duplicatas e manter ordem
                unique_partner_ids = list(dict.fromkeys(partner_ids))

                document_data = {
                    "id": employee_id,
                    "favorites": unique_partner_ids,
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                }

                if self.dry_run:
                    logger.info(
                        f"[DRY-RUN] Criaria documento employees_fav/{employee_id} com {len(unique_partner_ids)} favoritos"
                    )
                else:
                    await firestore_client.create_document(
                        collection="employees_fav",
                        data=document_data,
                        document_id=employee_id,
                    )
                    logger.info(
                        f"Migrado funcionário {employee_id} com {len(unique_partner_ids)} favoritos"
                    )

                self.stats["migrated_employees"] += 1

            except Exception as e:
                logger.error(
                    f"Erro ao migrar favoritos do funcionário {employee_id}: {e}"
                )
                self.stats["errors"] += 1

    async def remove_old_collection(self) -> None:
        """
        Remove a coleção 'favorites' antiga após confirmação.

        ATENÇÃO: Esta operação é irreversível!
        """
        if self.dry_run:
            logger.info("[DRY-RUN] Removeria a coleção 'favorites' antiga")
            return

        print("\n" + "=" * 60)
        print("ATENÇÃO: OPERAÇÃO IRREVERSÍVEL!")
        print("=" * 60)
        print("Você está prestes a REMOVER PERMANENTEMENTE a coleção 'favorites'.")
        print("Esta operação NÃO PODE SER DESFEITA!")
        print("Certifique-se de que a migração foi bem-sucedida antes de continuar.")
        print("=" * 60)

        confirmation = input("Digite 'CONFIRMO' para prosseguir com a remoção: ")

        if confirmation != "CONFIRMO":
            logger.info("Remoção cancelada pelo usuário")
            return

        logger.warning("Iniciando remoção da coleção 'favorites'...")

        try:
            # Obter todos os documentos da coleção
            result = await firestore_client.query_documents(
                collection="favorites", filters=[], limit=10000
            )

            favorites = result.get("items", [])

            # Remover cada documento
            for favorite in favorites:
                document_id = favorite.get("id")
                if document_id:
                    await firestore_client.delete_document("favorites", document_id)

            logger.warning(
                f"Removidos {len(favorites)} documentos da coleção 'favorites'"
            )

        except Exception as e:
            logger.error(f"Erro ao remover coleção antiga: {e}")
            raise

    def print_stats(self) -> None:
        """Imprime as estatísticas da migração."""
        print("\n" + "=" * 50)
        print("ESTATÍSTICAS DA MIGRAÇÃO")
        print("=" * 50)
        print(f"Total de favoritos encontrados: {self.stats['total_favorites']}")
        print(f"Estudantes com favoritos: {self.stats['students_with_favorites']}")
        print(f"Funcionários com favoritos: {self.stats['employees_with_favorites']}")
        print(f"Estudantes migrados: {self.stats['migrated_students']}")
        print(f"Funcionários migrados: {self.stats['migrated_employees']}")
        print(f"Erros encontrados: {self.stats['errors']}")
        print("=" * 50)

    async def run_migration(self, remove_old: bool = False) -> None:
        """
        Executa a migração completa.

        Args:
            remove_old: Se True, remove a coleção antiga após a migração
        """
        try:
            logger.info("Iniciando migração de favoritos...")

            # 1. Obter todos os favoritos
            favorites = await self.get_all_favorites()

            if not favorites:
                logger.info("Nenhum favorito encontrado para migrar")
                return

            # 2. Agrupar por usuário
            students_favorites, employees_favorites = self.group_favorites_by_user(
                favorites
            )

            # 3. Migrar favoritos dos estudantes
            if students_favorites:
                await self.migrate_students_favorites(students_favorites)

            # 4. Migrar favoritos dos funcionários
            if employees_favorites:
                await self.migrate_employees_favorites(employees_favorites)

            # 5. Remover coleção antiga se solicitado
            if remove_old and not self.dry_run:
                await self.remove_old_collection()

            # 6. Imprimir estatísticas
            self.print_stats()

            if self.stats["errors"] == 0:
                logger.info("Migração concluída com sucesso!")
            else:
                logger.warning(f"Migração concluída com {self.stats['errors']} erros")

        except Exception as e:
            logger.error(f"Erro durante a migração: {e}")
            raise


async def main():
    """Função principal do script."""
    parser = argparse.ArgumentParser(
        description="Migra favoritos para coleções separadas",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Executa sem fazer alterações, apenas mostra o que seria feito",
    )

    parser.add_argument(
        "--remove-old",
        action="store_true",
        help="Remove a coleção 'favorites' após a migração (requer confirmação)",
    )

    args = parser.parse_args()

    # Configurar logging
    if args.dry_run:
        logger.info("Executando em modo DRY-RUN - nenhuma alteração será feita")

    # Executar migração
    migrator = FavoritesMigrator(dry_run=args.dry_run)
    await migrator.run_migration(remove_old=args.remove_old)


if __name__ == "__main__":
    asyncio.run(main())
