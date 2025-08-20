"""
Implementação da camada de acesso ao PostgreSQL.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import asyncpg

from src.config import POSTGRES_CONNECTION_STRING
from src.utils import logger


class PostgresClient:
    """Cliente para acesso ao PostgreSQL."""

    @staticmethod
    async def get_connection():
        """
        Obtém uma conexão com o PostgreSQL.
        """
        try:
            conn = await asyncpg.connect(POSTGRES_CONNECTION_STRING)
            return conn
        except Exception as e:
            logger.error(f"Erro ao conectar ao PostgreSQL: {str(e)}")
            raise

    @staticmethod
    async def get_document(
        table: str, doc_id: str, tenant_id: str
    ) -> Optional[Dict[str, Any]]:
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
            raise

    @staticmethod
    async def query_documents(
        table: str,
        tenant_id: str,
        filters: Optional[List[Tuple[str, str, Any]]] = None,
        order_by: Optional[List[Tuple[str, str]]] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        Consulta documentos no PostgreSQL filtrando por tenant_id.
        """
        try:
            conn = await PostgresClient.get_connection()
            try:
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
                query += f" LIMIT {limit} OFFSET {offset}"
                rows = await conn.fetch(query, *params)
                return {"data": [dict(r) for r in rows]}
            finally:
                await conn.close()
        except Exception as e:
            logger.error(f"Erro ao consultar documentos {table}: {str(e)}")
            raise

    @staticmethod
    async def create_document(table: str, data: Dict[str, Any]) -> Dict[str, Any]:
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
            raise

    @staticmethod
    async def update_document(
        table: str, doc_id: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
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
            raise

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
            raise

    @staticmethod
    async def execute_transaction(queries: List[Dict[str, Any]]) -> bool:
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
            raise


# Instância do cliente PostgreSQL
postgres_client = PostgresClient()
