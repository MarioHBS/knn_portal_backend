import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query, status

from src.api.admin import (
    create_firebase_user,
    delete_firebase_user,
    update_entity,
    verify_existence,
)
from src.auth import JWTPayload, validate_admin_role
from src.db.circuit_breaker import with_circuit_breaker
from src.db.firestore import firestore_client
from src.db.postgres import postgres_client
from src.models import (
    BaseResponse,
    CollectionType,
    EntityResponse,
    EntityType,
    PartnerDetail,
    PartnerDetailResponse,
)
from src.models.pagination import PaginatedResponse
from src.models.partner import (
    PartnerCreateDTO,
    PartnerDTO,
    PartnerModel,
    PartnerUpdateDTO,
)
from src.utils.id_generators import IDGenerators
from src.utils.logging import logger
from src.utils.metrics_service import CrudOperation, MetricsService
from src.utils.partners_service import PartnersService

metrics_service_instance = MetricsService()

router = APIRouter(
    tags=["Admin - Partners"], dependencies=[Depends(validate_admin_role)]
)


@router.get(
    "/partners",
    response_model=PaginatedResponse[PartnerModel],
    summary="Lista parceiros com filtros e paginação",
)
async def get_partner_list(
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
    current_user: JWTPayload = Depends(validate_admin_role),
):
    """
    Lista parceiros com filtros e paginação.

    Endpoint específico para administradores com as seguintes características:
    - Utiliza circuit breaker para alta disponibilidade
    - Ordenação habilitada por padrão
    - Acesso a todos os parceiros (ativos e inativos)
    """
    try:
        partners, total = await PartnersService.list_partners_common(
            current_user=current_user,
            cat=cat,
            ord=ord,
            limit=limit,
            offset=offset,
            use_circuit_breaker=False,  # Desabilitado para usar apenas Firestore
            enable_ordering=True,  # Habilitado após criação do índice composto
        )
        return PaginatedResponse(
            items=partners,
            total=total,
            page=offset // limit + 1,
            per_page=limit,
            pages=(total + limit - 1) // limit,
        )

    except Exception as e:
        logger.error(f"Erro detalhado ao listar parceiros: {str(e)}", exc_info=True)
        logger.error(f"Tipo do erro: {type(e).__name__}")
        logger.error(f"Args do erro: {e.args}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {"code": "INTERNAL_ERROR", "msg": "Erro interno do servidor"}
            },
        ) from e


@router.get("/partners/{id}", response_model=EntityResponse[PartnerModel])
async def get_partner_individual(
    id: str = Path(..., description="ID do parceiro"),
    current_user: JWTPayload = Depends(validate_admin_role),
) -> PartnerDetailResponse:
    """
    Obtém detalhes completos de um parceiro específico.
    Administradores podem ver detalhes de qualquer parceiro.
    """
    try:
        # Buscar parceiro
        async def get_firestore_partner():
            return await firestore_client.get_document(
                "partners", id, tenant_id=current_user.tenant
            )

        async def get_postgres_partner():
            return await postgres_client.get_document(
                "partners", id, tenant_id=current_user.tenant
            )

        partner_data = await with_circuit_breaker(
            get_firestore_partner, get_postgres_partner
        )

        if not partner_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": {"code": "NOT_FOUND", "msg": "Parceiro não encontrado"}
                },
            )

        # Garantir que logo_url esteja presente, usando placeholder se necessário
        partner_raw_data = partner_data.get("data", partner_data)
        if not partner_raw_data.get("logo_url"):
            partner_raw_data["logo_url"] = "/data/placeholder.png"

        # Criar objeto PartnerDetail
        partner_detail = PartnerDetail(**partner_raw_data)

        return PartnerDetailResponse(data=partner_detail)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Erro ao obter detalhes do parceiro {id} para administrador {current_user.sub}: {e}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {"code": "INTERNAL_ERROR", "msg": "Erro interno do servidor"}
            },
        ) from e


@router.put("/partners/{id}", response_model=EntityResponse)
async def set_partner_individual(
    id: str,
    data: PartnerUpdateDTO = Body(..., description="Dados do parceiro para atualizar"),
    current_user: JWTPayload = Depends(validate_admin_role),
):
    """
    Atualiza um parceiro existente.
    """
    try:
        # Verificar se o parceiro existe
        verify_existence(
            collection=CollectionType.PARTNER,
            entity_id=id,
            tenant_id=current_user.tenant,
        )

        return update_entity(
            entity_id=id,
            model=data,
            collection=CollectionType.PARTNER,
            tenant=current_user.tenant,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao atualizar parceiro: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {"code": "SERVER_ERROR", "msg": "Erro ao atualizar parceiro"}
            },
        ) from e


@router.post("/partners", response_model=EntityResponse[PartnerModel])
async def create_partner(
    data: PartnerCreateDTO = Body(..., description="Dados do parceiro"),
    current_user: JWTPayload = Depends(validate_admin_role),
):
    """
    Cria um novo parceiro.
    """
    try:
        # 1. Gerar ID do parceiro
        try:
            partner_id = IDGenerators.generate_partner_id(
                trade_name=data.trade_name,
                category=str(data.category),
                cnpj=data.cnpj,
            )
        except Exception:
            partner_id = str(uuid.uuid4())

        # 2. Verificar se o parceiro já existe
        verify_existence(
            collection=CollectionType.PARTNER,
            entity_id=partner_id,
            tenant_id=current_user.tenant,
        )

        existing_user_by_email = await firestore_client.query_documents(
            collection=CollectionType.USER.value,
            filters=[("email", "==", data.email)],
            tenant_id=current_user.tenant,
        )
        if existing_user_by_email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": {
                        "code": "EMAIL_ALREADY_IN_USE",
                        "msg": "Já existe um usuário com este e-mail.",
                    }
                },
            )

        # 3. Criar usuário no Firebase e na coleção 'users'
        await create_firebase_user(
            entity=EntityType.PARTNER,
            entity_name=data.trade_name,
            entity_email=data.email,
            entity_id=partner_id,
            tenant_id=current_user.tenant,
        )

        # 4. Preparar e salvar dados do parceiro no Firestore
        current_time = datetime.now(UTC).isoformat()
        partner_data = PartnerDTO.to_firestore(data, current_time, current_time)

        if not partner_data.logo_url:
            partner_data.logo_url = "/data/placeholder.png"

        await firestore_client.create_document(
            CollectionType.PARTNER.value, partner_data.model_dump(), partner_id
        )

        # 5. Atualizar metadados
        await metrics_service_instance.update_metadata_on_crud(
            CollectionType.PARTNER, current_user.tenant, operation=CrudOperation.ADD
        )

        # 6. Retornar resposta
        created_partner_doc = await firestore_client.get_document(
            CollectionType.PARTNER.value, partner_id
        )
        if not created_partner_doc:
            raise HTTPException(
                status_code=500, detail="Falha ao recuperar parceiro após a criação."
            )

        partner_model = PartnerModel(**created_partner_doc)

        return EntityResponse(data=partner_model, msg="Parceiro criado com sucesso")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao criar parceiro: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {"code": "SERVER_ERROR", "msg": "Erro ao criar parceiro"}},
        ) from e


@router.delete("/partners/{id}", response_model=BaseResponse)
async def delete_partner(
    id: str,
    current_user: JWTPayload = Depends(validate_admin_role),
):
    """
    Exclui um parceiro existente.
    """
    try:
        # 1. Verificar a existência do parceiro
        await verify_existence(CollectionType.PARTNER, id, current_user.tenant)

        # 2. Deletar usuário do Firebase e da coleção 'users'
        await delete_firebase_user(EntityType.PARTNER, id, current_user.tenant)

        # 3. Deletar o documento do parceiro do Firestore
        await firestore_client.delete_document(CollectionType.PARTNER.value, id)

        # 4. Atualizar metadados
        await metrics_service_instance.update_metadata_on_crud(
            CollectionType.PARTNER, current_user.tenant, operation=CrudOperation.SUB
        )

        return BaseResponse(msg="Parceiro deletado com sucesso")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao excluir parceiro: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {"code": "SERVER_ERROR", "msg": "Erro ao excluir parceiro"}
            },
        ) from e
