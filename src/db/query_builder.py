"""Sistema avançado de construção de queries para operações de banco de dados.

Este módulo fornece classes para construção de queries complexas,
filtros avançados, ordenação e paginação.
"""

from datetime import datetime
from typing import Any

from src.db.unified_client import unified_client
from src.utils import logger


class QueryBuilder:
    """Construtor de queries avançadas para operações de banco de dados."""

    def __init__(self, collection: str, tenant_id: str):
        """Inicializa o QueryBuilder.

        Args:
            collection: Nome da coleção
            tenant_id: ID do tenant
        """
        self.collection = collection
        self.tenant_id = tenant_id
        self._filters = []
        self._order_by = []
        self._limit_value = None
        self._offset_value = 0
        self._select_fields = None

    def where(self, field: str, operator: str, value: Any) -> "QueryBuilder":
        """Adiciona um filtro à query.

        Args:
            field: Nome do campo
            operator: Operador de comparação (==, !=, <, <=, >, >=, in, not-in, array-contains)
            value: Valor para comparação

        Returns:
            Self para method chaining
        """
        self._filters.append({"field": field, "operator": operator, "value": value})
        return self

    def where_in(self, field: str, values: list[Any]) -> "QueryBuilder":
        """Adiciona filtro 'in' à query.

        Args:
            field: Nome do campo
            values: Lista de valores

        Returns:
            Self para method chaining
        """
        return self.where(field, "in", values)

    def where_not_in(self, field: str, values: list[Any]) -> "QueryBuilder":
        """Adiciona filtro 'not-in' à query.

        Args:
            field: Nome do campo
            values: Lista de valores

        Returns:
            Self para method chaining
        """
        return self.where(field, "not-in", values)

    def where_array_contains(self, field: str, value: Any) -> "QueryBuilder":
        """Adiciona filtro 'array-contains' à query.

        Args:
            field: Nome do campo
            value: Valor que deve estar no array

        Returns:
            Self para method chaining
        """
        return self.where(field, "array-contains", value)

    def where_between(self, field: str, start: Any, end: Any) -> "QueryBuilder":
        """Adiciona filtro de intervalo à query.

        Args:
            field: Nome do campo
            start: Valor inicial
            end: Valor final

        Returns:
            Self para method chaining
        """
        return self.where(field, ">=", start).where(field, "<=", end)

    def where_date_range(
        self, field: str, start_date: datetime, end_date: datetime
    ) -> "QueryBuilder":
        """Adiciona filtro de intervalo de datas.

        Args:
            field: Nome do campo de data
            start_date: Data inicial
            end_date: Data final

        Returns:
            Self para method chaining
        """
        return self.where_between(field, start_date, end_date)

    def order(self, field: str, direction: str = "asc") -> "QueryBuilder":
        """Adiciona ordenação à query.

        Args:
            field: Nome do campo
            direction: Direção da ordenação ('asc' ou 'desc')

        Returns:
            Self para method chaining
        """
        self._order_by.append({"field": field, "direction": direction})
        return self

    def order_by_created_at(self, direction: str = "desc") -> "QueryBuilder":
        """Ordena por data de criação.

        Args:
            direction: Direção da ordenação

        Returns:
            Self para method chaining
        """
        return self.order("created_at", direction)

    def order_by_updated_at(self, direction: str = "desc") -> "QueryBuilder":
        """Ordena por data de atualização.

        Args:
            direction: Direção da ordenação

        Returns:
            Self para method chaining
        """
        return self.order("updated_at", direction)

    def limit(self, count: int) -> "QueryBuilder":
        """Define limite de resultados.

        Args:
            count: Número máximo de resultados

        Returns:
            Self para method chaining
        """
        self._limit_value = count
        return self

    def offset(self, count: int) -> "QueryBuilder":
        """Define offset para paginação.

        Args:
            count: Número de registros para pular

        Returns:
            Self para method chaining
        """
        self._offset_value = count
        return self

    def select(self, fields: list[str]) -> "QueryBuilder":
        """Define campos específicos para retornar.

        Args:
            fields: Lista de campos

        Returns:
            Self para method chaining
        """
        self._select_fields = fields
        return self

    def page(self, page_number: int, page_size: int = 20) -> "QueryBuilder":
        """Configura paginação.

        Args:
            page_number: Número da página (começando em 1)
            page_size: Tamanho da página

        Returns:
            Self para method chaining
        """
        offset = (page_number - 1) * page_size
        return self.offset(offset).limit(page_size)

    async def get(self) -> list[dict[str, Any]]:
        """Executa a query e retorna os resultados.

        Returns:
            Lista de documentos
        """
        try:
            query_params = {
                "collection": self.collection,
                "tenant_id": self.tenant_id,
                "filters": self._filters,
                "order_by": self._order_by,
                "limit": self._limit_value,
                "offset": self._offset_value,
                "select_fields": self._select_fields,
            }

            logger.debug(f"Executando query: {query_params}")
            results = await unified_client.query_documents(**query_params)

            logger.info(
                f"Query executada com sucesso: {len(results)} resultados",
                extra={"collection": self.collection, "tenant_id": self.tenant_id},
            )

            return results

        except Exception as e:
            logger.error(
                f"Erro ao executar query: {str(e)}",
                extra={"collection": self.collection, "tenant_id": self.tenant_id},
            )
            raise

    async def get_first(self) -> dict[str, Any] | None:
        """Retorna o primeiro resultado da query.

        Returns:
            Primeiro documento ou None se não encontrado
        """
        results = await self.limit(1).get()
        return results[0] if results else None

    async def count(self) -> int:
        """Conta o número de documentos que atendem aos critérios.

        Returns:
            Número de documentos
        """
        try:
            count_params = {
                "collection": self.collection,
                "tenant_id": self.tenant_id,
                "filters": self._filters,
            }

            # Para contagem, usamos uma query específica
            results = await unified_client.query_documents(**count_params)
            return len(results)

        except Exception as e:
            logger.error(
                f"Erro ao contar documentos: {str(e)}",
                extra={"collection": self.collection, "tenant_id": self.tenant_id},
            )
            raise

    async def exists(self) -> bool:
        """Verifica se existe pelo menos um documento que atende aos critérios.

        Returns:
            True se existe pelo menos um documento
        """
        count = await self.count()
        return count > 0

    def clone(self) -> "QueryBuilder":
        """Cria uma cópia da query atual.

        Returns:
            Nova instância do QueryBuilder com os mesmos parâmetros
        """
        new_query = QueryBuilder(self.collection, self.tenant_id)
        new_query._filters = self._filters.copy()
        new_query._order_by = self._order_by.copy()
        new_query._limit_value = self._limit_value
        new_query._offset_value = self._offset_value
        new_query._select_fields = (
            self._select_fields.copy() if self._select_fields else None
        )
        return new_query


class SearchHelper:
    """Helper para operações de busca comuns."""

    @staticmethod
    def create_query(collection: str, tenant_id: str) -> QueryBuilder:
        """Cria uma nova instância do QueryBuilder.

        Args:
            collection: Nome da coleção
            tenant_id: ID do tenant

        Returns:
            Nova instância do QueryBuilder
        """
        return QueryBuilder(collection, tenant_id)

    @staticmethod
    async def find_by_id(
        collection: str, tenant_id: str, document_id: str
    ) -> dict[str, Any] | None:
        """Busca um documento por ID.

        Args:
            collection: Nome da coleção
            tenant_id: ID do tenant
            document_id: ID do documento

        Returns:
            Documento encontrado ou None
        """
        return await unified_client.get_document(collection, document_id, tenant_id)

    @staticmethod
    async def find_by_field(
        collection: str, tenant_id: str, field: str, value: Any
    ) -> list[dict[str, Any]]:
        """Busca documentos por um campo específico.

        Args:
            collection: Nome da coleção
            tenant_id: ID do tenant
            field: Nome do campo
            value: Valor do campo

        Returns:
            Lista de documentos encontrados
        """
        return await (
            SearchHelper.create_query(collection, tenant_id)
            .where(field, "==", value)
            .get()
        )

    @staticmethod
    async def search_text(
        collection: str, tenant_id: str, text_fields: list[str], search_term: str
    ) -> list[dict[str, Any]]:
        """Busca texto em múltiplos campos.

        Args:
            collection: Nome da coleção
            tenant_id: ID do tenant
            text_fields: Lista de campos de texto para buscar
            search_term: Termo de busca

        Returns:
            Lista de documentos encontrados
        """
        # Para busca de texto, usamos uma abordagem simples
        # Em implementações mais avançadas, poderia usar full-text search
        query = SearchHelper.create_query(collection, tenant_id)

        # Adiciona filtros para cada campo de texto
        for field in text_fields:
            # Nota: Esta é uma implementação simplificada
            # Para busca real de texto, seria necessário usar índices específicos
            query = query.where(field, ">=", search_term).where(
                field, "<", search_term + "\uf8ff"
            )

        return await query.get()

    @staticmethod
    async def find_active(
        collection: str, tenant_id: str, limit: int = 100
    ) -> list[dict[str, Any]]:
        """Busca registros ativos.

        Args:
            collection: Nome da coleção
            tenant_id: ID do tenant
            limit: Limite de resultados

        Returns:
            Registros ativos
        """
        return await (
            SearchHelper.create_query(collection, tenant_id)
            .where("active", "==", True)
            .order("created_at", "desc")
            .limit(limit)
            .get()
        )

    @staticmethod
    async def find_recent(
        collection: str, tenant_id: str, days: int = 7, limit: int = 50
    ) -> list[dict[str, Any]]:
        """Busca registros recentes.

        Args:
            collection: Nome da coleção
            tenant_id: ID do tenant
            days: Número de dias para considerar "recente"
            limit: Limite de resultados

        Returns:
            Registros recentes
        """
        from datetime import timedelta

        cutoff_date = datetime.now() - timedelta(days=days)
        return await (
            SearchHelper.create_query(collection, tenant_id)
            .where("created_at", ">=", cutoff_date)
            .order("created_at", "desc")
            .limit(limit)
            .get()
        )


# Instâncias para uso direto
search = SearchHelper()
