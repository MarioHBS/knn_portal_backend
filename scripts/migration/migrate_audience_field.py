#!/usr/bin/env python3
"""
Script de migração para converter o campo target_profile para audience nas promoções.

Este script:
1. Busca todas as promoções existentes
2. Converte target_profile para audience (List[str])
3. Atualiza os documentos no banco de dados

Mapeamento:
- "student" -> ["student"]
- "employee" -> ["employee"]
- "both" -> ["student", "employee"]
"""

import asyncio
import os
import sys
from datetime import datetime

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.db import firestore_client, postgres_client
from src.utils import logger


class AudienceMigration:
    """Classe para gerenciar a migração do campo audience."""

    def __init__(self):
        self.migrated_count = 0
        self.error_count = 0
        self.skipped_count = 0

    def convert_target_profile_to_audience(self, target_profile: str) -> list[str]:
        """Converte target_profile para audience."""
        mapping = {
            "student": ["student"],
            "employee": ["employee"],
            "both": ["student", "employee"],
        }
        return mapping.get(target_profile, ["student", "employee"])  # Default para both

    async def migrate_firestore_promotions(self) -> None:
        """Migra promoções no Firestore."""
        try:
            logger.info("Iniciando migração das promoções no Firestore...")

            # Buscar todas as promoções
            result = await firestore_client.query_documents(
                "promotions",
                filters=[],  # Sem filtros para pegar todas
                limit=1000,  # Ajustar conforme necessário
                tenant_id="knn-benefits-tenant",  # Tenant padrão
            )

            promotions = result.get("items", [])
            logger.info(f"Encontradas {len(promotions)} promoções para migrar")

            for promotion in promotions:
                try:
                    promotion_id = promotion.get("id")
                    target_profile = promotion.get("target_profile")

                    # Verificar se já tem o campo audience
                    if "audience" in promotion:
                        logger.info(
                            f"Promoção {promotion_id} já possui campo audience, pulando..."
                        )
                        self.skipped_count += 1
                        continue

                    # Verificar se tem target_profile
                    if not target_profile:
                        logger.warning(
                            f"Promoção {promotion_id} não possui target_profile, usando padrão [student, employee]"
                        )
                        audience = ["student", "employee"]
                    else:
                        audience = self.convert_target_profile_to_audience(
                            target_profile
                        )

                    # Atualizar documento
                    update_data = {
                        "audience": audience,
                        "migrated_at": datetime.now().isoformat(),
                    }

                    # Remover target_profile se existir
                    if target_profile:
                        update_data["target_profile"] = None

                    await firestore_client.update_document(
                        "promotions", promotion_id, update_data
                    )

                    logger.info(
                        f"Migrada promoção {promotion_id}: {target_profile} -> {audience}"
                    )
                    self.migrated_count += 1

                except Exception as e:
                    logger.error(
                        f"Erro ao migrar promoção {promotion.get('id', 'unknown')}: {str(e)}"
                    )
                    self.error_count += 1

            logger.info(
                f"Migração Firestore concluída: {self.migrated_count} migradas, {self.skipped_count} puladas, {self.error_count} erros"
            )

        except Exception as e:
            logger.error(f"Erro geral na migração Firestore: {str(e)}")

    async def migrate_postgres_promotions(self) -> None:
        """Migra promoções no PostgreSQL."""
        try:
            logger.info("Iniciando migração das promoções no PostgreSQL...")

            # Buscar todas as promoções
            result = await postgres_client.query_documents(
                "promotions",
                filters=[],  # Sem filtros para pegar todas
                limit=1000,  # Ajustar conforme necessário
                tenant_id="knn-benefits-tenant",  # Tenant padrão
            )

            promotions = result.get("items", [])
            logger.info(
                f"Encontradas {len(promotions)} promoções para migrar no PostgreSQL"
            )

            for promotion in promotions:
                try:
                    promotion_id = promotion.get("id")
                    target_profile = promotion.get("target_profile")

                    # Verificar se já tem o campo audience
                    if "audience" in promotion and promotion["audience"]:
                        logger.info(
                            f"Promoção {promotion_id} já possui campo audience, pulando..."
                        )
                        self.skipped_count += 1
                        continue

                    # Verificar se tem target_profile
                    if not target_profile:
                        logger.warning(
                            f"Promoção {promotion_id} não possui target_profile, usando padrão [student, employee]"
                        )
                        audience = ["student", "employee"]
                    else:
                        audience = self.convert_target_profile_to_audience(
                            target_profile
                        )

                    # Atualizar documento
                    update_data = {
                        "audience": audience,
                        "migrated_at": datetime.now().isoformat(),
                    }

                    await postgres_client.update_document(
                        "promotions", promotion_id, update_data
                    )

                    logger.info(
                        f"Migrada promoção PostgreSQL {promotion_id}: {target_profile} -> {audience}"
                    )
                    self.migrated_count += 1

                except Exception as e:
                    logger.error(
                        f"Erro ao migrar promoção PostgreSQL {promotion.get('id', 'unknown')}: {str(e)}"
                    )
                    self.error_count += 1

            logger.info(
                f"Migração PostgreSQL concluída: {self.migrated_count} migradas, {self.skipped_count} puladas, {self.error_count} erros"
            )

        except Exception as e:
            logger.error(f"Erro geral na migração PostgreSQL: {str(e)}")

    async def run_migration(self) -> None:
        """Executa a migração completa."""
        logger.info("=== INICIANDO MIGRAÇÃO DO CAMPO AUDIENCE ===")
        start_time = datetime.now()

        try:
            # Migrar Firestore
            await self.migrate_firestore_promotions()

            # Migrar PostgreSQL
            await self.migrate_postgres_promotions()

        except Exception as e:
            logger.error(f"Erro durante a migração: {str(e)}")

        end_time = datetime.now()
        duration = end_time - start_time

        logger.info("=== MIGRAÇÃO CONCLUÍDA ===")
        logger.info(f"Tempo total: {duration}")
        logger.info(f"Total migradas: {self.migrated_count}")
        logger.info(f"Total puladas: {self.skipped_count}")
        logger.info(f"Total com erro: {self.error_count}")

        if self.error_count > 0:
            logger.warning(
                f"Migração concluída com {self.error_count} erros. Verifique os logs."
            )
        else:
            logger.info("Migração concluída com sucesso!")


async def main():
    """Função principal."""
    migration = AudienceMigration()
    await migration.run_migration()


if __name__ == "__main__":
    asyncio.run(main())
