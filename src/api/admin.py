"""
Implementação dos endpoints para o perfil de administrador (admin).
"""

import uuid
from copy import deepcopy
from datetime import UTC, datetime

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query, status
from firebase_admin import auth
from pydantic import BaseModel

from src.auth import JWTPayload, validate_admin_role
from src.config import EMAIL_SERVICE_ENABLED
from src.db import firestore_client, postgres_client, with_circuit_breaker
from src.db.firestore import db
from src.models import (
    BaseResponse,
    CollectionType,
    EntityResponse,
    EntityType,
    NotificationRequest,
    PartnerDetail,
    PartnerDetailResponse,
    UserModel,
)
from src.models.benefit import (
    BenefitConfigurationDTO,
    BenefitCreationDTO,
    BenefitFirestoreDTO,
    BenefitModel,
)
from src.models.employee import (
    EmployeeCreateDTO,
    EmployeeFirestoreDTO,
    EmployeeModel,
    EmployeeUpdateDTO,
)
from src.models.pagination import PaginatedResponse
from src.models.partner import (
    PartnerCreateDTO,
    PartnerDTO,
    PartnerModel,
    PartnerUpdateDTO,
)
from src.models.user import UserFirestoreDTO
from src.utils.auth_service import AuthService
from src.utils.email_service import EmailService
from src.utils.id_generators import IDGenerators
from src.utils.logging import logger
from src.utils.metrics_service import metrics_service
from src.utils.partners_service import PartnersService

# Criar router
router = APIRouter(tags=["admin"])

# ==========================================================================
# CRUD PARTNER


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
        await metrics_service.update_metadata_on_crud(
            CollectionType.PARTNER.value, current_user.tenant, operation="add", delta=1
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
        await metrics_service.update_metadata_on_crud(
            CollectionType.PARTNER.value,
            current_user.tenant,
            operation="remove",
            delta=1,
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


# ==========================================================================
# CRUD EMPLOYEE


@router.get("/employees", response_model=PaginatedResponse[EmployeeModel])
async def get_employee_list(
    limit: int = Query(10, ge=1, le=100, description="Limit per page"),
    offset: int = Query(0, ge=0, description="Offset to start from"),
    current_user: JWTPayload = Depends(validate_admin_role),
):
    """
    Lists all employees with pagination.
    """
    try:
        # Fetch the list of employees
        employee_list = await firestore_client.query_documents(
            "employees",
            tenant_id=current_user.tenant,
            limit=limit,
            offset=offset,
        )

        # Fetch the total count of documents
        total = await firestore_client.get_collection_count(
            "employees", tenant_id=current_user.tenant
        )

        # The model validator will handle the data transformation.
        items = [EmployeeModel(**item) for item in employee_list]
        logger.info(f"Fetched {len(items)} employees for tenant {current_user.tenant}")

        return PaginatedResponse[EmployeeModel](
            items=items,
            total=total,
            page=(offset // limit) + 1,
            per_page=limit,
            pages=(total + limit - 1) // limit if total > 0 else 1,
        )

    except Exception as e:
        logger.error(f"Error listing employees: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {"code": "SERVER_ERROR", "msg": "Error listing employees"}
            },
        ) from e


@router.get("/employees/{id}", response_model=EntityResponse[EmployeeModel])
async def get_employee_individual(
    id: str,
    current_user: JWTPayload = Depends(validate_admin_role),
):
    """
    Busca um funcionário pelo ID.
    """
    try:
        employee_data = await firestore_client.get_document(
            "employees", id, tenant_id=current_user.tenant
        )
        if not employee_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": {"code": "NOT_FOUND", "msg": "Funcionário não encontrado"}
                },
            )

        employee = EmployeeFirestoreDTO(**employee_data).to_employee(id)
        return EntityResponse(data=employee, msg="Funcionário encontrado com sucesso")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao buscar funcionário: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {"code": "SERVER_ERROR", "msg": "Erro ao buscar funcionário"}
            },
        ) from e


@router.put("/employees/{id}", response_model=EntityResponse[EmployeeModel])
async def set_employee_individual(
    id: str = Path(..., description="ID do funcionário"),
    employee_data: EmployeeUpdateDTO = Body(
        ..., description="Dados do funcionário para atualizar"
    ),
    current_user: JWTPayload = Depends(validate_admin_role),
):
    """
    Atualiza um funcionário existente.
    """
    try:
        # Verificar se o funcionário existe
        existing_employee = await firestore_client.get_document("employees", id)
        if (
            not existing_employee
            or existing_employee.get("tenant_id") != current_user.tenant
        ):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": {"code": "NOT_FOUND", "msg": "Funcionário não encontrado"}
                },
            )

        # Atualizar dados
        update_data = EmployeeFirestoreDTO.from_update(
            employee_data, datetime.now(UTC).isoformat()
        )

        await firestore_client.update_document("employees", id, update_data)

        # Obter dados atualizados
        updated_employee_data = await firestore_client.get_document("employees", id)
        employee = EmployeeFirestoreDTO(**updated_employee_data).to_employee(id)

        return EntityResponse[EmployeeModel](
            data=employee, msg="Funcionário atualizado com sucesso"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao atualizar funcionário: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "SERVER_ERROR",
                    "msg": "Erro ao atualizar funcionário",
                }
            },
        ) from e


@router.post("/employees", response_model=EntityResponse[EmployeeModel])
async def create_employee(
    employee_data: EmployeeCreateDTO = Body(..., description="Dados do funcionário"),
    current_user: JWTPayload = Depends(validate_admin_role),
):
    """
    Cria um novo funcionário.
    """
    logger.info(
        f"Recebida requisição para criar funcionário com dados: {employee_data.model_dump()}"
    )
    try:
        # 1. Gerar ID do funcionário
        generated_id = IDGenerators.gerar_id_funcionario(
            employee_data.name,
            employee_data.role,
            employee_data.zip,
            employee_data.phone,
        )
        logger.debug(f"ID de funcionário gerado: {generated_id}")

        # 2. Verificar se o funcionário já existe (pelo ID gerado ou e-mail)
        verify_existence(
            collection=CollectionType.EMPLOYEE,
            doc_id=generated_id,
            tenant_id=current_user.tenant,
        )

        employee_dto = EmployeeFirestoreDTO.from_create(
            create_data=employee_data, tenant=current_user.tenant
        )

        # Criar funcionário no Firestore
        logger.info(f"Criando funcionário no Firestore com ID: {generated_id}")
        result = await firestore_client.create_document(
            CollectionType.EMPLOYEE, doc_id=generated_id, data=employee_dto.model_dump()
        )
        logger.info(f"Funcionário criado com sucesso no Firestore: {result}")

        await create_firebase_user(
            entity=CollectionType.EMPLOYEE,
            entity_name=employee_dto.name,
            entity_email=employee_dto.email,
            entity_id=generated_id,
            tenant_id=employee_dto.tenant_id,
        )

        # Atualiza contadores agregados na coleção 'metadata'
        await metrics_service.update_metadata_on_crud(
            "employees", current_user.tenant, operation="add"
        )
        return EntityResponse[EmployeeModel](
            data=employee_dto.to_employee(generated_id),
            msg="Funcionário criado com sucesso",
        )

    except ValueError as e:
        logger.error(f"Erro de validação ao criar funcionário: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error": {"code": "VALIDATION_ERROR", "msg": str(e)}},
        ) from e
    except Exception as e:
        logger.error(f"Erro ao criar funcionário: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {"code": "SERVER_ERROR", "msg": "Erro ao criar funcionário"}
            },
        ) from e


@router.delete("/employees/{id}", response_model=BaseResponse)
async def delete_employee(
    id: str = Path(..., description="ID do funcionário"),
    current_user: JWTPayload = Depends(validate_admin_role),
):
    """
    Remove um funcionário existente.
    """
    try:
        # 1. Verifica a existência do funcionário no Firestore
        existing_employee = await verify_existence(
            CollectionType.EMPLOYEE, id, current_user.tenant
        )

        # 2. Deleta o usuário associado no Firebase Authentication e na coleção 'users' do Firestore
        await delete_firebase_user(
            entity=CollectionType.EMPLOYEE,
            entity_id=id,
            tenant_id=current_user.tenant,
        )

        # 3. Remove o documento do funcionário da coleção 'employees' no Firestore
        await firestore_client.delete_document(CollectionType.EMPLOYEE, id)

        # 4. Atualiza os contadores agregados na coleção 'metadata'
        await metrics_service.update_metadata_on_crud(
            CollectionType.EMPLOYEE.value, current_user.tenant, operation="sub", delta=1
        )

        return BaseResponse(msg=f"Funcionário {id} removido com sucesso")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao remover funcionário {id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "SERVER_ERROR",
                    "msg": "Erro ao remover funcionário",
                }
            },
        ) from e


# ==========================================================================
# CRUD BENEFIT


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
            BenefitFirestoreDTO(**item).to_benefit(id=item["id"])
            for item in benefit_list
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
            detail={"error": {"code": "SERVER_ERROR", "msg": "Error listing benefits"}},
        ) from e


@router.get("/benefits/{benefit_id}", response_model=EntityResponse[BenefitModel])
async def get_benefit_individual(
    benefit_id: str = Path(..., description="ID do benefício"),
    current_user: JWTPayload = Depends(validate_admin_role),
):
    """
    Obtém detalhes de um benefício específico pelo ID do benefício.

    Endpoint para administradores visualizarem benefícios específicos
    de qualquer parceiro do sistema usando apenas o ID do benefício.
    """
    try:
        logger.info(f"Admin {current_user.sub} buscando benefício {benefit_id}")

        async def get_benefit_from_firestore():
            logger.info(f"🔍 Iniciando busca do benefício {benefit_id}")
            logger.info(f"🔍 Tenant do usuário: {current_user.tenant}")

            # Buscar o benefício na coleção 'benefits' usando query
            # Como não temos o partner_id, precisamos buscar em todos os documentos
            result = await firestore_client.query_documents(
                "benefits",
                tenant_id=current_user.tenant,
                limit=1000,  # Limite alto para buscar em todos os documentos
                offset=0,
            )

            logger.info(
                f"🔍 Encontrados {len(result.get('items', []))} documentos de parceiros"
            )

            # Procurar o benefício em todos os documentos de parceiros
            for partner_doc in result.get("items", []):
                partner_id = partner_doc.get("id")
                logger.info(f"🔍 Verificando parceiro {partner_id}")

                # Verificar se o benefício existe neste documento
                benefit_data = partner_doc.get(benefit_id)

                if benefit_data:
                    logger.info(
                        f"✅ Benefício {benefit_id} encontrado no parceiro {partner_id}"
                    )

                    # Adicionar informações do parceiro e benefício
                    benefit_with_ids = {
                        **benefit_data,
                        "benefit_id": benefit_id,
                        "partner_id": partner_id,
                    }

                    return benefit_with_ids

            # Se chegou até aqui, o benefício não foi encontrado
            logger.warning(
                f"❌ Benefício {benefit_id} não encontrado em nenhum parceiro"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": {
                        "code": "BENEFIT_NOT_FOUND",
                        "msg": "Benefício não encontrado",
                    }
                },
            )

        benefit = await get_benefit_from_firestore()

        logger.info(f"Benefício {benefit_id} encontrado com sucesso")

        return {"data": benefit, "msg": "Benefício encontrado com sucesso"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao buscar benefício {benefit_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {"code": "SERVER_ERROR", "msg": "Erro interno do servidor"}
            },
        ) from e


@router.put("/benefits/{benefit_id}", response_model=EntityResponse[BenefitModel])
async def set_benefit_individual(
    benefit_id: str = Path(..., description="ID do benefício"),
    benefit_data: BenefitCreationDTO = Body(
        ..., description="Dados para atualização do benefício"
    ),
    current_user: JWTPayload = Depends(validate_admin_role),
):
    """
    Atualiza um benefício específico pelo ID do benefício.

    Endpoint para administradores atualizarem benefícios de qualquer parceiro
    usando apenas o ID do benefício, sem necessidade do partner_id.
    """
    try:
        logger.info(f"Admin {current_user.sub} atualizando benefício {benefit_id}")

        async def update_benefit_firestore():
            """Função interna para atualizar benefício no Firestore."""
            # Buscar o benefício existente para confirmar existência
            await verify_existence(
                collection=CollectionType.BENEFIT,
                entity_id=benefit_id,
                user_tenant=current_user.tenant,
            )

            # Converter documento existente para DTO
            # existing_benefit = BenefitFirestoreDTO(**existing_benefit_doc)
            # Preparar dados de atualização apenas com campos fornecidos
            update_data = benefit_data.prepare_to_update(updated_at=datetime.now(UTC))

            # Atualizar documento no Firestore
            await firestore_client.update_document(
                CollectionType.BENEFIT,
                benefit_id,
                update_data,
                tenant_id=current_user.tenant,
            )

            # Buscar documento atualizado
            updated_doc = await firestore_client.get_document(
                "benefits", benefit_id, tenant_id=current_user.tenant
            )

            # Converter para DTO e depois para modelo
            updated_benefit_dto = BenefitFirestoreDTO(**updated_doc)
            return updated_benefit_dto.to_benefit(benefit_id)

        async def update_benefit_postgres():
            """Função interna de fallback para PostgreSQL (placeholder)."""
            # Implementação placeholder para PostgreSQL
            # Em uma implementação real, seria necessário mapear os campos
            # do BenefitCreationDTO para a estrutura da tabela PostgreSQL
            return await postgres_client.update_document(
                "benefits",
                benefit_id,
                benefit_data.model_dump(exclude_none=True),
                tenant_id=current_user.tenant,
            )

        # Usar circuit breaker para executar a atualização
        result = await with_circuit_breaker(
            update_benefit_firestore, update_benefit_postgres
        )

        logger.info(f"Benefício {benefit_id} atualizado com sucesso")

        # Atualiza 'last_updated' na coleção 'metadata' (benefits)
        await metrics_service.update_last_updated_on_crud(
            CollectionType.BENEFIT, tenant_id=current_user.tenant
        )

        # Converter o benefício atualizado para o modelo de resposta
        return EntityResponse[BenefitModel](
            data=result, msg="Benefício atualizado com sucesso"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao atualizar benefício {benefit_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "SERVER_ERROR",
                    "msg": "Erro interno do servidor ao atualizar benefício",
                }
            },
        ) from e


@router.post("/benefits", response_model=EntityResponse[BenefitModel])
async def create_benefit(
    data: BenefitCreationDTO = Body(..., description="Dados do benefício"),
    current_user: JWTPayload = Depends(validate_admin_role),
):
    """
    Cria um novo benefício seguindo o novo formato da coleção 'benefits' no Firestore.
    """
    try:
        partner_id = data.partner_id
        tenant_id = current_user.tenant

        # Gerar ID do benefício baseado em timestamp + iniciais do parceiro
        iniciais = IDGenerators.extract_partner_initials_from_id(partner_id) or "XX"
        benefit_id = IDGenerators.gerar_id_beneficio_timestamp(
            iniciais_parceiro=iniciais, tipo_beneficio=data.type
        )

        now = datetime.now(UTC)

        firestore_benefit = BenefitFirestoreDTO(
            partner_id=partner_id,
            tenant_id=tenant_id,
            title=data.title,
            description=data.description,
            configuration=BenefitConfigurationDTO(
                value=data.value, value_type=data.value_type
            ),
            tags=data.tags,
            type=data.type,
            valid_from=data.valid_from,
            valid_until=data.valid_to,
            created_at=now,
            updated_at=now,
            audience=data.audience,
        )

        # Persistir no Firestore sob o documento do parceiro
        # Atenção: create_document muta o dicionário recebido (ex.: created_at = SERVER_TIMESTAMP)
        # Para evitar enviar objetos Sentinels na resposta (quebrando a serialização Pydantic),
        # passamos uma cópia para o Firestore e mantemos o original para retorno.
        the_benefit = firestore_benefit.model_dump(exclude_none=True)

        # Usar deepcopy para garantir que nenhuma mutação do cliente Firestore
        # afete o dicionário que retornaremos na resposta.
        await firestore_client.create_document(
            "benefits", deepcopy(the_benefit), benefit_id
        )

        # Atualiza contadores agregados na coleção 'metadata' (benefits)
        await metrics_service.update_metadata_on_crud(
            "benefits", tenant_id, operation="add", delta=1
        )

        return {
            "data": {
                "benefit_id": benefit_id,
                "partner_id": partner_id,
                "benefit": the_benefit,
            },
            "msg": "Benefício criado com sucesso",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao criar benefício: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {"code": "SERVER_ERROR", "msg": str(e)}},
        ) from e


@router.delete("/benefits/{partner_id}/{benefit_id}", response_model=BaseResponse)
async def delete_benefit(
    partner_id: str = Path(..., description="ID do parceiro"),
    benefit_id: str = Path(..., description="ID do benefício"),
    soft_delete: bool = Query(
        False, description="Usar soft delete (padrão: False - Hard Delete)"
    ),
    current_user: JWTPayload = Depends(validate_admin_role),
):
    """
    Exclui um benefício.

    - **Hard Delete**: Remove o benefício permanentemente.
    - **Soft Delete**: Marca o benefício como inativo.
    """
    try:
        # Lógica para encontrar o parceiro que contém o benefício
        partners_cursor = (
            db.collection_group("benefits").where("id", "==", benefit_id).stream()
        )
        partner_id = None
        for benefit_ref in partners_cursor:
            partner_ref = benefit_ref.reference.parent.parent
            partner_doc = partner_ref.get()
            if partner_doc.exists:
                partner_data = partner_doc.to_dict()
                if partner_data.get("tenant_id") == current_user.tenant:
                    partner_id = partner_doc.id
                    break

        if not partner_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": {
                        "code": "NOT_FOUND",
                        "msg": "Benefício não encontrado ou não pertence ao tenant",
                    }
                },
            )

        if soft_delete:
            # Soft delete: marcar como inativo
            await firestore_client.update_document(
                f"partners/{partner_id}/benefits", benefit_id, {"active": False}
            )
            msg = "Benefício desativado com sucesso (soft delete)"
        else:
            # Hard delete: remover permanentemente
            await firestore_client.delete_document(
                f"partners/{partner_id}/benefits", benefit_id
            )
            msg = "Benefício excluído com sucesso (hard delete)"

        return BaseResponse(msg=msg)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao excluir benefício: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {"code": "SERVER_ERROR", "msg": "Erro ao excluir benefício"}
            },
        ) from e


# ==========================================================================
# CRUD METRICS


async def get_metrics(current_user: JWTPayload = Depends(validate_admin_role)):
    """
    Retorna métricas e KPIs do sistema.
    """
    try:
        # Contar alunos ativos
        async def count_firestore_active_students():
            from datetime import date

            today = date.today().isoformat()

            result = await firestore_client.query_documents(
                "students",
                tenant_id=current_user.tenant,
                filters=[("active_until", ">=", today)],
                limit=1000,
            )
            return result.get("total", 0)

        async def count_postgres_active_students():
            from datetime import date

            today = date.today().isoformat()

            result = await postgres_client.query_documents(
                "students",
                tenant_id=current_user.tenant,
                filters=[("active_until", ">=", today)],
                limit=1000,
            )
            return result.get("total", 0)

        active_students = await with_circuit_breaker(
            count_firestore_active_students, count_postgres_active_students
        )

        # Contar códigos gerados
        async def count_firestore_codes():
            result = await firestore_client.query_documents(
                "validation_codes", tenant_id=current_user.tenant
            )
            return result.get("total", 0)

        async def count_postgres_codes():
            result = await postgres_client.query_documents(
                "validation_codes", tenant_id=current_user.tenant
            )
            return result.get("total", 0)

        codes_generated = await with_circuit_breaker(
            count_firestore_codes, count_postgres_codes
        )

        # Contar códigos resgatados
        async def count_firestore_redeemed_codes():
            result = await firestore_client.query_documents(
                "validation_codes",
                tenant_id=current_user.tenant,
                filters=[("used_at", "!=", None)],
            )
            return result.get("total", 0)

        async def count_postgres_redeemed_codes():
            result = await postgres_client.query_documents(
                "validation_codes",
                tenant_id=current_user.tenant,
                filters=[("used_at", "!=", None)],
            )
            return result.get("total", 0)

        codes_redeemed = await with_circuit_breaker(
            count_firestore_redeemed_codes, count_postgres_redeemed_codes
        )

        # Obter top parceiros
        # Simplificado: na implementação real, seria necessário agregar dados
        top_partners = []

        async def get_firestore_partners():
            return await firestore_client.query_documents(
                "partners",
                tenant_id=current_user.tenant,
                filters=[("active", "==", True)],
                limit=5,
            )

        async def get_postgres_partners():
            return await postgres_client.query_documents(
                "partners", filters=[("active", "==", True)], limit=5
            )

        partners_result = await with_circuit_breaker(
            get_firestore_partners, get_postgres_partners
        )

        for partner in partners_result.get("items", []):
            # Contar resgates para este parceiro
            partner_id = partner["id"]

            async def count_firestore_partner_redemptions(pid=partner_id):
                codes_result = await firestore_client.query_documents(
                    "validation_codes",
                    filters=[
                        ("partner_id", "==", pid),
                        ("used_at", "!=", None),
                    ],
                )
                return codes_result.get("total", 0)

            async def count_postgres_partner_redemptions(pid=partner_id):
                codes_result = await postgres_client.query_documents(
                    "validation_codes",
                    filters=[
                        ("partner_id", "==", pid),
                        ("used_at", "!=", None),
                    ],
                )
                return codes_result.get("total", 0)

            redemptions = await with_circuit_breaker(
                count_firestore_partner_redemptions, count_postgres_partner_redemptions
            )

            top_partners.append(
                {
                    "partner_id": partner_id,
                    "trade_name": partner.get("trade_name", ""),
                    "redemptions": redemptions,
                }
            )

        # Ordenar por número de resgates (decrescente)
        top_partners.sort(key=lambda x: x["redemptions"], reverse=True)

        return {
            "data": {
                "active_students": active_students,
                "codes_generated": codes_generated,
                "codes_redeemed": codes_redeemed,
                "top_partners": top_partners,
            },
            "msg": "ok",
        }

    except Exception as e:
        logger.error(f"Erro ao obter métricas: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {"code": "SERVER_ERROR", "msg": "Erro ao obter métricas"}},
        ) from e


# ==========================================================================
# CRUD NOTIFICATION


@router.post("/notifications", response_model=BaseResponse)
async def send_notifications(
    request: NotificationRequest,
    current_user: JWTPayload = Depends(validate_admin_role),
):
    """
    Envia notificações push/e-mail para alunos ou parceiros.
    """
    try:
        # Validar target
        if request.target not in ["students", "partners"]:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": {
                        "code": "INVALID_TARGET",
                        "msg": "Target deve ser 'students' ou 'partners'",
                    }
                },
            )

        # Validar tipo de notificação
        if request.type not in ["email", "push", "both"]:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": {
                        "code": "INVALID_TYPE",
                        "msg": "Type deve ser 'email', 'push' ou 'both'",
                    }
                },
            )

        # Obter destinatários
        filters = []

        # Aplicar filtros adicionais
        for key, value in request.filter.items():
            filters.append((key, "==", value))

        async def get_firestore_recipients():
            return await firestore_client.query_documents(
                request.target, filters=filters, tenant_id=current_user.tenant
            )

        async def get_postgres_recipients():
            return await postgres_client.query_documents(
                request.target, filters=filters, tenant_id=current_user.tenant
            )

        recipients_result = await with_circuit_breaker(
            get_firestore_recipients, get_postgres_recipients
        )

        recipients = recipients_result.get("items", [])

        # Simular envio de notificações
        # Em uma implementação real, seria integrado com serviço de e-mail/push
        message_id = str(uuid.uuid4())

        logger.info(
            f"Notificação {message_id} enviada para {len(recipients)} destinatários",
            target=request.target,
            type=request.type,
            message=request.message,
        )

        return {
            "data": {"recipients": len(recipients), "message_id": message_id},
            "msg": "ok",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao enviar notificações: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {"code": "SERVER_ERROR", "msg": "Erro ao enviar notificações"}
            },
        ) from e


# ==========================================================================
# UTILS
async def verify_existence(
    collection: CollectionType, entity_id: str, user_tenant: str
):
    mapping = {
        CollectionType.BENEFIT: "Benefício",
        CollectionType.PARTNER: "Parceiro",
        CollectionType.STUDENT: "Aluno",
        CollectionType.EMPLOYEE: "Funcionário",
    }
    existing = await firestore_client.get_document(
        collection, doc_id=entity_id, tenant_id=user_tenant
    )
    if not existing or existing.get("tenant_id") != user_tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "NOT_FOUND",
                    "msg": f"Usuário associado ao {mapping.get(collection, 'Entidade')} {entity_id} não encontrado no Firestore.",
                }
            },
        )


async def create_firebase_user(
    entity: EntityType,
    entity_name: str,
    entity_email: str,
    entity_id: str,
    tenant_id: str,
) -> auth.UserRecord:
    """Cria um usuário no Firebase Authentication e no Firestore."""
    auth_service = AuthService()
    user_record = None
    try:
        user_record, temp_password = auth_service.create_user_with_temp_password(
            email=entity_email, display_name=entity_name
        )

        # Criar documento na coleção 'users' do Firestore usando UserFirestoreDTO
        user_data = UserFirestoreDTO(
            email=entity_email,
            entity_id=entity_id,
            first_access=True,
            name=entity_name,
            role=entity.value,
            tenant_id=tenant_id,
            updated_at=datetime.now(UTC),
        )
        await firestore_client.create_document(
            CollectionType.USER, doc_id=user_record.uid, data=user_data.model_dump()
        )

        if EMAIL_SERVICE_ENABLED:
            # Enviar e-mail com a senha temporária
            email_service = EmailService()
            email_service.send_email(
                to_email=entity_email,
                subject="Bem-vindo ao KNN Portal Journey Club!",
                body=f"Olá {entity_name}, sua conta foi criada com sucesso. Sua senha temporária é: {temp_password}",
            )
        return user_record

    except Exception as e:
        logger.error(
            f"Erro ao criar usuário no Firebase para {entity.value} {entity_id}: {str(e)}"
        )
        # Reverter a criação do funcionário no Firestore
        await firestore_client.delete_document(entity.value, entity_id)
        if user_record:
            auth_service.delete_user(user_record.uid)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "FIREBASE_ERROR",
                    "msg": "Erro ao criar usuário de autenticação",
                }
            },
        ) from e


async def delete_firebase_user(
    entity: EntityType,
    entity_id: str,
    tenant_id: str,
) -> bool:
    """Deleta um usuário do Firebase Authentication e do Firestore."""
    auth_service = AuthService()
    try:
        user = await search_correspondent_user(entity, entity_id, tenant_id)
        logger.info(f"Usuário associado ao funcionário {user.uid}: {user}")

        try:
            # Busca o usuário no Firebase Authentication pelo e-mail
            user = auth.get_user(uid=user.uid)
            logger.info(f"Usuário encontrado: {user}")
            # Deleta o usuário no Firebase Authentication
            auth_service.delete_user(user.uid)
            logger.info(f"Usuário {user.uid} excluído do Firebase Authentication.")

        except Exception as e:
            logger.error(
                f"Erro ao excluir usuário do Firebase Authentication: {str(e)}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": {
                        "code": "AUTH_ERROR",
                        "msg": "Erro ao excluir usuário do Firebase Authentication",
                    }
                },
            ) from e

        # Deleta o documento do usuário na coleção 'users' do Firestore
        await firestore_client.delete_document(CollectionType.USER, doc_id=user.uid)

        # Deleta o documento da entidade na coleção correspondente
        # await firestore_client.delete_document(entity.value, doc_id=entity_id)

        return True

    except Exception as e:
        logger.error(
            f"Erro ao deletar usuário no Firebase para {entity} {entity_id}: {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "FIREBASE_DELETE_ERROR",
                    "msg": "Erro ao deletar usuário de autenticação",
                }
            },
        ) from e


async def search_correspondent_user(
    entity: EntityType, entity_id: str, tenant: str
) -> UserModel | None:
    """Busca o documento correspondente à entidade na coleção 'users' no Firestore."""
    user_docs = await firestore_client.query_documents(
        CollectionType.USER,
        tenant_id=tenant,
        filters=[("entity_id", "==", entity_id)],
        limit=1,
    )
    logger.info(f"Resposta da busca do usuário: {user_docs}")

    if not user_docs:
        logger.warning(
            f"Usuário associado ao {entity.value} {entity_id} não encontrado no Firestore."
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "NOT_FOUND",
                    "msg": f"Usuário associado ao {entity.value} {entity_id} não encontrado",
                }
            },
        )

    user_data = user_docs[0]
    user_data["uid"] = user_data.pop("id")
    return UserModel(**user_data)


def update_entity(
    entity_id: str, model: BaseModel, collection: CollectionType, tenant: str
) -> EntityResponse:
    """Atualiza um documento na coleção especificada."""
    try:
        # Converte o modelo para um dicionário
        update_data = model.model_dump(exclude_unset=True)

        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": {
                        "code": "UPDATE_ERROR",
                        "msg": f"Nenhum dado para atualizar {collection.value} {entity_id}",
                    }
                },
            )

        # Atualize metadado de atualização
        update_data["updated_at"] = datetime.now(UTC).isoformat()

        # Atualiza o documento no Firestore
        result = firestore_client.update_document(
            collection.value, entity_id, update_data, tenant_id=tenant
        )

        return EntityResponse(
            data=result, msg=f"{collection.value} {entity_id} atualizado com sucesso"
        )

    except Exception as e:
        logger.error(f"Erro ao atualizar {collection.value} {entity_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "UPDATE_ERROR",
                    "msg": f"Erro ao atualizar {collection.value} {entity_id}",
                }
            },
        ) from e
