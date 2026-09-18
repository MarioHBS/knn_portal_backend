"""
Implementação dos endpoints para o perfil de aluno (student).
"""

import random
import string
from datetime import datetime, timedelta

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Path,
    Query,
    status,
)

from src.auth import JWTPayload, validate_student_role
from src.db import firestore_client, postgres_client
from src.models import (
    FavoriteRequest,
    FavoriteResponse,
    FavoritesResponse,
    Partner,
    PartnerDetail,
    PartnerDetailResponse,
    PartnerListResponse,
    ValidationCode,
    ValidationCodeCreationRequest,
)
from src.utils import logger
from src.utils.partners_service import PartnersService

# Criar router
router = APIRouter(tags=["student"])


@router.get("/partners", response_model=PartnerListResponse)
async def list_partners(
    cat: str | None = Query(None, description="Filtro por categoria"),
    ord: str | None = Query(
        None,
        description="Ordenação dos resultados",
        enum=["name_asc", "name_desc", "category_asc", "category_desc"],
    ),
    limit: int = Query(
        20, ge=1, le=100, description="Número máximo de itens por página"
    ),
    offset: int = Query(0, ge=0, description="Offset para paginação"),
    current_user: JWTPayload = Depends(validate_student_role),
):
    """
    Lista parceiros com filtros e paginação.

    Endpoint específico para estudantes com as seguintes características:
    - Utiliza circuit breaker para alta disponibilidade
    - Ordenação desabilitada por padrão (para evitar necessidade de índices)
    - Acesso apenas a parceiros ativos
    """
    try:
        return await PartnersService.list_partners_common(
            current_user=current_user,
            cat=cat,
            ord=ord,
            limit=limit,
            offset=offset,
            use_circuit_breaker=True,  # Habilitado para estudantes
            enable_ordering=False,  # Desabilitado para evitar índices
        )

    except Exception as e:
        logger.error(f"Erro detalhado ao listar parceiros: {str(e)}", exc_info=True)
        logger.error(f"Tipo do erro: {type(e).__name__}")
        logger.error(f"Args do erro: {e.args}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "SERVER_ERROR",
                    "msg": f"Erro ao listar parceiros: {str(e)}",
                }
            },
        ) from e


@router.get("/partners/{id}", response_model=PartnerDetailResponse)
async def get_partner_details(
    id: str = Path(..., description="ID do parceiro"),
    current_user: JWTPayload = Depends(validate_student_role),
):
    """
    Retorna detalhes do parceiro e suas promoções ativas.
    """
    try:
        # Obter parceiro com circuit breaker
        async def get_firestore_partner():
            return await firestore_client.get_document(
                "partners", id, tenant_id=current_user.tenant
            )

        async def get_postgres_partner():
            return await postgres_client.get_document(
                "partners", id, tenant_id=current_user.tenant
            )

        partner = await get_firestore_partner()

        if not partner:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": {"code": "NOT_FOUND", "msg": "Parceiro não encontrado"}
                },
            )

        if not partner.get("active", False):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": {"code": "NOT_FOUND", "msg": "Parceiro não encontrado"}
                },
            )

        # Obter benefícios ativos do parceiro para alunos
        async def get_firestore_benefits():
            """Busca benefícios ativos do parceiro na coleção 'benefits'."""
            try:
                # Buscar documento do parceiro na coleção 'benefits'
                partner_doc = await firestore_client.get_document(
                    "benefits", id, tenant_id=current_user.tenant
                )

                if not partner_doc:
                    logger.warning(
                        f"Documento do parceiro {id} não encontrado na coleção 'benefits'"
                    )
                    return []

                # Extrair benefícios ativos para estudantes
                benefits = []
                benefit_keys = [key for key in partner_doc if key.startswith("BNF_")]

                for benefit_key in benefit_keys:
                    benefit_data = partner_doc[benefit_key]
                    system = benefit_data.get("system", {})
                    status = system.get("status", "")
                    audience = system.get("audience", "")

                    # Filtrar apenas benefícios ativos para estudantes
                    if status == "active":
                        # Verificar se audience inclui estudantes
                        audience_includes_students = False

                        # Converter audience para string se necessário para debug
                        audience_str = str(audience) if audience else ""
                        logger.debug(
                            f"Processando audience para benefício {benefit_key}: {audience_str} (tipo: {type(audience)})"
                        )

                        if (
                            audience == "all"
                            or audience == "students"
                            or audience == "student"
                        ):
                            audience_includes_students = True
                        elif isinstance(audience, list):
                            try:
                                audience_includes_students = "student" in audience
                            except TypeError as e:
                                logger.error(
                                    f"Erro ao verificar 'student' em audience {audience}: {e}"
                                )
                                audience_includes_students = False
                        elif isinstance(audience, str) and "student" in audience_str:
                            audience_includes_students = True

                        if audience_includes_students:
                            # Converter usando BenefitDTO
                            from src.models.benefit import BenefitDTO

                            try:
                                benefit_dto = BenefitDTO(
                                    key=benefit_key,
                                    benefit_data=benefit_data,
                                    partner_id=id,
                                )
                                benefit_obj = benefit_dto.to_benefit()
                                benefits.append(benefit_obj.model_dump())
                            except Exception as e:
                                logger.error(
                                    f"Erro ao converter benefício {benefit_key}: {str(e)}"
                                )

                return benefits

            except Exception as e:
                logger.error(f"Erro ao buscar benefícios do parceiro {id}: {str(e)}")
                return []

        async def get_postgres_benefits():
            """Busca benefícios no PostgreSQL (implementação futura se necessário)."""
            # Por enquanto, retorna lista vazia pois os benefícios estão no Firestore
            return []

        benefits_result = await get_firestore_benefits()

        # Recalcular benefits_count baseado nos benefícios filtrados
        filtered_benefits_count = len(benefits_result)

        # Construir a resposta final
        partner_detail = PartnerDetail(
            **partner,
            benefits=benefits_result,
            benefits_count=filtered_benefits_count,
        )

        return PartnerDetailResponse(data=partner_detail)

    except HTTPException as e:
        # Re-raise HTTP exceptions para que o FastAPI as manipule
        raise e
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
        ) from e


@router.post("/validation-codes", status_code=status.HTTP_201_CREATED)
async def create_validation_code(
    request: ValidationCodeCreationRequest,
    current_user: JWTPayload = Depends(validate_student_role),
):
    """
    Gera um código de validação de 6 dígitos para um parceiro.
    """
    try:
        # Gerar código de 6 dígitos
        validation_code = "".join(random.choices(string.digits, k=6))
        expires_at = datetime.utcnow() + timedelta(minutes=10)

        # Criar objeto ValidationCode
        code_data = ValidationCode(
            tenant_id=current_user.tenant,
            partner_id=request.partner_id,
            student_id=current_user.entity_id,  # Usar entity_id
            expires=expires_at,
        )

        # Salvar no Firestore, usando o código como ID do documento
        await firestore_client.create_document(
            "validation_codes",
            code_data.model_dump(mode="json"),
            doc_id=validation_code,
        )

        return {
            "code": validation_code,
            "expires": expires_at.isoformat(),
        }

    except Exception as e:
        logger.error(
            f"Erro ao criar código de validação para o parceiro {request.partner_id}: {str(e)}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "VALIDATION_CODE_CREATION_FAILED",
                    "msg": "Não foi possível gerar o código de validação.",
                }
            },
        ) from e


# Endpoints de Favoritos

@router.get("/fav", response_model=FavoritesResponse)
async def list_student_favorites(
    current_user: JWTPayload = Depends(validate_student_role),
):
    """
    Lista os parceiros favoritados pelo estudante.

    Coleção utilizada: students_fav (um documento por favorito).
    """
    try:
        # Buscar favoritos do estudante
        fav_result = await firestore_client.query_documents(
            "students_fav",
            tenant_id=current_user.tenant,
            filters=[("student_id", "==", current_user.entity_id)],
            limit=100,
        )

        favorite_partner_ids = [item.get("partner_id") for item in fav_result.get("items", [])]

        favorite_partners: list[Partner] = []
        for pid in favorite_partner_ids:
            if not pid:
                continue
            partner = await firestore_client.get_document(
                "partners", pid, tenant_id=current_user.tenant
            )
            if partner and partner.get("active", False):
                favorite_partners.append(Partner(**partner))

        return {"data": favorite_partners, "msg": "ok"}

    except Exception as e:
        logger.error(f"Erro ao listar favoritos do estudante: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "SERVER_ERROR",
                    "msg": "Erro ao listar favoritos do estudante",
                }
            },
        ) from e


@router.post("/fav", response_model=FavoriteResponse)
async def add_student_favorite(
    request: FavoriteRequest, current_user: JWTPayload = Depends(validate_student_role)
):
    """
    Adiciona um parceiro aos favoritos do estudante.

    Estrutura: um documento por favorito na coleção students_fav.
    """
    try:
        student_id = current_user.entity_id
        partner_id_value = request.partner_id

        # Verificar se o parceiro existe e está ativo
        partner = await firestore_client.get_document(
            "partners", partner_id_value, tenant_id=current_user.tenant
        )
        if not partner or not partner.get("active", False):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": {"code": "NOT_FOUND", "msg": "Parceiro não encontrado"}
                },
            )

        # ID composto para o documento de favorito
        favorite_doc_id = f"{student_id}_{partner_id_value}"

        # Verificar se já existe
        existing = await firestore_client.get_document(
            "students_fav", favorite_doc_id, tenant_id=current_user.tenant
        )
        # Calcular contagem atual de favoritos
        fav_count_result = await firestore_client.query_documents(
            "students_fav",
            tenant_id=current_user.tenant,
            filters=[("student_id", "==", student_id)],
            limit=1,
        )
        current_count = fav_count_result.get("total", 0)

        if existing:
            return FavoriteResponse(
                success=True,
                message="Parceiro já está nos favoritos",
                favorites_count=current_count,
            )

        # Criar documento
        from src.models.favorites import StudentPartnerFavorite

        favorite_data = StudentPartnerFavorite(
            student_id=student_id, partner_id=partner_id_value
        ).model_dump(mode="json")
        favorite_data["tenant_id"] = current_user.tenant

        await firestore_client.create_document(
            "students_fav", favorite_data, doc_id=favorite_doc_id
        )

        # Nova contagem após criação
        new_count_result = await firestore_client.query_documents(
            "students_fav",
            tenant_id=current_user.tenant,
            filters=[("student_id", "==", student_id)],
            limit=1,
        )
        new_count = new_count_result.get("total", current_count + 1)

        return FavoriteResponse(
            success=True,
            message="Parceiro adicionado aos favoritos com sucesso",
            favorites_count=new_count,
        )

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Erro ao adicionar favorito para o estudante: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "SERVER_ERROR",
                    "msg": "Erro ao adicionar favorito",
                }
            },
        ) from e


@router.delete("/fav/{partner_id}", response_model=FavoriteResponse)
async def remove_student_favorite(
    partner_id: str = Path(..., description="ID do parceiro"),
    current_user: JWTPayload = Depends(validate_student_role),
):
    """
    Remove um parceiro dos favoritos do estudante.
    """
    try:
        student_id = current_user.entity_id
        favorite_doc_id = f"{student_id}_{partner_id}"

        # Verificar existência do favorito
        existing = await firestore_client.get_document(
            "students_fav", favorite_doc_id, tenant_id=current_user.tenant
        )
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": {"code": "NOT_FOUND", "msg": "Favorito não encontrado"}
                },
            )

        # Remover documento
        await firestore_client.delete_document("students_fav", favorite_doc_id)

        # Contagem atualizada
        fav_count_result = await firestore_client.query_documents(
            "students_fav",
            tenant_id=current_user.tenant,
            filters=[("student_id", "==", student_id)],
            limit=1,
        )
        new_count = fav_count_result.get("total", 0)

        return FavoriteResponse(
            success=True,
            message="Parceiro removido dos favoritos com sucesso",
            favorites_count=new_count,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao remover favorito do estudante: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {"code": "SERVER_ERROR", "msg": "Erro ao remover favorito"}},
        ) from e
