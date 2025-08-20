"""
Implementação dos endpoints para o perfil de parceiro (partner).
"""
import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from src.auth import JWTPayload, validate_partner_role
from src.config import CPF_HASH_SALT, RATE_LIMIT_REDEEM
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
from src.utils import hash_cpf, limiter, logger, validate_cpf

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

        # Validar CPF
        if not validate_cpf(request.cpf):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"error": {"code": "INVALID_CPF", "msg": "CPF inválido"}},
            )

        # Buscar código de validação
        async def get_firestore_codes():
            return await firestore_client.query_documents(
                "validation_codes",
                filters=[
                    ("code_hash", "==", request.code),
                    ("partner_id", "==", partner_id),
                    ("used_at", "==", None),
                ],
                limit=1,
            )

        async def get_postgres_codes():
            return await postgres_client.query_documents(
                "validation_codes",
                filters=[
                    ("code_hash", "==", request.code),
                    ("partner_id", "==", partner_id),
                    ("used_at", "==", None),
                ],
                limit=1,
            )

        codes_result = await with_circuit_breaker(
            get_firestore_codes, get_postgres_codes
        )

        if not codes_result.get("items"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": {"code": "INVALID_CODE", "msg": "Código não encontrado"}
                },
            )

        code = codes_result["items"][0]

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

        # Obter aluno
        student_id = code.get("student_id")

        async def get_firestore_student():
            return await firestore_client.get_document("students", student_id)

        async def get_postgres_student():
            return await postgres_client.get_document("students", student_id)

        student = await with_circuit_breaker(
            get_firestore_student, get_postgres_student
        )

        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": {
                        "code": "STUDENT_NOT_FOUND",
                        "msg": "Aluno não encontrado",
                    }
                },
            )

        # Verificar se o CPF corresponde ao aluno
        cpf_hash = hash_cpf(request.cpf, CPF_HASH_SALT)

        if student.get("cpf_hash") != cpf_hash:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": {
                        "code": "INVALID_CPF",
                        "msg": "CPF não corresponde ao aluno",
                    }
                },
            )

        # Verificar se o aluno está com matrícula ativa
        active_until = student.get("active_until")
        if active_until:
            # Converter para datetime se for string
            if isinstance(active_until, str):
                active_until = datetime.fromisoformat(
                    active_until.replace("Z", "+00:00")
                )

            if active_until < datetime.now().date():
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "error": {
                            "code": "INACTIVE_STUDENT",
                            "msg": "Aluno com matrícula inativa",
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
            "validation_code_id": code["id"],
            "value": 0.0,  # Valor simbólico, pode ser atualizado depois
            "used_at": now.isoformat(),
        }

        await firestore_client.create_document(
            "redemptions", redemption, redemption["id"]
        )

        # Retornar informações do aluno e promoção
        return {
            "data": {
                "student": {
                    "name": student.get("name", ""),
                    "course": student.get("course", ""),
                },
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
        )


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
        )


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
        )


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
        )


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
        )


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
        if month == 12:
            end_date = date(year + 1, 1, 1)
        else:
            end_date = date(year, month + 1, 1)
        end_date = (end_date - timedelta(days=1)).isoformat()

        # Obter códigos gerados no período
        async def get_firestore_codes():
            return await firestore_client.query_documents(
                "validation_codes",
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
        )
