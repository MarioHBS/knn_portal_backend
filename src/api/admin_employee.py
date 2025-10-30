from datetime import UTC, datetime

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query, status

from src.api.admin import (
    create_firebase_user,
    delete_firebase_user,
    verify_existence,
)
from src.auth import JWTPayload, validate_admin_role
from src.db.firestore import firestore_client
from src.models import (
    BaseResponse,
    CollectionType,
    EntityResponse,
)
from src.models.employee import (
    EmployeeCreateDTO,
    EmployeeFirestoreDTO,
    EmployeeModel,
    EmployeeUpdateDTO,
)
from src.models.pagination import PaginatedResponse
from src.utils.id_generators import IDGenerators
from src.utils.logging import logger
from src.utils.metrics_service import CrudOperation, MetricsService

metrics_service_instance = MetricsService()

router = APIRouter(
    tags=["Admin - Employees"], dependencies=[Depends(validate_admin_role)]
)


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
        await metrics_service_instance.update_metadata_on_crud(
            CollectionType.EMPLOYEE, current_user.tenant, operation=CrudOperation.ADD
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
        await verify_existence(CollectionType.EMPLOYEE, id, current_user.tenant)

        # 2. Deleta o usuário associado no Firebase Authentication e na coleção 'users' do Firestore
        await delete_firebase_user(
            entity=CollectionType.EMPLOYEE,
            entity_id=id,
            tenant_id=current_user.tenant,
        )

        # 3. Remove o documento do funcionário da coleção 'employees' no Firestore
        await firestore_client.delete_document(CollectionType.EMPLOYEE, id)

        # 4. Atualiza os contadores agregados na coleção 'metadata'
        await metrics_service_instance.update_metadata_on_crud(
            CollectionType.EMPLOYEE, current_user.tenant, operation=CrudOperation.SUB
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
