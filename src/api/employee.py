"""
Implementação dos endpoints para o perfil de funcionário (employee).
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from src.auth import JWTPayload, validate_employee_role
from src.db import firestore_client, postgres_client, with_circuit_breaker
from src.models import (
    PartnerDetail,
    PartnerDetailResponse,
    PartnerListResponse,
)
from src.utils import logger

# Criar router
router = APIRouter(tags=["employee"])

# Dependência para validação de funcionário
employee_dependency = Depends(validate_employee_role)


@router.get("/partners", response_model=PartnerListResponse)
async def list_partners(
    cat: str | None = Query(None, description="Filtro por categoria"),
    ord: str | None = Query("name", description="Ordenação (name, category)"),
    limit: int = Query(20, ge=1, le=100, description="Limite de resultados"),
    offset: int = Query(0, ge=0, description="Offset para paginação"),
    current_user: JWTPayload = employee_dependency,
) -> PartnerListResponse:
    """
    Lista parceiros disponíveis para funcionários com filtros e paginação.
    """
    try:
        # Construir filtros
        filters = {"active": True}
        if cat:
            filters["category"] = cat

        # Preparar filtros para query
        query_filters = []
        if cat:
            query_filters.append(("category", "==", cat))
        query_filters.append(("active", "==", True))

        # Preparar ordenação
        order_by = []
        if ord == "name":
            order_by.append(("trade_name", "ASCENDING"))
        elif ord == "category":
            order_by.append(("category", "ASCENDING"))
        else:
            order_by.append(("trade_name", "ASCENDING"))

        # Buscar parceiros com circuit breaker
        async def firestore_query():
            return await firestore_client.query_documents(
                "partners",
                filters=query_filters,
                order_by=order_by,
                limit=limit,
                offset=offset,
                tenant_id=current_user.tenant,
            )

        async def postgres_query():
            return await postgres_client.query_documents(
                "partners",
                filters=query_filters,
                order_by=order_by,
                limit=limit,
                offset=offset,
                tenant_id=current_user.tenant,
            )

        result = await with_circuit_breaker(firestore_query, postgres_query)

        partners_data = result.get("items", [])
        total = result.get("total", 0)

        return PartnerListResponse(
            data={
                "items": partners_data,
                "total": total,
                "limit": limit,
                "offset": offset,
            }
        )

    except Exception as e:
        logger.error(
            f"Erro ao listar parceiros para funcionário {current_user.id}: {e}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {"code": "INTERNAL_ERROR", "msg": "Erro interno do servidor"}
            },
        ) from e


@router.get("/partners/{id}", response_model=PartnerDetailResponse)
async def get_partner_details(
    id: str = Path(..., description="ID do parceiro"),
    current_user: JWTPayload = employee_dependency,
):
    """
    Retorna detalhes de um parceiro específico com suas promoções ativas para funcionários.
    """
    try:
        now = datetime.now()

        # Buscar parceiro
        async def get_firestore_partner():
            return await firestore_client.get_document(
                "partners", id, tenant_id=current_user.tenant
            )

        async def get_postgres_partner():
            return await postgres_client.get_document(
                "partners", id, tenant_id=current_user.tenant
            )

        partner_result = await with_circuit_breaker(
            get_firestore_partner, get_postgres_partner
        )
        partner = partner_result.get("data")

        if not partner or not partner.get("active"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": {
                        "code": "PARTNER_NOT_FOUND",
                        "msg": "Parceiro não encontrado ou inativo",
                    }
                },
            )

        # Buscar promoções ativas do parceiro para funcionários
        async def get_firestore_promotions():
            return await firestore_client.query_documents(
                "promotions",
                filters=[
                    ("partner_id", "==", id),
                    ("active", "==", True),
                    ("valid_from", "<=", now),
                    ("valid_to", ">=", now),
                    ("audience", "array_contains_any", ["employee"]),
                ],
            )

        async def get_postgres_promotions():
            return await postgres_client.query_documents(
                "promotions",
                filters=[
                    ("partner_id", "==", id),
                    ("active", "==", True),
                    ("valid_from", "<=", now),
                    ("valid_to", ">=", now),
                ],
            )

        promotions_result = await with_circuit_breaker(
            get_firestore_promotions, get_postgres_promotions
        )

        # Construir resposta
        partner_detail = PartnerDetail(
            **partner, promotions=promotions_result.get("items", [])
        )

        return {"data": partner_detail, "msg": "ok"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao obter detalhes do parceiro {id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "SERVER_ERROR",
                    "msg": "Erro ao obter detalhes do parceiro",
                }
            },
        ) from None
