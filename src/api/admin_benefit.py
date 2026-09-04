from datetime import UTC, datetime

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query, status

from src.api.admin import (
    verify_existence,
)
from src.auth import JWTPayload, validate_admin_role
from src.db.firestore import firestore_client
from src.models import (
    BaseResponse,
    CollectionType,
    EntityResponse,
)
from src.models.benefit import (
    BenefitCreateDTO,
    BenefitFirestoreDTO,
    BenefitModel,
)
from src.models.pagination import PaginatedResponse
from src.utils.id_generators import IDGenerators
from src.utils.logging import logger
from src.utils.metrics_service import CrudOperation, MetricsService

metrics_service_instance = MetricsService()

router = APIRouter(
    tags=["Admin - Benefits"], dependencies=[Depends(validate_admin_role)]
)


# .C. R U D
@router.post("/benefits", response_model=EntityResponse[BenefitModel])
async def create_benefit(
    create_data: BenefitCreateDTO = Body(..., description="Dados do benefício"),
    current_user: JWTPayload = Depends(validate_admin_role),
):
    """
    Cria um novo Benefício
    """
    partner_id = create_data.partner_id
    tenant_id = current_user.tenant
    try:
        # 1. Gerar ID do benefício baseado em timestamp + iniciais do parceiro
        benefit_id = IDGenerators.generate_benefit_id(
            iniciais_parceiro=IDGenerators.extract_partner_initials_from_id(partner_id)
            or "XX",
            tipo_beneficio=create_data.type,
        )

        # 2. Verificar se o benefício já existe (pelo ID gerado)
        await verify_existence(
            collection=CollectionType.PARTNER,
            entity_id=partner_id,
            user_tenant=tenant_id,
        )

        benefit_dto = BenefitFirestoreDTO.from_create(
            create_data=create_data, partner=partner_id, tenant=tenant_id
        )
        # CORREÇÃO: Usar mode='json' para serializar enums como strings simples
        dump = benefit_dto.model_dump(mode="json")
        logger.debug(f"Benefício a ser persistido: {dump}")

        # 3. Persistir no Firestore sob o documento do parceiro
        await firestore_client.create_document(
            collection=CollectionType.BENEFIT,
            doc_id=benefit_id,
            data=dump,
        )

        # 4. Atualizar contadores agregados na coleção 'metadata' (benefits)
        await metrics_service_instance.update_metadata_on_crud(
            CollectionType.BENEFIT, benefit_dto.tenant_id, operation=CrudOperation.ADD
        )

        return EntityResponse[BenefitModel](
            data=benefit_dto.to_model(id=benefit_id),
            msg="Benefício criado com sucesso",
        )

    except ValueError as e:
        logger.error(f"Erro de validação ao criar benefício: {str(e)}")
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
        logger.error(f"Erro ao criar benefício: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "SERVER_ERROR",
                    "msg": f"Erro interno do servidor ao criar benefício: {str(e)}",
                }
            },
        ) from e


@router.get("/benefits", response_model=PaginatedResponse[BenefitModel])
async def get_benefit_list(
    partner_id: str | None = Query(None, description="Filtrar por ID do parceiro"),
    limit: int = Query(10, ge=1, le=100, description="Limit per page"),
    offset: int = Query(0, ge=0, description="Offset to start from"),
    current_user: JWTPayload = Depends(validate_admin_role),
):
    """
    Lists all benefits with pagination.
    """
    from src.models.benefit import BenefitFirestoreDTO

    try:
        # Preparar filtros para a query
        filters = []
        if partner_id:
            filters.append(("partner_id", "==", partner_id))

        # Fetch the list of benefits
        benefit_list = await firestore_client.query_documents(
            "benefits",
            tenant_id=current_user.tenant,
            limit=limit,
            offset=offset,
            filters=filters,
        )

        # Fetch the total count of documents
        total = await firestore_client.get_collection_count(
            "benefits", tenant_id=current_user.tenant, filters=filters
        )

        benefits = [
            BenefitFirestoreDTO(**item).to_model(id=item["id"]) for item in benefit_list
        ]

        return PaginatedResponse[BenefitModel](
            items=benefits,
            total=total,
            page=(offset // limit) + 1,
            per_page=limit,
            pages=(total + limit - 1) // limit if total > 0 else 1,
        )

    except Exception as e:
        logger.error(f"Error listing benefits: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "SERVER_ERROR",
                    "msg": f"Erro ao listar benefÃ­cios: {str(e)}",
                }
            },
        ) from e


@router.get("/benefits/{benefit_id}", response_model=EntityResponse[BenefitModel])
async def get_benefit(
    benefit_id: str = Path(..., description="ID do benefÃ­cio"),
    current_user: JWTPayload = Depends(validate_admin_role),
):
    """
    ObtÃ©m um benefÃ­cio especÃ­fico pelo ID.
    """
    from src.models.benefit import BenefitFirestoreDTO

    try:
        benefit_data = await firestore_client.get_document(
            CollectionType.BENEFIT, benefit_id, tenant_id=current_user.tenant
        )
        if not benefit_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": {
                        "code": "NOT_FOUND",
                        "msg": "BenefÃ­cio nÃ£o encontrado",
                    }
                },
            )

        benefit = BenefitFirestoreDTO(**benefit_data).to_model(id=benefit_id)
        return EntityResponse[BenefitModel](data=benefit)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting benefit: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "SERVER_ERROR",
                    "msg": f"Erro ao obter benefÃ­cio: {str(e)}",
                }
            },
        ) from e


@router.put(
    "/benefits/{partner_id}/{benefit_id}", response_model=EntityResponse[BenefitModel]
)
async def update_benefit(
    partner_id: str = Path(..., description="ID do parceiro"),
    benefit_id: str = Path(..., description="ID do benefÃ­cio"),
    update_data: BenefitCreateDTO = Body(
        ..., description="Dados atualizados do benefÃ­cio"
    ),
    current_user: JWTPayload = Depends(validate_admin_role),
):
    """
    Atualiza um benefÃ­cio existente.
    """
    from src.models.benefit import BenefitFirestoreDTO

    try:
        # Verificar se o benefÃ­cio existe
        existing_benefit = await firestore_client.get_document(
            CollectionType.BENEFIT, benefit_id, tenant_id=current_user.tenant
        )
        if not existing_benefit:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": {
                        "code": "NOT_FOUND",
                        "msg": "BenefÃ­cio nÃ£o encontrado",
                    }
                },
            )

        # Criar DTO atualizado
        updated_dto = BenefitFirestoreDTO.from_create(
            create_data=update_data, partner=partner_id, tenant=current_user.tenant
        )
        updated_dto.created_at = existing_benefit.get("created_at", datetime.now(UTC))
        updated_dto.updated_at = datetime.now(UTC)

        # Atualizar no Firestore
        await firestore_client.update_document(
            CollectionType.BENEFIT, benefit_id, updated_dto.model_dump()
        )

        return EntityResponse[BenefitModel](
            data=updated_dto.to_model(id=benefit_id),
            msg="BenefÃ­cio atualizado com sucesso",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating benefit: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "SERVER_ERROR",
                    "msg": f"Erro ao atualizar benefÃ­cio: {str(e)}",
                }
            },
        ) from e


@router.delete("/benefits/{partner_id}/{benefit_id}")
async def delete_benefit(
    partner_id: str = Path(..., description="ID do parceiro"),
    benefit_id: str = Path(..., description="ID do benefÃ­cio"),
    current_user: JWTPayload = Depends(validate_admin_role),
):
    """
    Remove um benefÃ­cio.
    """
    try:
        # Verificar se o benefÃ­cio existe
        benefit = await firestore_client.get_document(
            CollectionType.BENEFIT, benefit_id, tenant_id=current_user.tenant
        )
        if not benefit:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": {
                        "code": "NOT_FOUND",
                        "msg": "BenefÃ­cio nÃ£o encontrado",
                    }
                },
            )

        # Remover do Firestore
        await firestore_client.delete_document(CollectionType.BENEFIT, benefit_id)

        # Atualizar contadores agregados na coleÃ§Ã£o 'metadata' (benefits)
        await metrics_service_instance.update_metadata_on_crud(
            CollectionType.BENEFIT, current_user.tenant, operation=CrudOperation.DELETE
        )

        return BaseResponse(msg="BenefÃ­cio removido com sucesso")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting benefit: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "SERVER_ERROR",
                    "msg": f"Erro ao remover benefÃ­cio: {str(e)}",
                }
            },
        ) from e
