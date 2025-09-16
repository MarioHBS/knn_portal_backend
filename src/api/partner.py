"""
Implementação dos endpoints para o perfil de parceiro (partner).
"""

import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from src.auth import JWTPayload, validate_partner_role
from src.config import CNPJ_HASH_SALT, RATE_LIMIT_REDEEM
from src.db import firestore_client, postgres_client, with_circuit_breaker
from src.models import (
    BaseResponse,
    PromotionListResponse,
    PromotionRequest,
    PromotionResponse,
    RedeemRequest,
    RedeemResponse,
    ReportResponse,
)
from src.utils import hash_cnpj, limiter, logger, validate_cnpj

# Criar router
router = APIRouter(tags=["partner"])


@router.post("/partner/redeem", response_model=RedeemResponse)
@limiter.limit(RATE_LIMIT_REDEEM)
async def redeem_code(
    request: RedeemRequest, current_user: JWTPayload = Depends(validate_partner_role)
):
    """
    Resgata um código de validação gerado por um aluno.
    Limitado a 5 requisições por minuto por IP.
    """
    try:
        partner_id = current_user.sub

        # Validar CNPJ
        if not validate_cnpj(request.cnpj):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"error": {"code": "INVALID_CNPJ", "msg": "CNPJ inválido"}},
            )

        # Buscar código de validação no Firestore e PostgreSQL
        async def get_firestore_code():
            return await firestore_client.get_document(
                "validation_codes", request.code, tenant_id=current_user.tenant
            )

        async def get_postgres_code():
            return await postgres_client.get_document(
                "validation_codes", request.code, tenant_id=current_user.tenant
            )

        code_result = await with_circuit_breaker(get_firestore_code, get_postgres_code)
        code_data = code_result.get("data")

        if not code_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": {"code": "NOT_FOUND", "msg": "Código não encontrado"}},
            )

        # Verificar se o código já foi usado
        if code_data.get("used_at"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": {"code": "CODE_USED", "msg": "Código já foi utilizado"}
                },
            )

        # Verificar se o código pertence ao parceiro correto
        if code_data.get("partner_id") != partner_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": {
                        "code": "INVALID_PARTNER",
                        "msg": "Código não pertence a este parceiro",
                    }
                },
            )

        code = code_data

        # Verificar se o código expirou
        expires = code.get("expires")
        if expires:
            # Converter para datetime se for string
            if isinstance(expires, str):
                expires = datetime.fromisoformat(expires.replace("Z", "+00:00"))

            if expires < datetime.now():
                raise HTTPException(
                    status_code=status.HTTP_410_GONE,
                    detail={"error": {"code": "EXPIRED", "msg": "Código expirado"}},
                )

        # Determinar tipo de usuário e buscar dados
        user_type = code.get("user_type", "student")  # Default para compatibilidade
        user_id = (
            code.get("student_id")
            if user_type == "student"
            else code.get("employee_id")
        )
        collection_name = "students" if user_type == "student" else "employees"

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": {
                        "code": "INVALID_CODE",
                        "msg": "Código inválido - usuário não identificado",
                    }
                },
            )

        async def get_firestore_user():
            return await firestore_client.get_document(
                collection_name, user_id, tenant_id=current_user.tenant
            )

        async def get_postgres_user():
            return await postgres_client.get_document(
                collection_name, user_id, tenant_id=current_user.tenant
            )

        user_result = await with_circuit_breaker(get_firestore_user, get_postgres_user)
        user = user_result.get("data")

        if not user:
            user_label = "Aluno" if user_type == "student" else "Funcionário"
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": {
                        "code": "USER_NOT_FOUND",
                        "msg": f"{user_label} não encontrado",
                    }
                },
            )

        # Verificar se o CNPJ corresponde ao parceiro
        cnpj_hash = hash_cnpj(request.cnpj, CNPJ_HASH_SALT)

        if user.get("cnpj_hash") != cnpj_hash:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": {
                        "code": "INVALID_CNPJ",
                        "msg": "CNPJ não corresponde ao parceiro",
                    }
                },
            )

        # Verificar se o usuário está com cadastro ativo
        active_until = user.get("active_until")
        if active_until:
            # Converter para datetime se for string
            if isinstance(active_until, str):
                active_until = datetime.fromisoformat(
                    active_until.replace("Z", "+00:00")
                )

            if active_until < datetime.now().date():
                user_label = "Aluno" if user_type == "student" else "Funcionário"
                error_code = (
                    "INACTIVE_STUDENT"
                    if user_type == "student"
                    else "INACTIVE_EMPLOYEE"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "error": {
                            "code": error_code,
                            "msg": f"{user_label} com cadastro inativo",
                        }
                    },
                )

        # Marcar código como usado
        now = datetime.now()

        await firestore_client.update_document(
            "validation_codes", code["id"], {"used_at": now.isoformat()}
        )

        # Registrar resgate
        redemption = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "user_type": user_type,
            "partner_id": partner_id,
            "validation_code_id": code["id"],
            "code": request.code,
            "redeemed_at": now.isoformat(),
            "tenant_id": current_user.tenant,
        }

        # Manter compatibilidade com campo student_id para códigos antigos
        if user_type == "student":
            redemption["student_id"] = user_id

        await firestore_client.create_document(
            "redemptions", redemption, redemption["id"]
        )

        # Retornar informações do usuário e promoção
        user_data = {
            "name": user.get("name", ""),
        }

        # Adicionar campos específicos por tipo de usuário
        if user_type == "student":
            user_data["course"] = user.get("course", "")
        else:  # employee
            user_data["department"] = user.get("department", "")
            user_data["position"] = user.get("position", "")

        return {
            "data": {
                "user": user_data,
                "user_type": user_type,
                "promotion": {
                    "title": "Promoção"  # Simplificado, poderia buscar a promoção específica
                },
            },
            "msg": "ok",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao resgatar código: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {"code": "SERVER_ERROR", "msg": "Erro ao resgatar código"}
            },
        ) from e


@router.get("/partner/promotions", response_model=PromotionListResponse)
async def list_partner_promotions(
    limit: int = Query(
        20, ge=1, le=100, description="Número máximo de itens por página"
    ),
    offset: int = Query(0, ge=0, description="Offset para paginação"),
    current_user: JWTPayload = Depends(validate_partner_role),
):
    """
    Lista promoções do parceiro.
    """
    try:
        partner_id = current_user.sub

        # Consultar promoções
        async def get_firestore_promotions():
            return await firestore_client.query_documents(
                "promotions",
                filters=[("partner_id", "==", partner_id)],
                order_by=[("valid_to", "DESCENDING")],
                limit=limit,
                offset=offset,
            )

        async def get_postgres_promotions():
            return await postgres_client.query_documents(
                "promotions",
                filters=[("partner_id", "==", partner_id)],
                order_by=[("valid_to", "DESCENDING")],
                limit=limit,
                offset=offset,
            )

        promotions_result = await with_circuit_breaker(
            get_firestore_promotions, get_postgres_promotions
        )

        return {"data": promotions_result, "msg": "ok"}

    except Exception as e:
        logger.error(f"Erro ao listar promoções: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {"code": "SERVER_ERROR", "msg": "Erro ao listar promoções"}
            },
        ) from None


@router.post("/partner/promotions", response_model=PromotionResponse)
async def create_promotion(
    request: PromotionRequest, current_user: JWTPayload = Depends(validate_partner_role)
):
    """
    Cria uma nova promoção para o parceiro.
    """
    try:
        partner_id = current_user.sub

        # Validar datas
        if request.valid_from >= request.valid_to:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": {
                        "code": "INVALID_DATES",
                        "msg": "Data de início deve ser anterior à data de término",
                    }
                },
            )

        # Criar promoção
        promotion = {
            "id": str(uuid.uuid4()),
            "partner_id": partner_id,
            "title": request.title,
            "type": request.type,
            "valid_from": request.valid_from.isoformat(),
            "valid_to": request.valid_to.isoformat(),
            "active": request.active,
            "audience": request.audience,
        }

        result = await firestore_client.create_document(
            "promotions", promotion, promotion["id"]
        )

        return {"data": result, "msg": "ok"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao criar promoção: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {"code": "SERVER_ERROR", "msg": "Erro ao criar promoção"}},
        ) from e


@router.put("/partner/promotions/{id}", response_model=PromotionResponse)
async def update_promotion(
    id: str = Path(..., description="ID da promoção"),
    request: PromotionRequest = None,
    current_user: JWTPayload = Depends(validate_partner_role),
):
    """
    Atualiza uma promoção existente do parceiro.
    """
    try:
        partner_id = current_user.sub

        # Verificar se a promoção existe e pertence ao parceiro
        async def get_firestore_promotion():
            return await firestore_client.get_document("promotions", id)

        async def get_postgres_promotion():
            return await postgres_client.get_document("promotions", id)

        promotion = await with_circuit_breaker(
            get_firestore_promotion, get_postgres_promotion
        )

        if not promotion:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": {"code": "NOT_FOUND", "msg": "Promoção não encontrada"}
                },
            )

        if promotion.get("partner_id") != partner_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": {
                        "code": "FORBIDDEN",
                        "msg": "Acesso negado a esta promoção",
                    }
                },
            )

        # Validar datas
        if request.valid_from >= request.valid_to:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": {
                        "code": "INVALID_DATES",
                        "msg": "Data de início deve ser anterior à data de término",
                    }
                },
            )

        # Atualizar promoção
        updated_promotion = {
            "title": request.title,
            "type": request.type,
            "valid_from": request.valid_from.isoformat(),
            "valid_to": request.valid_to.isoformat(),
            "active": request.active,
            "audience": request.audience,
        }

        result = await firestore_client.update_document(
            "promotions", id, updated_promotion
        )

        return {"data": result, "msg": "ok"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao atualizar promoção {id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {"code": "SERVER_ERROR", "msg": "Erro ao atualizar promoção"}
            },
        ) from e


@router.delete("/partner/promotions/{id}", response_model=BaseResponse)
async def delete_promotion(
    id: str = Path(..., description="ID da promoção"),
    current_user: JWTPayload = Depends(validate_partner_role),
):
    """
    Desativa uma promoção existente do parceiro.
    """
    try:
        partner_id = current_user.sub

        # Verificar se a promoção existe e pertence ao parceiro
        async def get_firestore_promotion():
            return await firestore_client.get_document("promotions", id)

        async def get_postgres_promotion():
            return await postgres_client.get_document("promotions", id)

        promotion = await with_circuit_breaker(
            get_firestore_promotion, get_postgres_promotion
        )

        if not promotion:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": {"code": "NOT_FOUND", "msg": "Promoção não encontrada"}
                },
            )

        if promotion.get("partner_id") != partner_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": {
                        "code": "FORBIDDEN",
                        "msg": "Acesso negado a esta promoção",
                    }
                },
            )

        # Desativar promoção (soft delete)
        await firestore_client.update_document("promotions", id, {"active": False})

        return {"msg": "ok"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao desativar promoção {id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {"code": "SERVER_ERROR", "msg": "Erro ao desativar promoção"}
            },
        ) from e


@router.get("/partner/reports", response_model=ReportResponse)
async def get_partner_reports(
    range: str = Query(..., description="Período para relatório (formato YYYY-MM)"),
    current_user: JWTPayload = Depends(validate_partner_role),
):
    """
    Retorna relatório de uso das promoções do parceiro.
    """
    try:
        partner_id = current_user.sub

        # Validar formato do período
        import re

        if not re.match(r"^\d{4}-\d{2}$", range):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": {
                        "code": "INVALID_RANGE",
                        "msg": "Formato de período inválido, use YYYY-MM",
                    }
                },
            )

        # Extrair ano e mês
        year, month = map(int, range.split("-"))

        # Calcular datas de início e fim do período
        from datetime import date

        start_date = date(year, month, 1).isoformat()

        # Calcular último dia do mês
        end_date = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
        end_date = (end_date - timedelta(days=1)).isoformat()

        # Obter códigos gerados no período
        async def get_firestore_codes():
            return await firestore_client.query_documents(
                "validation_codes",
                tenant_id=current_user.tenant,
                filters=[
                    ("partner_id", "==", partner_id),
                    ("created_at", ">=", start_date),
                    ("created_at", "<=", end_date),
                ],
            )

        async def get_postgres_codes():
            return await postgres_client.query_documents(
                "validation_codes",
                filters=[
                    ("partner_id", "==", partner_id),
                    ("created_at", ">=", start_date),
                    ("created_at", "<=", end_date),
                ],
            )

        codes_result = await with_circuit_breaker(
            get_firestore_codes, get_postgres_codes
        )

        # Contar códigos usados
        used_codes = [
            code for code in codes_result.get("items", []) if code.get("used_at")
        ]

        # Obter promoções do parceiro
        async def get_firestore_promotions():
            return await firestore_client.query_documents(
                "promotions", filters=[("partner_id", "==", partner_id)]
            )

        async def get_postgres_promotions():
            return await postgres_client.query_documents(
                "promotions", filters=[("partner_id", "==", partner_id)]
            )

        promotions_result = await with_circuit_breaker(
            get_firestore_promotions, get_postgres_promotions
        )

        # Contar resgates por promoção
        promotion_stats = []

        for promotion in promotions_result.get("items", []):
            # Contar resgates para esta promoção
            # Simplificado: na implementação real, seria necessário relacionar códigos com promoções
            redemptions_count = len(used_codes)

            promotion_stats.append(
                {
                    "id": promotion["id"],
                    "title": promotion["title"],
                    "redemptions": redemptions_count,
                }
            )

        # Ordenar por número de resgates (decrescente)
        promotion_stats.sort(key=lambda x: x["redemptions"], reverse=True)

        return {
            "data": {
                "period": range,
                "total_codes": len(codes_result.get("items", [])),
                "total_redemptions": len(used_codes),
                "promotions": promotion_stats,
            },
            "msg": "ok",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao gerar relatório: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {"code": "SERVER_ERROR", "msg": "Erro ao gerar relatório"}
            },
        ) from e
