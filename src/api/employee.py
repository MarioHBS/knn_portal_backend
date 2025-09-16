"""Implementação dos endpoints para o perfil de funcionário (employee)."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from src.auth import JWTPayload, validate_employee_role
from src.db import firestore_client, postgres_client, with_circuit_breaker
from src.models import (
    FavoriteRequest,
    FavoriteResponse,
    FavoritesResponse,
    Partner,
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
            enable_ordering=True,  # Habilitado para funcionários
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


@router.get("/me/fav", response_model=FavoritesResponse)
async def get_employee_favorites(
    current_user: JWTPayload = employee_dependency,
):
    """
    Retorna a lista de parceiros favoritos do funcionário.

    Utiliza a nova estrutura de coleções separadas (employees_fav).
    """
    try:
        employee_id = current_user.sub

        # Obter documento de favoritos do funcionário
        async def get_firestore_favorites():
            return await firestore_client.get_document("employees_fav", employee_id)

        async def get_postgres_favorites():
            return await postgres_client.get_document("employees_fav", employee_id)

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

            async def get_firestore_partner():
                return await firestore_client.get_document("partners", partner_id)

            async def get_postgres_partner():
                return await postgres_client.get_document("partners", partner_id)

            partner = await with_circuit_breaker(
                get_firestore_partner, get_postgres_partner
            )

            if partner and partner.get("active", False):
                favorite_partners.append(Partner(**partner))

        return {"data": favorite_partners, "msg": "ok"}

    except Exception as e:
        logger.error(f"Erro ao obter favoritos do funcionário: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "SERVER_ERROR",
                    "msg": "Erro ao obter favoritos do funcionário",
                }
            },
        ) from e


@router.post("/me/fav", response_model=FavoriteResponse)
async def add_employee_favorite(
    request: FavoriteRequest, current_user: JWTPayload = employee_dependency
):
    """
    Adiciona um parceiro à lista de favoritos do funcionário.

    Utiliza a nova estrutura de coleções separadas (employees_fav).
    """
    try:
        employee_id = current_user.sub
        partner_id_value = request.partner_id

        # Verificar se o parceiro existe e está ativo
        async def get_firestore_partner():
            return await firestore_client.get_document("partners", partner_id_value)

        async def get_postgres_partner():
            return await postgres_client.get_document("partners", partner_id_value)

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
            return await firestore_client.get_document("employees_fav", employee_id)

        async def get_postgres_favorites():
            return await postgres_client.get_document("employees_fav", employee_id)

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
            "id": employee_id,
            "favorites": current_favorites,
            "updated_at": datetime.now().isoformat(),
        }

        if favorites_doc:
            # Atualizar documento existente
            await firestore_client.update_document(
                "employees_fav",
                employee_id,
                {
                    "favorites": current_favorites,
                    "updated_at": datetime.now().isoformat(),
                },
            )
        else:
            # Criar novo documento
            await firestore_client.create_document(
                "employees_fav", favorites_data, employee_id
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
async def remove_employee_favorite(
    partner_id: str = Path(..., description="ID do parceiro"),
    current_user: JWTPayload = employee_dependency,
):
    """
    Remove um parceiro da lista de favoritos do funcionário.

    Utiliza a nova estrutura de coleções separadas (employees_fav).
    """
    try:
        employee_id = current_user.sub

        # Obter documento atual de favoritos
        async def get_firestore_favorites():
            return await firestore_client.get_document("employees_fav", employee_id)

        async def get_postgres_favorites():
            return await postgres_client.get_document("employees_fav", employee_id)

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
            "employees_fav",
            employee_id,
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
