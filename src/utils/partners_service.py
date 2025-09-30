"""
Serviço utilitário para operações com parceiros.

Este módulo contém a lógica comum compartilhada entre os endpoints
de listagem de parceiros para estudantes e funcionários.
"""

from typing import Any

from src.auth import JWTPayload
from src.db import firestore_client, postgres_client, with_circuit_breaker
from src.models import Partner, PartnerListResponse
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
    ) -> PartnerListResponse:
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
            PartnerListResponse: Lista de parceiros formatada

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

            # Extrair dados dos parceiros
            logger.info(f"DEBUG COMMON - Resultado da consulta Firestore: {result}")
            partners_data = result.get("items", [])
            logger.info(f"DEBUG COMMON - Quantidade de partners_data extraídos: {len(partners_data)}")

            # Converter dados brutos para objetos Partner
            partner_objects = []
            failed_partners = []
            for i, partner_data in enumerate(partners_data):
                try:
                    logger.info(f"DEBUG - Convertendo parceiro {i+1}: {partner_data}")
                    partner_obj = Partner(**partner_data)
                    partner_objects.append(partner_obj)
                    logger.info(f"DEBUG - Parceiro {i+1} convertido com sucesso")
                except Exception as e:
                    failed_partners.append({
                        'index': i+1,
                        'id': partner_data.get('id', 'N/A'),
                        'error': str(e)
                    })
                    logger.error(
                        f"❌ FALHA na conversão do parceiro {i+1} (ID: {partner_data.get('id', 'N/A')}): {e}"
                    )
                    logger.error(f"❌ Dados do parceiro que falhou: {partner_data}")
                    continue

            if failed_partners:
                logger.error(f"❌ RESUMO: {len(failed_partners)} parceiro(s) falharam na conversão:")
                for failed in failed_partners:
                    logger.error(f"   - Parceiro {failed['index']} (ID: {failed['id']}): {failed['error']}")

            logger.info(f"DEBUG - Total de partner_objects criados: {len(partner_objects)}")
            logger.info(
                f"Retornando {len(partner_objects)} parceiros para usuário "
                f"{current_user.role} (tenant: {current_user.tenant})"
            )

            return PartnerListResponse(data=partner_objects)

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
