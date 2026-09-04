from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query, status
from pydantic_core import ValidationError

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
    PartnerFirestoreDTO,
    PartnerModel,
    PartnerUpdateDTO,
)
from src.utils.id_generators import IDGenerators
from src.utils.logging import logger
from src.utils.metrics_service import CrudOperation, MetricsService

metrics_service_instance = MetricsService()

router = APIRouter(
    tags=["Admin - Partners"], dependencies=[Depends(validate_admin_role)]
)


# .C. R U D
@router.post("/partners", response_model=EntityResponse[PartnerModel])
async def create_partner(
    create_data: PartnerCreateDTO = Body(..., description="Dados do Parceiro"),
    current_user: JWTPayload = Depends(validate_admin_role),
):
    """
    Cria um Parceiro.
    """
    logger.info(
        f"Recebida requisição para criar parceiro com dados: {create_data.model_dump()}"
    )
    try:
        # 1. Gerar ID do parceiro
        partner_id = IDGenerators.generate_partner_id(
            create_data.trade_name,
            create_data.cnpj,
            str(create_data.category),
        )
        logger.debug(f"ID gerado do parceiro: {partner_id}")

        # 2. Verificar se o parceiro já existe
        await verify_existence(
            CollectionType.PARTNER,
            partner_id,
            current_user.tenant,
        )

        partner_dto = PartnerFirestoreDTO.from_create(
            create_data=create_data, tenant=current_user.tenant
        )

        # 3. Cria Parceiro na coleção 'partners'
        logger.info(f"Criando Parceiro no Firestore com ID: {partner_id}")
        await firestore_client.create_document(
            collection=CollectionType.PARTNER,
            doc_id=partner_id,
            data=partner_dto.model_dump(),
        )
        logger.info(f"Parceiro criado com sucesso: {partner_id}")

        # 4. Criar usuário no Firebase Authentication e na coleção 'users'
        await create_firebase_user(
            entity=EntityType.PARTNER,
            entity_name=partner_dto.trade_name,
            entity_email=partner_dto.email,
            entity_id=partner_id,
            tenant_id=partner_dto.tenant_id,
        )

        # 5. Atualizar contadores agregados na coleção 'metadata'
        await metrics_service_instance.update_metadata_on_crud(
            CollectionType.PARTNER, partner_dto.tenant_id, operation=CrudOperation.ADD
        )

        # 6. Retornar resposta
        return EntityResponse(
            data=partner_dto.to_model(partner_id), msg="Parceiro criado com sucesso"
        )

    except ValueError as e:
        logger.error(f"Erro de validação ao criar parceiro: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "msg": f"Erro de validação: {str(e)}",
                }
            },
        ) from e
    except Exception as e:
        logger.error(f"Erro inesperado ao criar parceiro: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "SERVER_ERROR",
                    "msg": "Erro interno do servidor ao criar parceiro",
                }
            },
        ) from e


# C .R. U D
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
    Lista todos os Parceiros com paginação.

    Endpoint específico para administradores com as seguintes características:
    - Utiliza circuit breaker para alta disponibilidade
    - Ordenação habilitada por padrão
    - Acesso a todos os parceiros (ativos e inativos)
    """
    try:
        logger.info("🔍 INICIANDO BUSCA DE PARCEIROS")
        logger.info(
            f"📋 Parâmetros: limit={limit}, offset={offset}, tenant={current_user.tenant}"
        )

        # 1. Buscar lista de parceiros
        items = await firestore_client.query_documents(
            CollectionType.PARTNER.value,
            tenant_id=current_user.tenant,
            limit=limit,
            offset=offset,
        )
        logger.info(f"📊 Query retornou {len(items)} documentos")

        if items:
            logger.info(
                f"📝 Primeiro documento: {items[0].get('id', 'sem_id')} - {items[0].get('trade_name', 'sem_nome')}"
            )
        else:
            logger.warning("⚠️ Nenhum documento retornado pela query!")

        partners = []
        for i, item in enumerate(items):
            try:
                logger.info(
                    f"🔄 Processando parceiro {i+1}/{len(items)}: {item.get('id', 'sem_id')}"
                )
                partner_model = PartnerFirestoreDTO(**item).to_model(
                    item.get("id", "unknown")
                )
                partners.append(partner_model)
                logger.info(f"✅ Parceiro {i+1} processado com sucesso")
            except ValidationError as e:
                partner_id = item.get("id", "sem_id")
                logger.error(
                    f"❌ Pydantic Validation Error for partner ID {partner_id}: {e}, Data: {item}"
                )
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail={
                        "error": {
                            "code": "VALIDATION_ERROR",
                            "msg": f"Validation error for partner ID {partner_id}: {e}",
                        }
                    },
                ) from e

        logger.info(f"✅ Parceiros processados: {len(partners)}")

        # 2. Obter a contagem total de parceiros
        logger.info("🔄 Obtendo contagem total...")
        total = await firestore_client.get_collection_count(
            CollectionType.PARTNER.value, tenant_id=current_user.tenant
        )
        logger.info(f"📊 Contagem total: {total}")

        # 3. Criar resposta paginada
        pages = (total + limit - 1) // limit if limit > 0 else 0
        page = (offset // limit) + 1

        logger.info(
            f"📄 Criando resposta paginada: items={len(partners)}, total={total}, page={page}, per_page={limit}, pages={pages}"
        )

        response = PaginatedResponse[PartnerModel](
            items=partners,
            total=total,
            page=page,
            per_page=limit,
            pages=pages,
        )

        logger.info(f"✅ RESPOSTA FINAL: {len(response.items)} parceiros retornados")
        return response

    except Exception as e:
        logger.error(f"❌ Error listing students: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {"code": "SERVER_ERROR", "msg": "Error listing students"}},
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
        await verify_existence(
            collection=CollectionType.PARTNER,
            entity_id=id,
            user_tenant=current_user.tenant,
        )

        return await update_entity(
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


@router.delete("/partners/{id}", response_model=BaseResponse)
async def delete_partner(
    id: str,
    current_user: JWTPayload = Depends(validate_admin_role),
):
    """
    Exclui um parceiro pelo ID.
    """
    try:
        # 1. Verifica a existência do parceiro
        await verify_existence(CollectionType.PARTNER, id, current_user.tenant)

        # 2. Exclui usuário associado no Firebase Authentication e na coleção 'users' do Firestore
        await delete_firebase_user(EntityType.PARTNER, id, current_user.tenant)

        # 3. Exclui o documento associado da coleção 'partners'
        await firestore_client.delete_document(CollectionType.PARTNER.value, id)

        # 4. Atualizar contadores agregados na coleção 'metadata'
        await metrics_service_instance.update_metadata_on_crud(
            CollectionType.PARTNER, current_user.tenant, operation=CrudOperation.SUB
        )

        return BaseResponse(msg=f"Parceiro {id} excluído com sucesso")

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


# =================================================================
# AUXILIARES


async def _set_partner_status(
    partner_id: str, tenant_id: str, is_active: bool
) -> BaseResponse:
    """
    Define o status de ativação de um parceiro.
    """
    try:
        # 1. Verificar se o parceiro existe
        await verify_existence(CollectionType.PARTNER, partner_id, tenant_id)

        # 2. Atualizar o status 'is_active' no Firestore
        await firestore_client.update_document(
            collection=CollectionType.PARTNER,
            doc_id=partner_id,
            data={"is_active": is_active},
        )

        status_msg = "ativado" if is_active else "desativado"
        logger.info(f"Parceiro {partner_id} {status_msg} com sucesso.")
        return BaseResponse(msg=f"Parceiro {partner_id} {status_msg} com sucesso.")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Erro ao {'ativar' if is_active else 'desativar'} parceiro {partner_id}: {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "SERVER_ERROR",
                    "msg": f"Erro ao {'ativar' if is_active else 'desativar'} parceiro",
                }
            },
        ) from e


@router.post("/partners/{id}/activate", response_model=BaseResponse)
async def activate_partner(
    id: str = Path(..., description="ID do parceiro a ser ativado"),
    current_user: JWTPayload = Depends(validate_admin_role),
):
    """
    Ativa um parceiro existente.
    """
    return await _set_partner_status(id, current_user.tenant, True)


@router.post("/partners/{id}/deactivate", response_model=BaseResponse)
async def deactivate_partner(
    id: str = Path(..., description="ID do parceiro a ser desativado"),
    current_user: JWTPayload = Depends(validate_admin_role),
):
    """
    Desativa um parceiro existente.
    """
    return await _set_partner_status(id, current_user.tenant, False)
