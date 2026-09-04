from datetime import UTC, datetime

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query, status
from pydantic_core import ValidationError

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
    EntityType,
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


# .C. R U D
@router.post("/employees", response_model=EntityResponse[EmployeeModel])
async def create_employee(
    employee_data: EmployeeCreateDTO = Body(..., description="Dados do funcionário"),
    current_user: JWTPayload = Depends(validate_admin_role),
):
    """
    Cria um Funcionário.
    """
    logger.info(
        f"Recebida requisição para criar funcionário com dados: {employee_data.model_dump()}"
    )
    try:
        # 1. Gerar ID do funcionário
        generated_id = IDGenerators.generate_employee_id(
            employee_data.name,
            employee_data.role,
            employee_data.zip,
            employee_data.phone,
            employee_data.email,
        )
        logger.debug(f"ID de funcionário gerado: {generated_id}")

        # 2. Verificar se o funcionário já existe (pelo ID gerado ou e-mail)
        # Passamos should_exist=False para garantir que NÃO exista (evitar duplicatas)
        await verify_existence(
            collection=CollectionType.EMPLOYEE,
            entity_id=generated_id,
            user_tenant=current_user.tenant,
            should_exist=False,
        )

        employee_dto = EmployeeFirestoreDTO.from_create(
            create_data=employee_data, tenant=current_user.tenant
        )

        # 3. Criar funcionário no Firestore
        logger.info(f"Criando funcionário no Firestore com ID: {generated_id}")
        result = await firestore_client.create_document(
            CollectionType.EMPLOYEE, doc_id=generated_id, data=employee_dto.model_dump()
        )
        logger.info(f"Funcionário criado com sucesso no Firestore: {result}")

        await create_firebase_user(
            entity=EntityType.EMPLOYEE,
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
            data=employee_dto.to_model(generated_id),
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


# C .R. U D
@router.get("/employees", response_model=PaginatedResponse[EmployeeModel])
async def get_employee_list(
    limit: int = Query(
        10, ge=1, le=100, description="Número máximo de itens por página"
    ),
    offset: int = Query(0, ge=0, description="Offset para pafinação"),
    current_user: JWTPayload = Depends(validate_admin_role),
):
    """
    Lista todos os funcionários com paginação.
    """
    try:
        logger.info("🔍 INICIANDO BUSCA DE FUNCIONÁRIOS")
        logger.info(
            f"📋 Parâmetros: limit={limit}, offset={offset}, tenant={current_user.tenant}"
        )

        # 1. Buscar lista de funcionários
        logger.info("🔄 Executando query_documents...")
        items = await firestore_client.query_documents(
            CollectionType.EMPLOYEE.value,
            tenant_id=current_user.tenant,
            limit=limit,
            offset=offset,
        )
        logger.info(f"📊 Query retornou {len(items)} documentos")

        if items:
            logger.info(
                f"📝 Primeiro documento: {items[0].get('id', 'sem_id')} - {items[0].get('name', 'sem_nome')}"
            )
        else:
            logger.warning("⚠️ Nenhum documento retornado pela query!")

        employees = []
        for i, item in enumerate(items):
            try:
                logger.info(
                    f"🔄 Processando funcionário {i+1}/{len(items)}: {item.get('id', 'sem_id')}"
                )
                employee_model = EmployeeFirestoreDTO(**item).to_model(
                    item.get("id", "unknown")
                )
                employees.append(employee_model)
                logger.info(f"✅ Funcionário {i+1} processado com sucesso")
            except ValidationError as e:
                employee_id = item.get("id", "unknown")
                logger.error(
                    f"❌ Pydantic Validation Error for employee ID {employee_id}: {e}, Data: {item}"
                )
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail={
                        "error": {
                            "code": "VALIDATION_ERROR",
                            "msg": f"Validation error for employee ID {employee_id}: {e}",
                        }
                    },
                ) from e

        logger.info(f"📊 Total de funcionários processados: {len(employees)}")

        # 2. Obter a contagem total de funcionários
        logger.info("🔄 Obtendo contagem total...")
        total = await firestore_client.get_collection_count(
            CollectionType.EMPLOYEE.value, tenant_id=current_user.tenant
        )
        logger.info(f"📊 Contagem total: {total}")

        # 3. Criar resposta paginada
        pages = (total + limit - 1) // limit if limit > 0 else 0
        page = (offset // limit) + 1

        logger.info(
            f"📄 Criando resposta paginada: items={len(employees)}, total={total}, page={page}, per_page={limit}, pages={pages}"
        )

        response = PaginatedResponse[EmployeeModel](
            items=employees,
            total=total,
            page=page,
            per_page=limit,
            pages=pages,
        )

        logger.info(f"✅ RESPOSTA FINAL: {len(response.items)} funcionários retornados")
        return response

    except Exception as e:
        logger.error(f"❌ Error listing employees: {str(e)}")
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

        employee = EmployeeFirestoreDTO(**employee_data).to_model(id)
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


# C R .U. D
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
        employee = EmployeeFirestoreDTO(**updated_employee_data).to_model(id)

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


# C R U .D.
@router.delete("/employees/{id}", response_model=BaseResponse)
async def delete_employee(
    id: str = Path(..., description="ID do funcionário"),
    current_user: JWTPayload = Depends(validate_admin_role),
):
    """
    Remove um funcionário existente.
    """
    try:
        # 1. Verifica a existência do funcionário
        await verify_existence(CollectionType.EMPLOYEE, id, current_user.tenant)

        # 2. Exclui o usuário associado no Firebase Authentication e na coleção 'users' do Firestore
        await delete_firebase_user(CollectionType.EMPLOYEE, id, current_user.tenant)

        # 3. Exclui o documento associado da coleção 'employees'
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
