"""Implementação dos endpoints para o perfil de funcionário (employee)."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from src.auth import JWTPayload, validate_employee_role
from src.db import firestore_client, postgres_client, with_circuit_breaker
from src.models import (
    PartnerDetail,
    PartnerDetailResponse,
    PartnerListResponse,
    ValidationCodeRequest,
    ValidationCodeResponse,
)
from src.utils import logger
from src.utils.business_rules import business_rules
from src.utils.partners_service import PartnersService

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
    
    Endpoint específico para funcionários com as seguintes características:
    - Utiliza circuit breaker para alta disponibilidade
    - Ordenação habilitada por padrão
    - Acesso apenas a parceiros ativos
    """
    try:
        return await PartnersService.list_partners_common(
            current_user=current_user,
            cat=cat,
            ord=ord,
            limit=limit,
            offset=offset,
            use_circuit_breaker=True,  # Habilitado para funcionários
            enable_ordering=True,      # Habilitado para funcionários
        )

    except Exception as e:
        logger.error(
            f"Erro ao listar parceiros para funcionário {current_user.sub}: {e}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {"code": "INTERNAL_ERROR", "msg": "Erro interno do servidor"}
            },
        ) from e


@router.get("/me/history")
async def get_employee_validation_history(
    current_user: JWTPayload = employee_dependency,
):
    """
    Retorna o histórico de códigos de validação usados pelo funcionário.
    """
    try:
        employee_id = current_user.sub

        # Buscar códigos de validação usados pelo funcionário
        async def get_firestore_codes():
            return await firestore_client.query_documents(
                "validation_codes",
                tenant_id=current_user.tenant,
                filters=[
                    ("employee_id", "==", employee_id),
                    ("used_at", "!=", None),
                ],
                order_by=[("used_at", "desc")],
                limit=50,
            )

        async def get_postgres_codes():
            return await postgres_client.query_documents(
                "validation_codes",
                filters=[
                    ("employee_id", "==", employee_id),
                    ("used_at", "!=", None),
                ],
                order_by=[("used_at", "desc")],
                limit=50,
                tenant_id=current_user.tenant,
            )

        codes_result = await with_circuit_breaker(
            get_firestore_codes, get_postgres_codes
        )
        codes = codes_result.get("items", [])

        # Buscar informações dos parceiros para cada código
        history = []
        for code in codes:
            partner_id = code.get("partner_id")

            # Buscar dados do parceiro
            async def get_firestore_partner():
                return await firestore_client.get_document(
                    "partners", partner_id, tenant_id=current_user.tenant
                )

            async def get_postgres_partner():
                return await postgres_client.get_document(
                    "partners", partner_id, tenant_id=current_user.tenant
                )

            try:
                partner_result = await with_circuit_breaker(
                    get_firestore_partner, get_postgres_partner
                )
                partner = partner_result.get("data", {})
            except Exception:
                partner = {"name": "Parceiro não encontrado"}

            history.append(
                {
                    "code": code.get("code_hash", "***"),
                    "used_at": code.get("used_at"),
                    "partner": {
                        "id": partner_id,
                        "name": partner.get("name", "Parceiro não encontrado"),
                    },
                }
            )

        return {
            "data": {
                "history": history,
                "total": len(history),
            },
            "msg": "ok",
        }

    except Exception as e:
        logger.error(f"Erro ao buscar histórico do funcionário: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "SERVER_ERROR",
                    "msg": "Erro ao buscar histórico",
                }
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


@router.post("/validation-codes", response_model=ValidationCodeResponse)
async def create_validation_code(
    request: ValidationCodeRequest,
    current_user: JWTPayload = employee_dependency,
):
    """
    Gera um código de validação de 6 dígitos que expira em 3 minutos para funcionários.
    """
    try:
        # Verificar se o parceiro existe e está ativo
        async def get_firestore_partner():
            return await firestore_client.get_document(
                "partners", request.partner_id, tenant_id=current_user.tenant
            )

        async def get_postgres_partner():
            return await postgres_client.get_document(
                "partners", request.partner_id, tenant_id=current_user.tenant
            )

        partner_result = await with_circuit_breaker(
            get_firestore_partner, get_postgres_partner
        )
        partner = partner_result.get("data")

        if not partner or not partner.get("active", False):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": {"code": "NOT_FOUND", "msg": "Parceiro não encontrado"}
                },
            )

        # Verificar se o funcionário existe e está ativo
        employee_id = current_user.sub

        async def get_firestore_employee():
            return await firestore_client.get_document(
                "employees", employee_id, tenant_id=current_user.tenant
            )

        async def get_postgres_employee():
            return await postgres_client.get_document(
                "employees", employee_id, tenant_id=current_user.tenant
            )

        employee_result = await with_circuit_breaker(
            get_firestore_employee, get_postgres_employee
        )
        employee = employee_result.get("data")

        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": {"code": "NOT_FOUND", "msg": "Funcionário não encontrado"}
                },
            )

        # Verificar se o funcionário está ativo
        if not business_rules.validate_student_active(employee.get("active_until")):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": {
                        "code": "INACTIVE_EMPLOYEE",
                        "msg": "Funcionário com cadastro inativo",
                    }
                },
            )

        # Gerar código único de 6 dígitos
        code = business_rules.generate_validation_code()
        expires = business_rules.calculate_code_expiration()

        # Usar o código como chave do documento para evitar duplicatas
        validation_code = {
            "id": code,  # Usar código como ID do documento
            "employee_id": employee_id,
            "partner_id": request.partner_id,
            "code_hash": code,
            "expires": expires.isoformat(),
            "used_at": None,
            "user_type": "employee",
            "tenant_id": current_user.tenant,
            "created_at": datetime.now().isoformat(),
        }

        # Tentar criar documento com código como ID
        try:
            await firestore_client.create_document(
                "validation_codes", validation_code, code
            )
        except Exception as e:
            # Se falhar (código duplicado), gerar novo código
            if "already exists" in str(e).lower():
                # Gerar novo código e tentar novamente
                code = business_rules.generate_validation_code()
                validation_code["id"] = code
                validation_code["code_hash"] = code

                await firestore_client.create_document(
                    "validation_codes", validation_code, code
                )
            else:
                raise

        return {
            "data": {
                "code": code,
                "expires": expires.isoformat(),
                "ttl_seconds": 180,  # 3 minutos
            },
            "msg": "ok",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao gerar código de validação para funcionário: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "SERVER_ERROR",
                    "msg": "Erro ao gerar código de validação",
                }
            },
        )
