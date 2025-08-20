"""
Implementação dos endpoints para o perfil de funcionário (employee).
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.auth import JWTPayload, validate_employee_role
from src.db import firestore_client, with_circuit_breaker
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

        # Buscar parceiros
        partners_data = await with_circuit_breaker(
            firestore_client.query_documents,
            "partners",
            filters=filters,
            order_by=ord,
            limit=limit,
            offset=offset,
            tenant_id=current_user.tenant_id,
        )

        # Contar total
        total = await with_circuit_breaker(
            firestore_client.count_documents,
            "partners",
            filters=filters,
            tenant_id=current_user.tenant_id,
        )

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
