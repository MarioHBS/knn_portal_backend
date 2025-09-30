"""
Implementação dos endpoints para o perfil de parceiro (partner).
"""

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request, status

from src.auth import JWTPayload, validate_partner_role
from src.config import RATE_LIMIT_REDEEM
from src.db import firestore_client, postgres_client, with_circuit_breaker
from src.db.unified_client import UnifiedDatabaseClient
from src.models import (
    BaseResponse,
    RedeemResponse,
    ReportResponse,
)
from src.models.benefit import Benefit, BenefitDTO, BenefitRequest, BenefitResponse
from src.models.validation_code import ValidationCode, ValidationCodeRedeemRequest
from src.utils import limiter, logger
from src.utils.id_generators import IDGenerators

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
        partner_doc = await db.get_document("partners", partner_id, tenant_id=current_user.tenant)
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
            logger.warning(f"Código de validação '{redeem_request.code}' não encontrado.")
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
                status_code=status.HTTP_410_GONE, detail=f"Código '{redeem_request.code}' expirado."
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
            student_doc = await db.get_document("students", student_id, tenant_id=current_user.tenant)
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


@router.post("/promotions", response_model=BenefitResponse, status_code=201)
async def create_promotion(
    promotion_data: BenefitRequest,
    current_user: JWTPayload = Depends(validate_partner_role),
):
    """
    Cria uma nova promoção para o parceiro.
    """
    try:
        # Obter entity_id do JWT token (abordagem híbrida)
        partner_id = current_user.entity_id
        tenant_id = current_user.tenant

        # Validar datas
        if promotion_data.valid_from >= promotion_data.valid_to:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": {
                        "code": "INVALID_DATES",
                        "msg": "Data de início deve ser anterior à data de término",
                    }
                },
            )

        # Extrair iniciais do entity_id do parceiro para gerar ID do benefício
        # Formato do entity_id: PTN_T4L5678_TEC -> extrair T4L5678 -> TL
        def extrair_iniciais_do_entity_id(entity_id: str) -> str:
            """Extrai as iniciais da parte central do entity_id do parceiro.

            Args:
                entity_id: ID da entidade no formato PTN_XXXXXXX_XXX

            Returns:
                Iniciais extraídas (apenas letras)
            """
            try:
                # Dividir o entity_id pelas underscores
                partes = entity_id.split("_")
                if len(partes) >= 2:
                    # Pegar a parte central (ex: T4L5678)
                    parte_central = partes[1]
                    # Extrair apenas as letras
                    iniciais = "".join([c for c in parte_central if c.isalpha()])
                    return iniciais.upper()
                return "XX"  # Fallback
            except Exception:
                return "XX"  # Fallback em caso de erro

        partner_iniciais = extrair_iniciais_do_entity_id(partner_id)

        # Gerar ID do benefício usando o novo método baseado em timestamp
        # Não precisa mais consultar benefícios existentes para contagem
        benefit_id = IDGenerators.gerar_id_beneficio_timestamp(
            iniciais_parceiro=partner_iniciais, tipo_beneficio=promotion_data.type
        )

        # Criar estrutura do benefício compatível com o modelo Benefit
        benefit_data = {
            "id": benefit_id,
            "partner_id": partner_id,
            "tenant_id": tenant_id,
            "title": promotion_data.title,
            "type": promotion_data.type,
            "valid_from": promotion_data.valid_from.isoformat(),
            "valid_to": promotion_data.valid_to.isoformat(),
            "active": promotion_data.active,
            "audience": promotion_data.audience,
            "created_at": datetime.now(UTC).isoformat(),
            "updated_at": datetime.now(UTC).isoformat(),
            # Adicionar campos obrigatórios do modelo Benefit
            "value": getattr(promotion_data, "discount_percentage", 0) or 0,
            "value_type": "percentage",
            "tags": [],
        }

        # Criar estrutura para salvar no Firestore usando BenefitDTO
        benefit_obj = Benefit(**benefit_data)
        firestore_data = BenefitDTO.from_benefit(benefit_obj)

        # Buscar documento de benefícios do parceiro
        # Usar o mesmo método que o GET /partner/promotions usa
        async def get_firestore_benefits():
            from src.db.firestore import get_database

            db = get_database()
            doc_ref = db.collection("benefits").document(partner_id)
            doc = doc_ref.get()

            if doc.exists:
                logger.info(
                    f"Documento de benefícios encontrado para partner_id: {partner_id}"
                )
                return {"data": doc.to_dict()}
            else:
                logger.info(
                    f"Documento de benefícios não encontrado para partner_id: {partner_id}"
                )
                return None

        async def get_postgres_benefits():
            return await postgres_client.get_document("benefits", partner_id)

        benefits_doc = await with_circuit_breaker(
            get_firestore_benefits, get_postgres_benefits
        )

        # Atualizar documento de benefícios do parceiro com o novo benefício
        # Usar benefit_data do DTO em vez do objeto DTO completo
        update_data = {benefit_id: firestore_data.benefit_data}

        if benefits_doc:
            # Documento existe, atualizar com merge
            await firestore_client.update_document("benefits", partner_id, update_data)
        else:
            # Documento não existe, criar novo
            await firestore_client.create_document("benefits", update_data, partner_id)

        return {"data": benefit_obj, "msg": "ok"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao criar promoção: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {"code": "SERVER_ERROR", "msg": "Erro ao criar promoção"}},
        ) from e


@router.put("/promotions/{id}", response_model=BenefitResponse)
async def update_promotion(
    id: str = Path(..., description="ID da promoção"),
    promotion_data: BenefitRequest = None,
    current_user: JWTPayload = Depends(validate_partner_role),
):
    """
    Atualiza uma promoção existente do parceiro.
    """
    try:
        # Obter entity_id do JWT token (abordagem híbrida)
        partner_id = current_user.entity_id
        tenant_id = current_user.tenant

        # Buscar documento de benefícios do parceiro
        async def get_firestore_benefits():
            from src.db.firestore import get_database

            db = get_database()
            doc_ref = db.collection("benefits").document(partner_id)
            doc = doc_ref.get()

            if doc.exists:
                logger.info(
                    f"Documento de benefícios encontrado para partner_id: {partner_id}"
                )
                return {"data": doc.to_dict()}
            else:
                logger.info(
                    f"Documento de benefícios não encontrado para partner_id: {partner_id}"
                )
                return None

        async def get_postgres_benefits():
            return await postgres_client.get_document("benefits", partner_id)

        benefits_doc = await with_circuit_breaker(
            get_firestore_benefits, get_postgres_benefits
        )

        if not benefits_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": {
                        "code": "NOT_FOUND",
                        "msg": "Documento de benefícios não encontrado",
                    }
                },
            )

        # Verificar se o benefício específico existe
        benefits_data = benefits_doc.get("data", {})
        if id not in benefits_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": {"code": "NOT_FOUND", "msg": "Promoção não encontrada"}
                },
            )

        # Verificar se o benefício pertence ao parceiro
        existing_benefit = benefits_data[id]

        # Como o partner_id não está mais armazenado no benefit_data (foi removido para evitar redundância),
        # e o benefício está no documento do partner_id, podemos assumir que pertence ao parceiro
        # A verificação de acesso já foi feita ao buscar o documento pelo partner_id do token JWT

        # Validar datas
        if promotion_data.valid_from >= promotion_data.valid_to:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": {
                        "code": "INVALID_DATES",
                        "msg": "Data de início deve ser anterior à data de término",
                    }
                },
            )

        # Atualizar benefício mantendo dados originais e estrutura aninhada
        updated_benefit = existing_benefit.copy()

        logger.info(f"DEBUG - Dados originais do benefício {id}: {existing_benefit}")

        # Atualizar campos no nível raiz
        updated_benefit["title"] = promotion_data.title

        # Atualizar campos no system
        if "system" not in updated_benefit:
            updated_benefit["system"] = {}
        updated_benefit["system"]["type"] = promotion_data.type
        updated_benefit["system"]["status"] = (
            "active" if promotion_data.active else "inactive"
        )

        # Converter audience de lista para formato Firestore (string)
        audience_mapping = {
            frozenset(["student"]): "students",
            frozenset(["employee"]): "employees",
            frozenset(["student", "employee"]): "all",
        }
        firestore_audience = audience_mapping.get(
            frozenset(promotion_data.audience), "students"
        )
        updated_benefit["system"]["audience"] = firestore_audience

        # Atualizar campos nas dates
        if "dates" not in updated_benefit:
            updated_benefit["dates"] = {}
        updated_benefit["dates"]["valid_from"] = promotion_data.valid_from.isoformat()
        updated_benefit["dates"]["valid_until"] = promotion_data.valid_to.isoformat()
        updated_benefit["dates"]["updated_at"] = datetime.now(UTC).isoformat()

        # Atualizar documento com o benefício modificado
        update_data = {id: updated_benefit}
        await firestore_client.update_document("benefits", partner_id, update_data)

        # Converter o benefício atualizado para o modelo Benefit para a resposta
        benefit_dto = BenefitDTO(
            key=id, benefit_data=updated_benefit, partner_id=partner_id
        )
        benefit_obj = benefit_dto.to_benefit()

        return {"data": benefit_obj, "msg": "ok"}

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


@router.delete("/promotions/{id}", response_model=BaseResponse)
async def delete_promotion(
    id: str = Path(..., description="ID da promoção"),
    current_user: JWTPayload = Depends(validate_partner_role),
):
    """
    Remove uma promoção existente do parceiro usando hard delete.
    """
    try:
        logger.info(f"Iniciando delete_promotion para ID: {id}")

        # Obter entity_id do JWT token (abordagem híbrida)
        partner_id = current_user.entity_id
        tenant_id = current_user.tenant

        logger.info(f"Partner ID: {partner_id}, Tenant ID: {tenant_id}")

        # Buscar documento de benefícios do parceiro para verificar se existe
        # Usar o mesmo método que o GET /partner/promotions usa
        async def get_firestore_benefits():
            from src.db.firestore import get_database

            db = get_database()

            # Debug: Tentar diferentes formas de buscar o documento
            logger.info(f"Tentando buscar documento com ID: {partner_id}")

            # Método 1: Busca direta (como no GET)
            doc_ref = db.collection("benefits").document(partner_id)
            doc = doc_ref.get()

            if doc.exists:
                logger.info(f"✅ Documento encontrado com busca direta: {partner_id}")
                return {"data": doc.to_dict()}
            else:
                logger.info(
                    f"❌ Documento não encontrado com busca direta: {partner_id}"
                )

                # Debug: Listar todos os documentos na coleção benefits
                logger.info("Listando todos os documentos na coleção benefits:")
                benefits_collection = db.collection("benefits")
                all_docs = benefits_collection.limit(10).stream()

                for doc in all_docs:
                    logger.info(f"  - Documento ID: {doc.id}")

                return None

        async def get_postgres_benefits():
            return await postgres_client.get_document("benefits", partner_id)

        logger.info("Buscando documento de benefícios...")
        benefits_doc = await with_circuit_breaker(
            get_firestore_benefits, get_postgres_benefits
        )

        logger.info(f"Documento encontrado: {benefits_doc is not None}")

        if not benefits_doc:
            logger.warning("Documento de benefícios não encontrado")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": {
                        "code": "NOT_FOUND",
                        "msg": "Documento de benefícios não encontrado",
                    }
                },
            )

        # Verificar se o benefício específico existe
        benefits_data = benefits_doc.get("data", {})
        logger.info(f"Benefícios disponíveis: {list(benefits_data.keys())}")

        if id not in benefits_data:
            logger.warning(f"Promoção {id} não encontrada nos benefícios")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": {"code": "NOT_FOUND", "msg": "Promoção não encontrada"}
                },
            )

        # Verificar se o benefício pertence ao parceiro
        # Como o partner_id não é salvo no nível raiz do benefício no Firestore,
        # vamos usar uma abordagem alternativa: verificar se o benefício está no documento
        # do parceiro (que já é uma indicação de propriedade) e se o tenant_id corresponde
        existing_benefit = benefits_data[id]
        existing_partner_id = existing_benefit.get("partner_id")
        benefit_tenant_id = existing_benefit.get("system", {}).get("tenant_id")

        logger.info(f"🔍 DEBUG - Partner ID do usuário: {partner_id}")
        logger.info(f"🔍 DEBUG - Partner ID do benefício: {existing_partner_id}")
        logger.info(f"🔍 DEBUG - Tenant ID do usuário: {tenant_id}")
        logger.info(f"🔍 DEBUG - Tenant ID do benefício: {benefit_tenant_id}")

        # Verificação de propriedade: o benefício deve estar no documento do parceiro
        # e ter o mesmo tenant_id (isso garante que pertence ao parceiro correto)
        if benefit_tenant_id != tenant_id:
            logger.warning(
                f"❌ Acesso negado: tenant_id do benefício ({benefit_tenant_id}) != tenant_id do usuário ({tenant_id})"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": {
                        "code": "FORBIDDEN",
                        "msg": "Acesso negado a esta promoção",
                    }
                },
            )

        logger.info(
            f"✅ Verificação de propriedade passou: benefício pertence ao parceiro {partner_id}"
        )

        # Remover o campo específico do documento usando delete_field
        success = await firestore_client.delete_field("benefits", partner_id, id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": {
                        "code": "DELETE_FAILED",
                        "msg": "Falha ao remover promoção do Firestore",
                    }
                },
            )

        logger.info(f"Promoção {id} removida com sucesso para parceiro {partner_id}")
        return {"msg": "ok"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao remover promoção {id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {"code": "SERVER_ERROR", "msg": "Erro ao remover promoção"}
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
