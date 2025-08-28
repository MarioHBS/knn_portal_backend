"""
Implementação dos endpoints para o perfil de funcionário (employee).
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.auth import JWTPayload, validate_employee_role
from src.db import firestore_client, postgres_client, with_circuit_breaker
from src.models import (
    PartnerListResponse,
)
from src.utils import logger

# Criar router
router = APIRouter(tags=["employee"])

# Dependência para validação de funcionário
employee_dependency = Depends(validate_employee_role)


@router.get("/partners", response_model=PartnerListResponse)
async def list_partners(
    cat: Optional[str] = Query(None, description="Filtro por categoria"),
    ord: Optional[str] = Query("name", description="Ordenação (name, category)"),
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
