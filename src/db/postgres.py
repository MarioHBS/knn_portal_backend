"""
Implementação da camada de acesso ao PostgreSQL.
"""
import asyncpg
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime

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
    async def get_document(table: str, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtém um documento do PostgreSQL.
        """
        try:
            conn = await PostgresClient.get_connection()
            try:
                # Construir query
                query = f"SELECT * FROM {table} WHERE id = $1"
                
                # Executar query
                row = await conn.fetchrow(query, doc_id)
                
                if row:
                    # Converter para dicionário
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
        filters: Optional[List[Tuple[str, str, Any]]] = None, 
        order_by: Optional[List[Tuple[str, str]]] = None,
        limit: int = 20,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Consulta documentos no PostgreSQL com filtros e ordenação.
        
        Args:
            table: Nome da tabela
            filters: Lista de tuplas (campo, operador, valor)
            order_by: Lista de tuplas (campo, direção)
            limit: Limite de documentos
            offset: Offset para paginação
        
        Returns:
            Dict com items, total, limit e offset
        """
        try:
            conn = await PostgresClient.get_connection()
            try:
                # Construir query base
                query = f"SELECT * FROM {table}"
                count_query = f"SELECT COUNT(*) FROM {table}"
                
                # Aplicar filtros
                params = []
                if filters:
                    where_clauses = []
                    for i, (field, op, value) in enumerate(filters):
                        # Converter operadores do Firestore para SQL
                        sql_op = "="
                        if op == "==": sql_op = "="
                        elif op == "!=": sql_op = "!="
                        elif op == "<": sql_op = "<"
                        elif op == "<=": sql_op = "<="
                        elif op == ">": sql_op = ">"
                        elif op == ">=": sql_op = ">="
                        
                        where_clauses.append(f"{field} {sql_op} ${i+1}")
                        params.append(value)
                    
                    if where_clauses:
                        where_clause = " WHERE " + " AND ".join(where_clauses)
                        query += where_clause
                        count_query += where_clause
                
                # Aplicar ordenação
                if order_by:
                    order_clauses = []
                    for field, direction in order_by:
                        # Converter direção para SQL
                        sql_direction = "ASC" if direction == "ASCENDING" else "DESC"
                        order_clauses.append(f"{field} {sql_direction}")
                    
                    if order_clauses:
                        query += " ORDER BY " + ", ".join(order_clauses)
                
                # Aplicar paginação
                query += f" LIMIT {limit} OFFSET {offset}"
                
                # Executar queries
                total = await conn.fetchval(count_query, *params)
                rows = await conn.fetch(query, *params)
                
                # Converter para dicionários
                items = [dict(row) for row in rows]
                
                return {
                    "items": items,
                    "total": total,
                    "limit": limit,
                    "offset": offset
                }
            finally:
                await conn.close()
        except Exception as e:
            logger.error(f"Erro ao consultar documentos em {table}: {str(e)}")
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
    async def update_document(table: str, doc_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Atualiza um documento no PostgreSQL.
        """
        try:
            conn = await PostgresClient.get_connection()
            try:
                # Adicionar timestamp de atualização
                data["updated_at"] = datetime.now()
                
                # Construir query
                set_clauses = [f"{field} = ${i+2}" for i, field in enumerate(data.keys())]
                
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
