"""
Implementação dos endpoints para o perfil de parceiro (partner).
"""

import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from src.auth import JWTPayload, validate_partner_role
from src.config import CNPJ_HASH_SALT, RATE_LIMIT_REDEEM
from src.db import firestore_client, postgres_client, with_circuit_breaker
from src.models import (
    BaseResponse,
    BenefitListResponse,
    RedeemRequest,
    RedeemResponse,
    ReportResponse,
)
from src.models.benefit import Benefit, BenefitDTO, BenefitRequest, BenefitResponse
from src.utils import hash_cnpj, limiter, logger, validate_cnpj
from src.utils.id_generators import IDGenerators

# Criar router
router = APIRouter(tags=["partner"])


@router.post("/redeem", response_model=RedeemResponse)
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


@router.get("/promotions", response_model=BenefitListResponse)
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
        # Obter entity_id do JWT token (abordagem híbrida)
        partner_id = current_user.entity_id
        tenant_id = current_user.tenant
        logger.info(f"DEBUG - ID do Parceiro: {partner_id} - Tenant ID: {tenant_id}")

        # Buscar documento de benefícios do parceiro
        # Solução 1: Busca direta sem prefixo tenant_id no documento ID
        async def get_firestore_benefits():
            # Buscar diretamente pelo partner_id sem usar tenant_id no documento ID
            from src.db.firestore import get_database

            db = get_database()
            doc_ref = db.collection("benefits").document(partner_id)
            doc = doc_ref.get()

            if doc.exists:
                logger.info(
                    f"DEBUG - Beneficio encontrado diretamente para partner_id: {partner_id}"
                )
                return {"data": doc.to_dict()}
            else:
                logger.info(
                    f"DEBUG - Nenhum benefício encontrado para partner_id: {partner_id}"
                )
                return {"data": {}}

        async def get_postgres_benefits():
            return await postgres_client.get_document("benefits", partner_id)

        benefits_doc = await with_circuit_breaker(
            get_firestore_benefits, get_postgres_benefits
        )

        # Extrair benefícios do documento
        logger.info(f"DEBUG - Resultado da consulta Firestore: {benefits_doc}")
        benefits_data = benefits_doc.get("data", {}) if benefits_doc else {}

        # Debug: verificar tipo e estrutura dos dados
        logger.info(f"DEBUG - Tipo de benefits_data: {type(benefits_data)}")
        logger.info(f"DEBUG - Conteúdo de benefits_data: {benefits_data}")

        # Verificar se benefits_data é um dicionário
        if not isinstance(benefits_data, dict):
            logger.warning(
                f"DEBUG - benefits_data não é um dicionário, é: {type(benefits_data)}"
            )
            benefits_data = {}

        # Obter partner_id dos dados
        # partner_id = benefits_data.get("_partner_info", {}).get("partner_id", partner_id) # desnecessário

        # Função auxiliar para converter dados do Firestore
        def convert_firestore_data(data):
            """Converte dados do Firestore para formato compatível com Pydantic."""
            if isinstance(data, dict):
                converted = {k: convert_firestore_data(v) for k, v in data.items()}
                # Normalizar campo audience para string se for lista
                if "system" in converted and "audience" in converted["system"]:
                    audience = converted["system"]["audience"]
                    if isinstance(audience, list):
                        # Converter lista para string separada por vírgula
                        converted["system"]["audience"] = ",".join(audience)
                return converted
            elif hasattr(data, "timestamp"):  # DatetimeWithNanoseconds
                return data.timestamp()
            elif isinstance(data, list):
                return [convert_firestore_data(item) for item in data]
            else:
                return data

        # Filtrar apenas os campos que são benefícios (começam com BNF_)
        benefits_list = []
        for key, value in benefits_data.items():
            if key.startswith("BNF_") and isinstance(value, dict):
                try:
                    # Converter dados do Firestore para formato compatível
                    converted_value = convert_firestore_data(value)
                    benefit = BenefitDTO(
                        key=key, benefit_data=converted_value, partner_id=partner_id
                    ).to_benefit()
                    benefits_list.append(benefit)
                except Exception as e:
                    logger.warning(f"Erro ao processar benefício {key}: {str(e)}")
                    # Pular este benefício e continuar com os outros
                    continue

        # Ordenar por valid_to (mais recente primeiro)
        benefits_list.sort(
            key=lambda x: x.valid_to if x.valid_to else datetime.min, reverse=True
        )

        # Aplicar paginação
        paginated_benefits = benefits_list[offset : offset + limit]

        # Estrutura de resposta compatível com o formato esperado
        result = paginated_benefits

        return {"data": result, "msg": "ok"}

    except Exception as e:
        logger.error(f"Erro ao listar promoções: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {"code": "SERVER_ERROR", "msg": "Erro ao listar promoções"}
            },
        ) from None


@router.post("/promotions", response_model=BenefitResponse)
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
