#!/usr/bin/env python3
"""Script para limpeza automática de códigos de validação expirados.

Este script deve ser executado periodicamente (ex: a cada 5 minutos) para
remover códigos de validação que expiraram há mais de 3 minutos.

Uso:
    python scripts/maintenance/cleanup_expired_codes.py
"""

import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Adicionar o diretório raiz ao path para importar módulos
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.db import firestore_client, postgres_client
from src.utils import logger


async def cleanup_expired_validation_codes():
    """Remove códigos de validação expirados do banco de dados."""
    try:
        # Calcular timestamp de corte (códigos expirados há mais de 3 minutos)
        cutoff_time = datetime.now() - timedelta(minutes=3)
        cutoff_iso = cutoff_time.isoformat()

        logger.info(f"Iniciando limpeza de códigos expirados antes de {cutoff_iso}")

        # Buscar códigos expirados no Firestore
        try:
            expired_codes_firestore = await firestore_client.query_documents(
                "validation_codes",
                filters=[
                    ("expires", "<", cutoff_iso),
                ],
                limit=1000,  # Processar em lotes
            )

            firestore_count = 0
            if expired_codes_firestore.get("items"):
                for code in expired_codes_firestore["items"]:
                    try:
                        await firestore_client.delete_document(
                            "validation_codes", code["id"]
                        )
                        firestore_count += 1
                    except Exception as e:
                        logger.warning(
                            f"Erro ao deletar código {code['id']} do Firestore: {e}"
                        )

            logger.info(f"Removidos {firestore_count} códigos expirados do Firestore")

        except Exception as e:
            logger.error(f"Erro ao limpar códigos do Firestore: {e}")

        # Buscar códigos expirados no PostgreSQL
        try:
            expired_codes_postgres = await postgres_client.query_documents(
                "validation_codes",
                filters=[
                    ("expires", "<", cutoff_iso),
                ],
                limit=1000,  # Processar em lotes
            )

            postgres_count = 0
            if expired_codes_postgres.get("items"):
                for code in expired_codes_postgres["items"]:
                    try:
                        await postgres_client.delete_document(
                            "validation_codes", code["id"]
                        )
                        postgres_count += 1
                    except Exception as e:
                        logger.warning(
                            f"Erro ao deletar código {code['id']} do PostgreSQL: {e}"
                        )

            logger.info(f"Removidos {postgres_count} códigos expirados do PostgreSQL")

        except Exception as e:
            logger.error(f"Erro ao limpar códigos do PostgreSQL: {e}")

        total_cleaned = firestore_count + postgres_count
        logger.info(f"Limpeza concluída. Total de códigos removidos: {total_cleaned}")

        return total_cleaned

    except Exception as e:
        logger.error(f"Erro durante limpeza de códigos expirados: {e}")
        raise


async def cleanup_old_redemptions():
    """Remove registros de resgate antigos (mais de 30 dias)."""
    try:
        # Calcular timestamp de corte (30 dias atrás)
        cutoff_time = datetime.now() - timedelta(days=30)
        cutoff_iso = cutoff_time.isoformat()

        logger.info(f"Iniciando limpeza de resgates antigos antes de {cutoff_iso}")

        # Buscar resgates antigos no Firestore
        try:
            old_redemptions_firestore = await firestore_client.query_documents(
                "redemptions",
                filters=[
                    ("redeemed_at", "<", cutoff_iso),
                ],
                limit=1000,  # Processar em lotes
            )

            firestore_count = 0
            if old_redemptions_firestore.get("items"):
                for redemption in old_redemptions_firestore["items"]:
                    try:
                        await firestore_client.delete_document(
                            "redemptions", redemption["id"]
                        )
                        firestore_count += 1
                    except Exception as e:
                        logger.warning(
                            f"Erro ao deletar resgate {redemption['id']} do Firestore: {e}"
                        )

            logger.info(f"Removidos {firestore_count} resgates antigos do Firestore")

        except Exception as e:
            logger.error(f"Erro ao limpar resgates do Firestore: {e}")

        # Buscar resgates antigos no PostgreSQL
        try:
            old_redemptions_postgres = await postgres_client.query_documents(
                "redemptions",
                filters=[
                    ("redeemed_at", "<", cutoff_iso),
                ],
                limit=1000,  # Processar em lotes
            )

            postgres_count = 0
            if old_redemptions_postgres.get("items"):
                for redemption in old_redemptions_postgres["items"]:
                    try:
                        await postgres_client.delete_document(
                            "redemptions", redemption["id"]
                        )
                        postgres_count += 1
                    except Exception as e:
                        logger.warning(
                            f"Erro ao deletar resgate {redemption['id']} do PostgreSQL: {e}"
                        )

            logger.info(f"Removidos {postgres_count} resgates antigos do PostgreSQL")

        except Exception as e:
            logger.error(f"Erro ao limpar resgates do PostgreSQL: {e}")

        total_cleaned = firestore_count + postgres_count
        logger.info(f"Limpeza de resgates concluída. Total removidos: {total_cleaned}")

        return total_cleaned

    except Exception as e:
        logger.error(f"Erro durante limpeza de resgates antigos: {e}")
        raise


async def main():
    """Função principal do script de limpeza."""
    try:
        logger.info("=== Iniciando script de limpeza automática ===")

        # Limpar códigos expirados
        codes_cleaned = await cleanup_expired_validation_codes()

        # Limpar resgates antigos (opcional, executar menos frequentemente)
        redemptions_cleaned = await cleanup_old_redemptions()

        logger.info(
            f"=== Limpeza concluída: {codes_cleaned} códigos, {redemptions_cleaned} resgates ==="
        )

    except Exception as e:
        logger.error(f"Erro durante execução do script de limpeza: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
