"""Exemplos de uso do sistema de banco de dados unificado.

Este arquivo demonstra como usar o UnifiedDatabaseClient,
QueryBuilder e sistema de tratamento de erros.
"""

import asyncio
from datetime import datetime, timedelta

from src.db.error_handler import ErrorHandler, RetryConfig, with_error_handling
from src.db.query_builder import QueryBuilder, SearchHelper
from src.db.unified_client import unified_client
from src.utils import logger


async def exemplo_crud_basico():
    """Demonstra operações CRUD básicas."""
    tenant_id = "exemplo_tenant"
    collection = "usuarios"

    try:
        # Criar documento
        novo_usuario = {
            "nome": "João Silva",
            "email": "joao@exemplo.com",
            "idade": 30,
            "ativo": True,
            "created_at": datetime.now(),
        }

        logger.info("Criando novo usuário...")
        doc_id = await unified_client.create_document(
            collection, novo_usuario, tenant_id
        )
        logger.info(f"Usuário criado com ID: {doc_id}")

        # Ler documento
        logger.info("Buscando usuário criado...")
        usuario = await unified_client.get_document(collection, doc_id, tenant_id)
        logger.info(f"Usuário encontrado: {usuario['nome']}")

        # Atualizar documento
        logger.info("Atualizando usuário...")
        await unified_client.update_document(
            collection, doc_id, {"idade": 31, "updated_at": datetime.now()}, tenant_id
        )
        logger.info("Usuário atualizado com sucesso")

        # Deletar documento
        logger.info("Deletando usuário...")
        await unified_client.delete_document(collection, doc_id, tenant_id)
        logger.info("Usuário deletado com sucesso")

    except Exception as e:
        logger.error(f"Erro no exemplo CRUD: {e}")


async def exemplo_queries_avancadas():
    """Demonstra queries avançadas usando o unified_client."""
    tenant_id = "exemplo_tenant"
    collection = "produtos"

    try:
        # Criar alguns produtos de exemplo
        produtos = [
            {
                "nome": "Notebook Dell",
                "categoria": "eletrônicos",
                "preco": 2500.00,
                "estoque": 10,
                "ativo": True,
            },
            {
                "nome": "Mouse Logitech",
                "categoria": "eletrônicos",
                "preco": 150.00,
                "estoque": 50,
                "ativo": True,
            },
            {
                "nome": "Cadeira Gamer",
                "categoria": "móveis",
                "preco": 800.00,
                "estoque": 5,
                "ativo": False,
            },
        ]

        logger.info("Criando produtos de exemplo...")
        for produto in produtos:
            await unified_client.create_document(collection, produto, tenant_id)

        # Query com filtros
        logger.info("Buscando produtos eletrônicos ativos...")
        filtros = [
            ("categoria", "==", "eletrônicos"),
            ("ativo", "==", True),
            ("preco", "<", 2000.00),
        ]

        resultado = await unified_client.query_documents(
            collection=collection,
            tenant_id=tenant_id,
            filters=filtros,
            order_by=[("preco", "asc")],
            limit=10,
        )

        logger.info(f"Encontrados {len(resultado['data'])} produtos")
        for produto in resultado["data"]:
            logger.info(f"  - {produto['nome']}: R$ {produto['preco']}")

    except Exception as e:
        logger.error(f"Erro nas queries avançadas: {e}")


async def exemplo_query_builder():
    """Demonstra o uso do QueryBuilder."""
    tenant_id = "exemplo_tenant"
    collection = "pedidos"

    try:
        # Criar alguns pedidos de exemplo
        pedidos = [
            {
                "cliente_id": "cliente_1",
                "valor_total": 350.00,
                "status": "pendente",
                "created_at": datetime.now() - timedelta(days=1),
            },
            {
                "cliente_id": "cliente_2",
                "valor_total": 1200.00,
                "status": "concluído",
                "created_at": datetime.now() - timedelta(days=3),
            },
            {
                "cliente_id": "cliente_1",
                "valor_total": 750.00,
                "status": "cancelado",
                "created_at": datetime.now() - timedelta(days=5),
            },
        ]

        logger.info("Criando pedidos de exemplo...")
        for pedido in pedidos:
            await unified_client.create_document(collection, pedido, tenant_id)

        # Usando QueryBuilder
        logger.info("Buscando pedidos com QueryBuilder...")
        query = (
            QueryBuilder(collection, tenant_id)
            .where("valor_total", ">=", 500.00)
            .where_in("status", ["pendente", "concluído"])
            .order_by_created_at("desc")
            .limit(5)
        )

        resultados = await query.get()
        logger.info(f"Encontrados {len(resultados)} pedidos")

        for pedido in resultados:
            logger.info(
                f"  - Cliente: {pedido['cliente_id']}, "
                f"Valor: R$ {pedido['valor_total']}, "
                f"Status: {pedido['status']}"
            )

        # Usando SearchHelper
        logger.info("Buscando pedidos recentes...")
        pedidos_recentes = await SearchHelper.find_recent(
            collection, tenant_id, days=7, limit=10
        )

        logger.info(f"Pedidos recentes: {len(pedidos_recentes)}")

    except Exception as e:
        logger.error(f"Erro no exemplo QueryBuilder: {e}")


@with_error_handling(operation_name="operacao_com_retry")
async def operacao_com_retry():
    """Exemplo de operação com retry automático."""
    # Simula uma operação que pode falhar
    import random

    if random.random() < 0.7:  # 70% de chance de falhar
        raise Exception("Erro simulado para demonstrar retry")

    return "Operação bem-sucedida!"


async def exemplo_tratamento_erros():
    """Demonstra o sistema de tratamento de erros."""
    try:
        logger.info("Testando operação com retry...")
        resultado = await operacao_com_retry()
        logger.info(f"Resultado: {resultado}")

    except Exception as e:
        logger.error(f"Operação falhou após todas as tentativas: {e}")

    # Exemplo de configuração personalizada de retry
    config_agressiva = RetryConfig(
        max_attempts=5, base_delay=0.5, max_delay=10.0, exponential_base=1.5
    )

    try:
        logger.info("Testando com configuração agressiva de retry...")
        resultado = await ErrorHandler.retry_with_backoff(
            operacao_com_retry, config_agressiva
        )
        logger.info(f"Resultado: {resultado}")

    except Exception as e:
        logger.error(f"Operação falhou: {e}")


async def exemplo_operacoes_lote():
    """Demonstra operações em lote."""
    tenant_id = "exemplo_tenant"
    collection = "categorias"

    try:
        # Preparar operações em lote
        operacoes = [
            {
                "operation": "create",
                "collection": collection,
                "data": {"nome": "Eletrônicos", "ativo": True},
                "tenant_id": tenant_id,
            },
            {
                "operation": "create",
                "collection": collection,
                "data": {"nome": "Roupas", "ativo": True},
                "tenant_id": tenant_id,
            },
            {
                "operation": "create",
                "collection": collection,
                "data": {"nome": "Casa e Jardim", "ativo": False},
                "tenant_id": tenant_id,
            },
        ]

        logger.info("Executando operações em lote...")
        resultados = await unified_client.batch_operation(operacoes)

        logger.info(f"Operações executadas: {len(resultados)}")
        for i, resultado in enumerate(resultados):
            if resultado["success"]:
                logger.info(f"  Operação {i+1}: Sucesso - ID: {resultado['id']}")
            else:
                logger.error(f"  Operação {i+1}: Erro - {resultado['error']}")

    except Exception as e:
        logger.error(f"Erro nas operações em lote: {e}")


async def exemplo_paginacao():
    """Demonstra paginação de resultados."""
    tenant_id = "exemplo_tenant"
    collection = "usuarios"

    try:
        # Criar vários usuários para demonstrar paginação
        logger.info("Criando usuários para paginação...")
        for i in range(25):
            usuario = {
                "nome": f"Usuário {i+1:02d}",
                "email": f"usuario{i+1:02d}@exemplo.com",
                "created_at": datetime.now(),
            }
            await unified_client.create_document(collection, usuario, tenant_id)

        # Paginar resultados
        logger.info("Demonstrando paginação...")
        page_size = 10
        page = 0

        while True:
            offset = page * page_size

            resultado = await unified_client.query_documents(
                collection=collection,
                tenant_id=tenant_id,
                order_by=[("nome", "asc")],
                limit=page_size,
                offset=offset,
            )

            if not resultado["data"]:
                break

            logger.info(f"Página {page + 1}: {len(resultado['data'])} usuários")
            for usuario in resultado["data"]:
                logger.info(f"  - {usuario['nome']}")

            page += 1

            # Evitar loop infinito em exemplo
            if page >= 3:
                break

    except Exception as e:
        logger.error(f"Erro na paginação: {e}")


async def main():
    """Função principal que executa todos os exemplos."""
    logger.info("=== Iniciando exemplos de uso do sistema de banco de dados ===")

    logger.info("\n1. Exemplo CRUD Básico")
    await exemplo_crud_basico()

    logger.info("\n2. Exemplo Queries Avançadas")
    await exemplo_queries_avancadas()

    logger.info("\n3. Exemplo QueryBuilder")
    await exemplo_query_builder()

    logger.info("\n4. Exemplo Tratamento de Erros")
    await exemplo_tratamento_erros()

    logger.info("\n5. Exemplo Operações em Lote")
    await exemplo_operacoes_lote()

    logger.info("\n6. Exemplo Paginação")
    await exemplo_paginacao()

    logger.info("\n=== Exemplos concluídos ===")


if __name__ == "__main__":
    asyncio.run(main())
