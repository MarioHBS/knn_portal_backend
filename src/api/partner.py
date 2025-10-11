"""
Implementação dos endpoints para o perfil de parceiro (partner).
"""

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from src.auth import JWTPayload, validate_partner_role
from src.config import RATE_LIMIT_REDEEM
from src.db import firestore_client, postgres_client, with_circuit_breaker
from src.db.unified_client import UnifiedDatabaseClient
from src.models import (
    RedeemResponse,
    ReportResponse,
)
from src.models.validation_code import ValidationCodeRedeemRequest
from src.utils import limiter, logger

# Criar router
router = APIRouter(tags=["partner"])


@router.post("/redeem", response_model=RedeemResponse)
@limiter.limit(RATE_LIMIT_REDEEM)
async def redeem_code(
    request: Request,
    redeem_request: ValidationCodeRedeemRequest,
    current_user: JWTPayload = Depends(validate_partner_role),
):
    """
    Resgata um código de validação gerado por um aluno.
    Limitado a 5 requisições por minuto por IP.
    """
    try:
        db = UnifiedDatabaseClient()
        partner_id = current_user.entity_id
        logger.info(f"Partner ID from token: {partner_id}")
        logger.info(f"Tenant from token: {current_user.tenant}")

        # 1. Buscar o parceiro para verificar o CNPJ
        partner_doc = await db.get_document(
            "partners", partner_id, tenant_id=current_user.tenant
        )
        if not partner_doc or partner_doc.get("cnpj") != redeem_request.cnpj:
            logger.warning(
                f"Tentativa de resgate com CNPJ incorreto. "
                f"Parceiro: {partner_id}, CNPJ enviado: {redeem_request.cnpj}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CNPJ não corresponde ao parceiro autenticado.",
            )

        # 2. Buscar código de validação pelo ID do documento
        code_data = await db.get_document(
            "validation_codes", redeem_request.code, tenant_id=current_user.tenant
        )

        if not code_data:
            logger.warning(
                f"Código de validação '{redeem_request.code}' não encontrado."
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Código '{redeem_request.code}' não encontrado.",
            )

        # O ID do documento é o próprio código
        code_id = redeem_request.code
        code_data["id"] = code_id

        # 3. Validar o código
        # Validar se o código pertence ao parceiro correto
        if code_data.get("partner_id") != partner_id:
            logger.warning(
                f"Código '{redeem_request.code}' não pertence ao parceiro autenticado. "
                f"Parceiro no token: {partner_id}, "
                f"Parceiro no código: {code_data.get('partner_id')}"
            )
            # Retorna 404 para não vazar a informação de que o código existe.
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Código '{redeem_request.code}' não encontrado.",
            )

        if code_data.get("used_at"):
            logger.warning(f"Código '{redeem_request.code}' já foi resgatado.")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Código '{redeem_request.code}' já foi resgatado.",
            )

        expires_at = code_data.get("expires_at")
        if expires_at and datetime.now(UTC) > expires_at:
            logger.warning(f"Código '{redeem_request.code}' está expirado.")
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail=f"Código '{redeem_request.code}' expirado.",
            )

        # 4. Atualizar o código como resgatado
        redeemed_time = datetime.now(UTC)
        await db.update_document(
            collection="validation_codes",
            doc_id=code_id,
            data={
                "used_at": redeemed_time,
                "redeemed_by_partner_id": partner_id,
            },
            tenant_id=current_user.tenant,
        )

        # 5. Buscar nome do aluno para a resposta
        student_id = code_data.get("student_id")
        user_name = "Aluno não encontrado"
        if student_id:
            student_doc = await db.get_document(
                "students", student_id, tenant_id=current_user.tenant
            )
            if student_doc:
                user_name = student_doc.get("name", "Nome não disponível")

        logger.info(
            f"Código {redeem_request.code} resgatado com sucesso pelo parceiro {partner_id}"
        )

        return RedeemResponse(
            data={
                "user_name": user_name,
                "redeemed_at": redeemed_time.isoformat(),
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao resgatar código: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "msg": "Ocorreu um erro inesperado ao resgatar o código",
                }
            },
        ) from e


@router.get("/reports", response_model=ReportResponse)
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
                "benefits", filters=[("partner_id", "==", partner_id)]
            )

        async def get_postgres_promotions():
            return await postgres_client.query_documents(
                "benefits", filters=[("partner_id", "==", partner_id)]
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
                "benefits": promotion_stats,
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
