"""
Implementação dos endpoints para o perfil de aluno (student).
"""

import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from src.auth import JWTPayload, validate_student_role
from src.db import firestore_client, postgres_client, with_circuit_breaker
from src.models import (
    BaseResponse,
    FavoritesResponse,
    HistoryResponse,
    Partner,
    PartnerDetail,
    PartnerDetailResponse,
    PartnerListResponse,
    ValidationCodeRequest,
    ValidationCodeResponse,
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
            enable_ordering=False,     # Desabilitado para evitar índices
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
            return await firestore_client.get_document("partners", id)

        async def get_postgres_partner():
            return await postgres_client.get_document("partners", id)

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

        # Obter promoções ativas do parceiro para alunos
        now = datetime.now().isoformat()

        async def get_firestore_promotions():
            return await firestore_client.query_documents(
                "promotions",
                filters=[
                    ("partner_id", "==", id),
                    ("active", "==", True),
                    ("valid_from", "<=", now),
                    ("valid_to", ">=", now),
                    ("audience", "array_contains_any", ["student"]),
                ],
                tenant_id=current_user.tenant,
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
                tenant_id=current_user.tenant,
            )

        promotions_result = await get_firestore_promotions()

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
        ) from e


@router.post("/validation-codes", response_model=ValidationCodeResponse)
async def create_validation_code(
    request: ValidationCodeRequest,
    current_user: JWTPayload = Depends(validate_student_role),
):
    """
    Gera um código de validação de 6 dígitos que expira em 3 minutos.
    """
    try:
        # Verificar se o parceiro existe e está ativo
        async def get_firestore_partner():
            return await firestore_client.get_document("partners", request.partner_id)

        async def get_postgres_partner():
            return await postgres_client.get_document("partners", request.partner_id)

        partner = await get_firestore_partner()

        if not partner or not partner.get("active", False):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": {"code": "NOT_FOUND", "msg": "Parceiro não encontrado"}
                },
            )

        # Verificar se o aluno está ativo
        student_id = current_user.sub

        async def get_firestore_student():
            return await firestore_client.get_document("students", student_id)

        async def get_postgres_student():
            return await postgres_client.get_document("students", student_id)

        student = await get_firestore_student()

        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": {"code": "NOT_FOUND", "msg": "Aluno não encontrado"}},
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

        # Gerar código de 6 dígitos
        import random

        code = str(random.randint(100000, 999999))

        # Calcular data de expiração (3 minutos)
        expires = datetime.now() + timedelta(minutes=3)

        # Criar código de validação no Firestore
        validation_code = {
            "id": str(uuid.uuid4()),
            "student_id": student_id,
            "partner_id": request.partner_id,
            "code_hash": code,  # Em produção, deve ser hash
            "expires": expires.isoformat(),
            "used_at": None,
        }

        await firestore_client.create_document(
            "validation_codes", validation_code, validation_code["id"]
        )

        # Retornar código e data de expiração
        return {"data": {"code": code, "expires": expires.isoformat()}, "msg": "ok"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao gerar código de validação: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "SERVER_ERROR",
                    "msg": "Erro ao gerar código de validação",
                }
            },
        ) from e


@router.get("/students/me/history", response_model=HistoryResponse)
async def get_student_history(
    limit: int = Query(
        20, ge=1, le=100, description="Número máximo de itens por página"
    ),
    offset: int = Query(0, ge=0, description="Offset para paginação"),
    current_user: JWTPayload = Depends(validate_student_role),
):
    """
    Retorna o histórico de resgates do aluno.
    """
    try:
        student_id = current_user.sub

        # Obter códigos de validação usados pelo aluno
        async def get_firestore_codes():
            return await firestore_client.query_documents(
                "validation_codes",
                tenant_id=current_user.tenant,
                filters=[("student_id", "==", student_id), ("used_at", "!=", None)],
                order_by=[("used_at", "DESCENDING")],
                limit=limit,
                offset=offset,
            )

        async def get_postgres_codes():
            return await postgres_client.query_documents(
                "validation_codes",
                filters=[("student_id", "==", student_id), ("used_at", "!=", None)],
                order_by=[("used_at", "DESCENDING")],
                limit=limit,
                offset=offset,
                tenant_id=current_user.tenant,
            )

        codes_result = await get_firestore_codes()

        # Construir histórico com detalhes de parceiros e resgates
        history_items = []

        for code in codes_result.get("items", []):
            # Obter parceiro
            async def get_firestore_partner(current_code=code):
                return await firestore_client.get_document(
                    "partners", current_code["partner_id"]
                )

            async def get_postgres_partner(current_code=code):
                return await postgres_client.get_document(
                    "partners", current_code["partner_id"]
                )

            partner = await get_firestore_partner()

            if not partner:
                continue

            # Obter resgate
            async def get_firestore_redemption(current_code=code):
                redemptions = await firestore_client.query_documents(
                    "redemptions",
                    filters=[("validation_code_id", "==", current_code["id"])],
                    limit=1,
                )
                return (
                    redemptions.get("items", [])[0]
                    if redemptions.get("items")
                    else None
                )

            async def get_postgres_redemption(current_code=code):
                redemptions = await postgres_client.query_documents(
                    "redemptions",
                    filters=[("validation_code_id", "==", current_code["id"])],
                    limit=1,
                )
                return (
                    redemptions.get("items", [])[0]
                    if redemptions.get("items")
                    else None
                )

            redemption = await get_firestore_redemption()

            if not redemption:
                continue

            # Obter promoção (opcional)
            promotion_title = "Promoção"

            # Adicionar ao histórico
            history_items.append(
                {
                    "id": redemption["id"],
                    "partner": {
                        "id": partner["id"],
                        "trade_name": partner["trade_name"],
                    },
                    "promotion": {"title": promotion_title},
                    "value": redemption["value"],
                    "used_at": code["used_at"],
                }
            )

        return {
            "data": {
                "items": history_items,
                "total": codes_result.get("total", 0),
                "limit": limit,
                "offset": offset,
            },
            "msg": "ok",
        }

    except Exception as e:
        logger.error(f"Erro ao obter histórico do aluno: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "SERVER_ERROR",
                    "msg": "Erro ao obter histórico do aluno",
                }
            },
        ) from e


@router.get("/students/me/fav", response_model=FavoritesResponse)
async def get_student_favorites(
    current_user: JWTPayload = Depends(validate_student_role),
):
    """
    Retorna a lista de parceiros favoritos do aluno.
    """
    try:
        student_id = current_user.sub

        # Obter favoritos do aluno
        async def get_firestore_favorites():
            return await firestore_client.query_documents(
                "favorites",
                filters=[("student_id", "==", student_id)],
                tenant_id=current_user.tenant,
            )

        async def get_postgres_favorites():
            return await postgres_client.query_documents(
                "favorites",
                filters=[("student_id", "==", student_id)],
                tenant_id=current_user.tenant,
            )

        favorites_result = await get_firestore_favorites()

        # Obter detalhes dos parceiros favoritos
        favorite_partners = []

        for favorite in favorites_result.get("items", []):
            partner_id = favorite.get("partner_id")

            if not partner_id:
                continue

            # Obter parceiro
            async def get_firestore_partner(pid=partner_id):
                return await firestore_client.get_document("partners", pid)

            async def get_postgres_partner(pid=partner_id):
                return await postgres_client.get_document("partners", pid)

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


@router.post("/students/me/fav", response_model=BaseResponse)
async def add_student_favorite(
    partner_id: dict, current_user: JWTPayload = Depends(validate_student_role)
):
    """
    Adiciona um parceiro à lista de favoritos do aluno.
    """
    try:
        student_id = current_user.sub
        partner_id_value = partner_id.get("partner_id")

        if not partner_id_value:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "msg": "ID do parceiro é obrigatório",
                    }
                },
            )

        # Verificar se o parceiro existe e está ativo
        async def get_firestore_partner():
            return await firestore_client.get_document("partners", partner_id_value)

        async def get_postgres_partner():
            return await postgres_client.get_document("partners", partner_id_value)

        partner = await get_firestore_partner()

        if not partner or not partner.get("active", False):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": {"code": "NOT_FOUND", "msg": "Parceiro não encontrado"}
                },
            )

        # Verificar se já é favorito
        async def get_firestore_favorite():
            favorites = await firestore_client.query_documents(
                "favorites",
                filters=[
                    ("student_id", "==", student_id),
                    ("partner_id", "==", partner_id_value),
                ],
                limit=1,
            )
            return favorites.get("items", [])[0] if favorites.get("items") else None

        async def get_postgres_favorite():
            favorites = await postgres_client.query_documents(
                "favorites",
                filters=[
                    ("student_id", "==", student_id),
                    ("partner_id", "==", partner_id_value),
                ],
                limit=1,
            )
            return favorites.get("items", [])[0] if favorites.get("items") else None

        existing_favorite = await get_firestore_favorite()

        if existing_favorite:
            return {"msg": "ok"}

        # Adicionar aos favoritos
        favorite = {
            "id": str(uuid.uuid4()),
            "student_id": student_id,
            "partner_id": partner_id_value,
            "created_at": datetime.now().isoformat(),
        }

        await firestore_client.create_document("favorites", favorite, favorite["id"])

        return {"msg": "ok"}

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


@router.delete("/students/me/fav/{pid}", response_model=BaseResponse)
async def remove_student_favorite(
    pid: str = Path(..., description="ID do parceiro"),
    current_user: JWTPayload = Depends(validate_student_role),
):
    """
    Remove um parceiro da lista de favoritos do aluno.
    """
    try:
        student_id = current_user.sub

        # Verificar se é favorito
        async def get_firestore_favorite():
            favorites = await firestore_client.query_documents(
                "favorites",
                filters=[("student_id", "==", student_id), ("partner_id", "==", pid)],
                limit=1,
            )
            return favorites.get("items", [])[0] if favorites.get("items") else None

        async def get_postgres_favorite():
            favorites = await postgres_client.query_documents(
                "favorites",
                filters=[("student_id", "==", student_id), ("partner_id", "==", pid)],
                limit=1,
            )
            return favorites.get("items", [])[0] if favorites.get("items") else None

        favorite = await get_firestore_favorite()

        if not favorite:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": {
                        "code": "NOT_FOUND",
                        "msg": "Parceiro não encontrado nos favoritos",
                    }
                },
            )

        # Remover dos favoritos
        await firestore_client.delete_document("favorites", favorite["id"])

        return {"msg": "ok"}

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
