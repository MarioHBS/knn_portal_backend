#!/usr/bin/env python3
"""
Exemplo de uso das funcionalidades de múltiplos bancos Firestore.

Este script demonstra como:
1. Usar o banco principal configurado
2. Acessar bancos específicos
3. Listar bancos disponíveis
4. Alternar entre bancos

Configuração necessária no .env:
FIRESTORE_PROJECT=knn-benefits
FIRESTORE_DATABASES=["(default)","knn-benefits"]
FIRESTORE_DATABASE=0
"""

import os
import sys

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.config import (
    CURRENT_FIRESTORE_DATABASE,
    FIRESTORE_DATABASE,
    FIRESTORE_DATABASES_LIST,
    FIRESTORE_PROJECT,
)
from src.db.firestore import (
    databases,
    db,  # Banco principal
    get_current_database_name,
    get_database,
    list_available_databases,
)
from src.utils import logger


def demonstrate_multi_database_usage():
    """Demonstra o uso de múltiplos bancos Firestore."""

    logger.info("=== Demonstração de Múltiplos Bancos Firestore ===")

    # 1. Mostrar configurações atuais
    logger.info(f"Projeto Firestore: {FIRESTORE_PROJECT}")
    logger.info(f"Bancos configurados: {FIRESTORE_DATABASES_LIST}")
    logger.info(f"Índice do banco principal: {FIRESTORE_DATABASE}")
    logger.info(f"Nome do banco principal: {CURRENT_FIRESTORE_DATABASE}")

    # 2. Listar bancos disponíveis
    available_dbs = list_available_databases()
    logger.info(f"Bancos disponíveis: {available_dbs}")

    # 3. Usar o banco principal
    logger.info("\n=== Usando Banco Principal ===")
    if db:
        logger.info(f"Banco principal conectado: {get_current_database_name()}")
        # Exemplo de operação no banco principal
        try:
            collections = db.collections()
            logger.info("Coleções no banco principal:")
            for collection in collections:
                logger.info(f"  - {collection.id}")
        except Exception as e:
            logger.warning(f"Erro ao listar coleções: {e}")
    else:
        logger.error("Banco principal não está conectado")

    # 4. Acessar bancos específicos
    logger.info("\n=== Acessando Bancos Específicos ===")
    for db_name in available_dbs:
        logger.info(f"\nTestando banco: {db_name}")
        specific_db = get_database(db_name)
        if specific_db:
            logger.info(f"  ✓ Conexão estabelecida com {db_name}")
            try:
                # Teste simples de conectividade
                collections = specific_db.collections()
                collection_count = len(list(collections))
                logger.info(f"  ✓ {collection_count} coleções encontradas")
            except Exception as e:
                logger.warning(f"  ⚠ Erro ao acessar {db_name}: {e}")
        else:
            logger.error(f"  ✗ Falha ao conectar com {db_name}")

    # 5. Demonstrar uso em operações CRUD
    logger.info("\n=== Exemplo de Operações CRUD ===")

    # Usando banco principal
    main_db = get_database()  # None = banco principal
    logger.info(f"Operações no banco principal: {get_current_database_name()}")

    # Usando banco específico
    if "knn-benefits" in available_dbs:
        benefits_db = get_database("knn-benefits")
        logger.info("Operações no banco knn-benefits")

    # 6. Mostrar estatísticas
    logger.info("\n=== Estatísticas ===")
    logger.info(f"Total de bancos configurados: {len(FIRESTORE_DATABASES_LIST)}")
    logger.info(f"Total de bancos conectados: {len(databases)}")
    logger.info(f"Banco ativo: {get_current_database_name()}")

    return True


def test_database_switching():
    """Testa a alternância entre bancos."""

    logger.info("\n=== Teste de Alternância de Bancos ===")

    available_dbs = list_available_databases()

    for db_name in available_dbs:
        logger.info(f"\nTestando operações no banco: {db_name}")

        # Obter conexão específica
        test_db = get_database(db_name)

        if test_db:
            try:
                # Teste de leitura
                collections = list(test_db.collections())
                logger.info(f"  ✓ Leitura bem-sucedida: {len(collections)} coleções")

                # Teste de escrita (coleção de teste)
                test_collection = test_db.collection("_test_connection")
                test_doc = test_collection.document("test")

                # Tentar escrever um documento de teste
                test_doc.set(
                    {
                        "timestamp": firestore.SERVER_TIMESTAMP,
                        "database": db_name,
                        "test": True,
                    }
                )
                logger.info(f"  ✓ Escrita bem-sucedida no banco {db_name}")

                # Limpar documento de teste
                test_doc.delete()
                logger.info(f"  ✓ Limpeza bem-sucedida no banco {db_name}")

            except Exception as e:
                logger.error(f"  ✗ Erro no banco {db_name}: {e}")
        else:
            logger.error(f"  ✗ Não foi possível conectar ao banco {db_name}")


if __name__ == "__main__":
    try:
        # Executar demonstração
        demonstrate_multi_database_usage()

        # Executar testes de alternância
        test_database_switching()

        logger.info("\n=== Demonstração Concluída ===")

    except Exception as e:
        logger.error(f"Erro durante a demonstração: {e}")
        sys.exit(1)
