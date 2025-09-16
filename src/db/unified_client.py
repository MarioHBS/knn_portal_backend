"""Cliente unificado para acesso aos bancos de dados com circuit breaker.

Este módulo fornece uma interface unificada para operações CRUD
que funciona com Firestore (primário) e PostgreSQL (fallback).
"""

from typing import Any

from src.db.circuit_breaker import with_circuit_breaker
from src.db.error_handler import (
    DEFAULT_RETRY_CONFIG,
    validate_required_fields,
    with_error_handling,
)
from src.db.firestore import firestore_client
from src.db.postgres import postgres_client


class UnifiedDatabaseClient:
    """Cliente unificado que combina Firestore e PostgreSQL com circuit breaker."""

    @staticmethod
    @with_error_handling(DEFAULT_RETRY_CONFIG, "get_document")
    async def get_document(
        collection: str, doc_id: str, tenant_id: str
    ) -> dict[str, Any] | None:
        """Obtém um documento por ID.

        Args:
            collection: Nome da coleção/tabela
            doc_id: ID do documento
            tenant_id: ID do tenant

        Returns:
            Documento encontrado ou None
        """
        # Validações
        validate_required_fields(
            {"collection": collection, "doc_id": doc_id, "tenant_id": tenant_id},
            ["collection", "doc_id", "tenant_id"],
        )

        return await with_circuit_breaker(
            firestore_client.get_document,
            postgres_client.get_document,
            collection,
            doc_id,
            tenant_id,
        )

    @staticmethod
    @with_error_handling(DEFAULT_RETRY_CONFIG, "create_document")
    async def create_document(
        collection: str, data: dict[str, Any], tenant_id: str
    ) -> dict[str, Any]:
        """Cria um novo documento.

        Args:
            collection: Nome da coleção/tabela
            data: Dados do documento
            tenant_id: ID do tenant

        Returns:
            Documento criado com ID
        """
        # Validações
        validate_required_fields(
            {"collection": collection, "data": data, "tenant_id": tenant_id},
            ["collection", "data", "tenant_id"],
        )

        # Adicionar tenant_id aos dados
        data_with_tenant = {**data, "tenant_id": tenant_id}

        async def firestore_create():
            return await firestore_client.create_document(collection, data_with_tenant)

        async def postgres_create():
            return await postgres_client.create_document(collection, data_with_tenant)

        return await with_circuit_breaker(firestore_create, postgres_create)

    @staticmethod
    @with_error_handling(DEFAULT_RETRY_CONFIG, "update_document")
    async def update_document(
        collection: str, doc_id: str, data: dict[str, Any], tenant_id: str
    ) -> dict[str, Any]:
        """Atualiza um documento existente.

        Args:
            collection: Nome da coleção/tabela
            doc_id: ID do documento
            data: Dados para atualização
            tenant_id: ID do tenant

        Returns:
            Documento atualizado
        """
        # Validações
        validate_required_fields(
            {
                "collection": collection,
                "doc_id": doc_id,
                "data": data,
                "tenant_id": tenant_id,
            },
            ["collection", "doc_id", "data", "tenant_id"],
        )

        # Adicionar tenant_id aos dados
        data_with_tenant = {**data, "tenant_id": tenant_id}

        async def firestore_update():
            return await firestore_client.update_document(
                collection, doc_id, data_with_tenant
            )

        async def postgres_update():
            return await postgres_client.update_document(
                collection, doc_id, data_with_tenant
            )

        return await with_circuit_breaker(firestore_update, postgres_update)

    @staticmethod
    @with_error_handling(DEFAULT_RETRY_CONFIG, "delete_document")
    async def delete_document(collection: str, doc_id: str, tenant_id: str) -> bool:
        """Remove um documento.

        Args:
            collection: Nome da coleção/tabela
            doc_id: ID do documento
            tenant_id: ID do tenant

        Returns:
            True se removido com sucesso
        """
        # Validações
        validate_required_fields(
            {"collection": collection, "doc_id": doc_id, "tenant_id": tenant_id},
            ["collection", "doc_id", "tenant_id"],
        )

        async def firestore_delete():
            return await firestore_client.delete_document(collection, doc_id, tenant_id)

        async def postgres_delete():
            return await postgres_client.delete_document(collection, doc_id)

        return await with_circuit_breaker(firestore_delete, postgres_delete)

    @staticmethod
    @with_error_handling(DEFAULT_RETRY_CONFIG, "query_documents")
    async def query_documents(
        collection: str,
        *,
        tenant_id: str,
        filters: list[tuple[str, str, Any]] | None = None,
        order_by: list[tuple[str, str]] | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Consulta documentos com filtros.

        Args:
            collection: Nome da coleção/tabela
            tenant_id: ID do tenant
            filters: Lista de filtros [(campo, operador, valor)]
            order_by: Lista de ordenação [(campo, direção)]
            limit: Limite de resultados
            offset: Offset para paginação

        Returns:
            Resultado da consulta com dados e metadados
        """
        # Validações
        validate_required_fields(
            {"collection": collection, "tenant_id": tenant_id},
            ["collection", "tenant_id"],
        )

        return await with_circuit_breaker(
            firestore_client.query_documents,
            postgres_client.query_documents,
            collection,
            tenant_id,
            filters,
            order_by,
            limit,
            offset,
        )

    @staticmethod
    @with_error_handling(DEFAULT_RETRY_CONFIG, "batch_operation")
    async def batch_operation(operations: list[dict[str, Any]], tenant_id: str) -> bool:
        """Executa operações em lote.

        Args:
            operations: Lista de operações no formato:
                {
                    "type": "create" | "update" | "delete",
                    "collection": "nome_colecao",
                    "doc_id": "id_documento" (para update/delete),
                    "data": {...} (para create/update)
                }
            tenant_id: ID do tenant

        Returns:
            True se todas as operações foram executadas com sucesso
        """
        # Validações
        validate_required_fields(
            {"operations": operations, "tenant_id": tenant_id},
            ["operations", "tenant_id"],
        )

        async def firestore_batch():
            return await firestore_client.batch_operation(operations, tenant_id)

        async def postgres_batch():
            # Converter operações para formato PostgreSQL
            queries = []
            for op in operations:
                op_data = {**op.get("data", {}), "tenant_id": tenant_id}

                if op["type"] == "create":
                    fields = list(op_data.keys())
                    placeholders = [f"${i+1}" for i in range(len(fields))]
                    query = f"""
                    INSERT INTO {op["collection"]} ({', '.join(fields)})
                    VALUES ({', '.join(placeholders)})
                    """
                    queries.append(
                        {
                            "query": query,
                            "params": [op_data[field] for field in fields],
                        }
                    )

                elif op["type"] == "update":
                    set_clauses = [
                        f"{field} = ${i+2}" for i, field in enumerate(op_data.keys())
                    ]
                    query = f"""
                    UPDATE {op["collection"]}
                    SET {', '.join(set_clauses)}
                    WHERE id = $1
                    """
                    queries.append(
                        {
                            "query": query,
                            "params": [op["doc_id"]] + list(op_data.values()),
                        }
                    )

                elif op["type"] == "delete":
                    query = f"DELETE FROM {op['collection']} WHERE id = $1"
                    queries.append({"query": query, "params": [op["doc_id"]]})

            return await postgres_client.execute_transaction(queries)

        return await with_circuit_breaker(firestore_batch, postgres_batch)


# Instância do cliente unificado
unified_client = UnifiedDatabaseClient()
