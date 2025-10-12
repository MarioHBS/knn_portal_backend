"""
Implementação da camada de acesso ao PostgreSQL.
"""

from datetime import datetime
from typing import Any

import asyncpg

from src.config import POSTGRES_CONNECTION_STRING
from src.utils import logger


class PostgresClient:
    """Cliente para acesso ao PostgreSQL."""

    _pool = None

    @classmethod
    async def get_pool(cls):
        """Obtém o pool de conexões PostgreSQL."""
        if cls._pool is None:
            try:
                logger.info(
                    f"Criando pool de conexões PostgreSQL: {POSTGRES_CONNECTION_STRING}"
                )
                cls._pool = await asyncpg.create_pool(
                    POSTGRES_CONNECTION_STRING,
                    min_size=1,
                    max_size=10,
                    command_timeout=30,
                )
                logger.info("Pool de conexões PostgreSQL criado com sucesso")
            except Exception as e:
                logger.error(f"Erro ao criar pool PostgreSQL: {str(e)}", exc_info=True)
                raise Exception(f"Erro ao criar pool PostgreSQL") from e
        return cls._pool

    @staticmethod
    async def get_connection():
        """
        Obtém uma conexão com o PostgreSQL.
        """
        try:
            pool = await PostgresClient.get_pool()
            conn = await pool.acquire()
            return conn
        except Exception as e:
            logger.error(f"Erro ao conectar ao PostgreSQL: {str(e)}", exc_info=True)
            raise Exception(f"Erro ao conectar ao PostgreSQL") from e

    @staticmethod
    async def release_connection(conn):
        """Libera uma conexão de volta ao pool."""
        try:
            pool = await PostgresClient.get_pool()
            await pool.release(conn)
        except Exception as e:
            logger.error(f"Erro ao liberar conexão PostgreSQL: {str(e)}")

    @staticmethod
    async def get_document(
        table: str, doc_id: str, tenant_id: str
    ) -> dict[str, Any] | None:
        """
        Obtém um documento do PostgreSQL filtrando por tenant_id.
        """
        try:
            conn = await PostgresClient.get_connection()
            try:
                # Query com chave composta
                query = f"SELECT * FROM {table} WHERE id = $1 AND tenant_id = $2"
                row = await conn.fetchrow(query, doc_id, tenant_id)
                if row:
                    return dict(row)
                return None
            finally:
                await conn.close()
        except Exception as e:
            logger.error(f"Erro ao obter documento {table}/{doc_id}: {str(e)}")
            raise Exception(f"Erro ao obter documento {table}/{doc_id}") from e

    @staticmethod
    async def query_documents(
        table: str,
        *,
        tenant_id: str,
        filters: list[tuple[str, str, Any]] | None = None,
        order_by: list[tuple[str, str]] | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> dict[str, Any]:
        """
        Consulta documentos no PostgreSQL filtrando por tenant_id.
        """
        conn = None
        try:
            conn = await PostgresClient.get_connection()

            query = f"SELECT * FROM {table} WHERE tenant_id = $1"
            params = [tenant_id]
            param_idx = 2

            if filters:
                for f in filters:
                    query += f" AND {f[0]} {f[1]} ${param_idx}"
                    params.append(f[2])
                    param_idx += 1

            if order_by:
                order_str = ", ".join([f"{o[0]} {o[1]}" for o in order_by])
                query += f" ORDER BY {order_str}"

            # Aplicar limit e offset na query principal
            query += f" LIMIT {limit} OFFSET {offset}"

            logger.info(f"Executando query PostgreSQL: {query} com params: {params}")
            rows = await conn.fetch(query, *params)
            logger.info(
                f"Query executada com sucesso, {len(rows)} registros retornados"
            )

            return {
                "items": [dict(r) for r in rows],
                "total": len(rows),  # Temporário: usar len dos resultados
                "limit": limit,
                "offset": offset,
            }

        except Exception as e:
            logger.error(
                f"Erro ao consultar documentos {table}: {str(e)}", exc_info=True
            )
            raise Exception(f"Erro ao consultar documentos {table}") from e
        finally:
            if conn:
                try:
                    await PostgresClient.release_connection(conn)
                    logger.info("Conexão PostgreSQL liberada com sucesso")
                except Exception as e:
                    logger.error(f"Erro ao liberar conexão PostgreSQL: {str(e)}")

    @staticmethod
    async def create_document(table: str, data: dict[str, Any]) -> dict[str, Any]:
        """
        Cria um documento no PostgreSQL.
        """
        try:
            conn = await PostgresClient.get_connection()
            try:
                # Adicionar timestamp de criação
                data["created_at"] = datetime.now()

                # Construir query
                fields = list(data.keys())
                placeholders = [f"${i+1}" for i in range(len(fields))]

                query = f"""
                INSERT INTO {table} ({', '.join(fields)})
                VALUES ({', '.join(placeholders)})
                RETURNING *
                """

                # Executar query
                row = await conn.fetchrow(query, *[data[field] for field in fields])

                # Converter para dicionário
                return dict(row)
            finally:
                await conn.close()
        except Exception as e:
            logger.error(f"Erro ao criar documento em {table}: {str(e)}")
            raise Exception(f"Erro ao criar documento em {table}") from e

    @staticmethod
    async def update_document(
        table: str, doc_id: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Atualiza um documento no PostgreSQL.
        """
        try:
            conn = await PostgresClient.get_connection()
            try:
                # Adicionar timestamp de atualização
                data["updated_at"] = datetime.now()

                # Construir query
                set_clauses = [
                    f"{field} = ${i+2}" for i, field in enumerate(data.keys())
                ]

                query = f"""
                UPDATE {table}
                SET {', '.join(set_clauses)}
                WHERE id = $1
                RETURNING *
                """

                # Executar query
                row = await conn.fetchrow(query, doc_id, *data.values())

                # Converter para dicionário
                return dict(row)
            finally:
                await conn.close()
        except Exception as e:
            logger.error(f"Erro ao atualizar documento {table}/{doc_id}: {str(e)}")
            raise Exception(f"Erro ao atualizar documento {table}/{doc_id}") from e

    @staticmethod
    async def delete_document(table: str, doc_id: str) -> bool:
        """
        Remove um documento do PostgreSQL.
        """
        try:
            conn = await PostgresClient.get_connection()
            try:
                # Construir query
                query = f"DELETE FROM {table} WHERE id = $1"

                # Executar query
                await conn.execute(query, doc_id)

                return True
            finally:
                await conn.close()
        except Exception as e:
            logger.error(f"Erro ao remover documento {table}/{doc_id}: {str(e)}")
            raise Exception(f"Erro ao remover documento {table}/{doc_id}") from e

    @staticmethod
    async def execute_transaction(queries: list[dict[str, Any]]) -> bool:
        """
        Executa uma transação no PostgreSQL.

        Args:
            queries: Lista de queries no formato:
                {
                    "query": "SQL query com placeholders $1, $2, ...",
                    "params": [param1, param2, ...]
                }
        """
        try:
            conn = await PostgresClient.get_connection()
            try:
                async with conn.transaction():
                    for query_data in queries:
                        query = query_data.get("query")
                        params = query_data.get("params", [])

                        await conn.execute(query, *params)

                return True
            finally:
                await conn.close()
        except Exception as e:
            logger.error(f"Erro ao executar transação: {str(e)}")
            raise Exception(f"Erro ao executar transação") from e


# Instância do cliente PostgreSQL
postgres_client = PostgresClient()
