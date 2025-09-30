"""
Implementação dos endpoints para o perfil de aluno (student).
"""

import random
import string
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from src.auth import JWTPayload, validate_student_role
from src.db import firestore_client, postgres_client, with_circuit_breaker
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
                benefit_keys = [
                    key for key in partner_doc.keys() if key.startswith("BNF_")
                ]

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


@router.get("/me/fav", response_model=FavoritesResponse)
async def list_favorites(current_user: JWTPayload = Depends(validate_student_role)):
    """
    Retorna a lista de parceiros favoritos do aluno.

    Utiliza a nova estrutura de coleções separadas (students_fav).
    """
    try:
        student_id = current_user.sub

        # Obter documento de favoritos do estudante
        async def get_firestore_favorites():
            return await firestore_client.get_document(
                "students_fav", student_id, tenant_id=current_user.tenant
            )

        async def get_postgres_favorites():
            return await postgres_client.get_document("students_fav", student_id)

        favorites_doc = await with_circuit_breaker(
            get_firestore_favorites, get_postgres_favorites
        )

        # Se não existe documento de favoritos, retornar lista vazia
        if not favorites_doc:
            return {"data": [], "msg": "ok"}

        # Obter lista de IDs dos parceiros favoritos
        favorite_partner_ids = favorites_doc.get("favorites", [])

        # Obter detalhes dos parceiros favoritos
        favorite_partners = []

        for partner_id in favorite_partner_ids:
            # Obter parceiro
            async def get_firestore_partner(pid=partner_id):
                return await firestore_client.get_document(
                    "partners", pid, tenant_id=current_user.tenant
                )

            async def get_postgres_partner(pid=partner_id):
                return await postgres_client.get_document(
                    "partners", pid, tenant_id=current_user.tenant
                )

            partner = await with_circuit_breaker(
                get_firestore_partner, get_postgres_partner
            )

            if partner and partner.get("active", False):
                favorite_partners.append(Partner(**partner))

        return {"data": favorite_partners, "msg": "ok"}

    except Exception as e:
        logger.error(f"Erro ao obter favoritos do aluno: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "SERVER_ERROR",
                    "msg": "Erro ao obter favoritos do aluno",
                }
            },
        ) from e


@router.post("/me/fav", response_model=FavoriteResponse)
async def add_student_favorite(
    request: FavoriteRequest, current_user: JWTPayload = Depends(validate_student_role)
):
    """
    Adiciona um parceiro à lista de favoritos do aluno.

    Utiliza a nova estrutura de coleções separadas (students_fav).
    """
    try:
        student_id = current_user.sub
        partner_id_value = request.partner_id

        # Verificar se o parceiro existe e está ativo
        async def get_firestore_partner():
            return await firestore_client.get_document(
                "partners", partner_id_value, tenant_id=current_user.tenant
            )

        async def get_postgres_partner():
            return await postgres_client.get_document(
                "partners", partner_id_value, tenant_id=current_user.tenant
            )

        partner = await with_circuit_breaker(
            get_firestore_partner, get_postgres_partner
        )

        if not partner or not partner.get("active", False):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": {"code": "NOT_FOUND", "msg": "Parceiro não encontrado"}
                },
            )

        # Obter documento atual de favoritos
        async def get_firestore_favorites():
            return await firestore_client.get_document(
                "students_fav", student_id, tenant_id=current_user.tenant
            )

        async def get_postgres_favorites():
            return await postgres_client.get_document("students_fav", student_id)

        favorites_doc = await with_circuit_breaker(
            get_firestore_favorites, get_postgres_favorites
        )

        current_favorites = []
        if favorites_doc:
            current_favorites = favorites_doc.get("favorites", [])

        # Verificar se já é favorito
        if partner_id_value in current_favorites:
            return FavoriteResponse(
                success=True,
                message="Parceiro já está nos favoritos",
                favorites_count=len(current_favorites),
            )

        # Adicionar aos favoritos
        current_favorites.append(partner_id_value)

        # Criar ou atualizar documento de favoritos
        favorites_data = {
            "id": student_id,
            "favorites": current_favorites,
            "updated_at": datetime.now().isoformat(),
        }

        if favorites_doc:
            # Atualizar documento existente
            await firestore_client.update_document(
                "students_fav",
                student_id,
                {
                    "favorites": current_favorites,
                    "updated_at": datetime.now().isoformat(),
                },
            )
        else:
            # Criar novo documento
            await firestore_client.create_document(
                "students_fav", favorites_data, student_id
            )

        return FavoriteResponse(
            success=True,
            message="Parceiro adicionado aos favoritos com sucesso",
            favorites_count=len(current_favorites),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao adicionar favorito: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {"code": "SERVER_ERROR", "msg": "Erro ao adicionar favorito"}
            },
        ) from e


@router.delete("/me/fav/{partner_id}", response_model=FavoriteResponse)
async def remove_student_favorite(
    partner_id: str = Path(..., description="ID do parceiro"),
    current_user: JWTPayload = Depends(validate_student_role),
):
    """
    Remove um parceiro da lista de favoritos do aluno.

    Utiliza a nova estrutura de coleções separadas (students_fav).
    """
    try:
        student_id = current_user.sub

        # Obter documento atual de favoritos
        async def get_firestore_favorites():
            return await firestore_client.get_document(
                "students_fav", student_id, tenant_id=current_user.tenant
            )

        async def get_postgres_favorites():
            return await postgres_client.get_document("students_fav", student_id)

        favorites_doc = await with_circuit_breaker(
            get_firestore_favorites, get_postgres_favorites
        )

        if not favorites_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": {"code": "NOT_FOUND", "msg": "Favorito não encontrado"}
                },
            )

        current_favorites = favorites_doc.get("favorites", [])

        # Verificar se o parceiro está nos favoritos
        if partner_id not in current_favorites:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": {"code": "NOT_FOUND", "msg": "Favorito não encontrado"}
                },
            )

        # Remover dos favoritos
        current_favorites.remove(partner_id)

        # Atualizar documento
        await firestore_client.update_document(
            "students_fav",
            student_id,
            {
                "favorites": current_favorites,
                "updated_at": datetime.now().isoformat(),
            },
        )

        return FavoriteResponse(
            success=True,
            message="Parceiro removido dos favoritos com sucesso",
            favorites_count=len(current_favorites),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao remover favorito: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {"code": "SERVER_ERROR", "msg": "Erro ao remover favorito"}
            },
        ) from e
