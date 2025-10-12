"""
Serviço utilitário para operações com parceiros.

Este módulo contém a lógica comum compartilhada entre os endpoints
de listagem de parceiros para estudantes e funcionários.
"""

import json
from typing import Any

from src.auth import JWTPayload
from src.db import firestore_client, postgres_client, with_circuit_breaker
from src.models import PartnerModel
from src.utils import logger


class PartnersService:
    """Serviço para operações com parceiros."""

    @staticmethod
    async def list_partners_common(
        current_user: JWTPayload,
        cat: str | None = None,
        ord: str | None = None,
        limit: int = 20,
        offset: int = 0,
        use_circuit_breaker: bool = True,
        enable_ordering: bool = True,
    ) -> tuple[list[PartnerModel], int]:
        """
        Lista parceiros com filtros e paginação.

        Função comum compartilhada entre endpoints de student e employee.

        Args:
            current_user: Dados do usuário autenticado
            cat: Filtro por categoria (opcional)
            ord: Ordenação dos resultados (opcional)
            limit: Número máximo de itens por página
            offset: Offset para paginação
            use_circuit_breaker: Se deve usar circuit breaker (padrão: True)
            enable_ordering: Se deve aplicar ordenação (padrão: True)

        Returns:
            tuple[list[PartnerModel], int]: Tupla com a lista de parceiros e o total de itens.

        Raises:
            HTTPException: Em caso de erro na consulta
        """
        try:
            # Construir filtros base (sempre filtrar apenas parceiros ativos)
            filters = [("active", "==", True)]

            # Adicionar filtro de categoria se fornecido
            if cat:
                filters.append(("category", "==", cat))

            # Preparar ordenação se habilitada
            order_by = []
            if enable_ordering and ord:
                if ord in ["name", "name_asc"]:
                    order_by.append(("trade_name", "ASCENDING"))
                elif ord == "name_desc":
                    order_by.append(("trade_name", "DESCENDING"))
                elif ord in ["category", "category_asc"]:
                    order_by.append(("category", "ASCENDING"))
                elif ord == "category_desc":
                    order_by.append(("category", "DESCENDING"))
                else:
                    # Ordenação padrão se valor inválido
                    order_by.append(("trade_name", "ASCENDING"))
            elif enable_ordering:
                # Ordenação padrão quando habilitada
                order_by.append(("trade_name", "ASCENDING"))

            # Executar consulta com ou sem circuit breaker
            if use_circuit_breaker:
                result = await PartnersService._query_with_circuit_breaker(
                    current_user=current_user,
                    filters=filters,
                    order_by=order_by,
                    limit=limit,
                    offset=offset,
                )
            else:
                result = await PartnersService._query_firestore_only(
                    current_user=current_user,
                    filters=filters,
                    order_by=order_by,
                    limit=limit,
                    offset=offset,
                )

            # Extrair dados dos parceiros e total
            partners_data = result.get("items", [])
            total = result.get("total", 0)

            # Converter dados brutos para objetos Partner
            partner_objects = []
            for partner_data in partners_data:
                try:
                    partner_obj = PartnerModel(**partner_data)
                    partner_objects.append(partner_obj)
                except Exception as e:
                    raise ValueError(
                        f"Failed to parse partner data: {json.dumps(partner_data, indent=2)}. Error: {e}"
                    ) from e

            logger.info(
                f"Retornando {len(partner_objects)} de {total} parceiros para usuário "
                f"{current_user.role} (tenant: {current_user.tenant})"
            )

            return partner_objects, total

        except Exception as e:
            logger.error(
                f"Erro ao listar parceiros para {current_user.role}: {str(e)}",
                exc_info=True,
            )
            raise

    @staticmethod
    async def _query_with_circuit_breaker(
        current_user: JWTPayload,
        filters: list[tuple[str, str, Any]],
        order_by: list[tuple[str, str]],
        limit: int,
        offset: int,
    ) -> dict[str, Any]:
        """
        Executa consulta com circuit breaker (Firestore + fallback PostgreSQL).

        Args:
            current_user: Dados do usuário autenticado
            filters: Lista de filtros para aplicar
            order_by: Lista de ordenações para aplicar
            limit: Limite de resultados
            offset: Offset para paginação

        Returns:
            dict: Resultado da consulta
        """

        async def firestore_query():
            return await firestore_client.query_documents(
                "partners",
                tenant_id=current_user.tenant,
                filters=filters,
                order_by=order_by,
                limit=limit,
                offset=offset,
            )

        async def postgres_query():
            return await postgres_client.query_documents(
                "partners",
                filters=filters,
                order_by=order_by,
                limit=limit,
                offset=offset,
                tenant_id=current_user.tenant,
            )

        return await with_circuit_breaker(firestore_query, postgres_query)

    @staticmethod
    async def _query_firestore_only(
        current_user: JWTPayload,
        filters: list[tuple[str, str, Any]],
        order_by: list[tuple[str, str]] | None,
        limit: int,
        offset: int,
    ) -> dict[str, Any]:
        """
        Executa consulta apenas no Firestore (sem circuit breaker).

        Args:
            current_user: Dados do usuário autenticado
            filters: Lista de filtros para aplicar
            order_by: Lista de ordenações para aplicar (pode ser None)
            limit: Limite de resultados
            offset: Offset para paginação

        Returns:
            dict: Resultado da consulta
        """
        return await firestore_client.query_documents(
            "partners",
            tenant_id=current_user.tenant,
            filters=filters,
            order_by=order_by,
            limit=limit,
            offset=offset,
        )
