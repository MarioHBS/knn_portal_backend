"""
Implementação dos endpoints para o perfil de administrador (admin).
"""

import uuid
from copy import deepcopy
from datetime import UTC, datetime

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query, status
from firebase_admin import auth
from firebase_admin.auth import UserNotFoundError
from pydantic import ValidationError

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
    EmployeeContactDTO,
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
from src.models.student import (
    StudentCreationDTO,
    StudentDTO,
    StudentGuardian,
    StudentModel,
    StudentUpdateDTO,
)
from src.utils.auth_service import AuthService, generate_temporary_password
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
        existing_partner = await firestore_client.get_document(
            "partners", id, tenant_id=current_user.tenant
        )
        if not existing_partner:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": {"code": "NOT_FOUND", "msg": "Parceiro não encontrado"}
                },
            )

        # Converte o DTO em um dicionário, excluindo valores não definidos
        update_data = data.model_dump(exclude_unset=True)

        if not update_data:
            raise HTTPException(
                status_code=400, detail="Nenhum dado fornecido para atualização"
            )

        # Atualizar metadados
        update_data["updated_at"] = datetime.now(UTC).isoformat()

        # Atualizar parceiro
        result = await firestore_client.update_document(
            "partners", id, update_data, tenant_id=current_user.tenant
        )
        return EntityResponse(data=result, msg="Parceiro atualizado com sucesso")

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
    partner_id = None  # Inicializa o ID do parceiro como None
    try:
        # Adicionar metadados
        current_time = datetime.now(UTC).isoformat()
        # Converter para PartnerDTO para manipulação segura
        partner_data = PartnerDTO.to_firestore(data, current_time, current_time)

        # Geração de ID usando gerador padronizado
        try:
            partner_id = IDGenerators.gerar_id_parceiro(
                trade_name=partner_data.trade_name,
                category=str(partner_data.category),
                cnpj=partner_data.cnpj,
            )
        except Exception:
            partner_id = str(uuid.uuid4())

        # Garantir logo_url padrão se não fornecido
        if not partner_data.logo_url:
            partner_data.logo_url = "/data/placeholder.png"

        # Criar parceiro no Firestore
        result = await firestore_client.create_document(
            "partners", partner_data.model_dump(), partner_id
        )

        # Criar usuário no Firebase Auth
        try:
            temp_password = generate_temporary_password()
            await AuthService.create_user(
                email=partner_data.email,
                password=temp_password,
                display_name=partner_data.trade_name,
            )
            # Enviar e-mail com a senha temporária
            EmailService.send_email(
                recipient_email=partner_data.email,
                subject="Bem-vindo ao Portal KNN!",
                body=f"Sua senha temporária é: {temp_password}",
            )
        except Exception as auth_error:
            # Rollback: Excluir o parceiro do Firestore se a criação do usuário falhar
            if partner_id:
                await firestore_client.delete_document("partners", partner_id)
            logger.error(f"Erro ao criar usuário de parceiro no Firebase: {auth_error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": {
                        "code": "USER_CREATION_FAILED",
                        "msg": "Erro ao criar o usuário do parceiro.",
                    }
                },
            ) from auth_error

        # Atualiza contadores agregados na coleção 'metadata'
        await metrics_service.update_metadata_on_crud(
            "partners", current_user.tenant, operation="add", delta=1
        )
        return EntityResponse(data=result, msg="Parceiro criado com sucesso")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao criar parceiro: {str(e)}")
        # Rollback em caso de outros erros
        if partner_id:
            await firestore_client.delete_document("partners", partner_id)
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
        # Verificar se o parceiro existe e pertence ao tenant
        existing_partner = await firestore_client.get_document(
            "partners", id, tenant_id=current_user.tenant
        )
        if not existing_partner:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": {"code": "NOT_FOUND", "msg": "Parceiro não encontrado"}
                },
            )

        # Excluir usuário do Firebase Authentication
        try:
            partner_email = existing_partner.get("contact", {}).get("email")
            if partner_email:
                await AuthService.delete_user(email=partner_email)
        except UserNotFoundError:
            logger.warning(
                f"Usuário com e-mail {partner_email} não encontrado no Firebase Auth."
            )
        except Exception as auth_error:
            logger.error(
                f"Erro ao excluir usuário do Firebase Auth para o parceiro {id}: {auth_error}"
            )
            # Decide-se por prosseguir com a exclusão no Firestore mesmo que a exclusão no Auth falhe

        # Excluir parceiro
        await firestore_client.delete_document("partners", id)
        # Atualiza contadores agregados na coleção 'metadata'
        await metrics_service.update_metadata_on_crud(
            "partners", current_user.tenant, operation="delete", delta=-1
        )
        return EntityResponse(data={"id": id}, msg="Parceiro excluído com sucesso")

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
# CRUD STUDENT


@router.get("/students", response_model=PaginatedResponse[StudentModel])
async def get_student_list(
    limit: int = Query(10, ge=1, le=100, description="Limit per page"),
    offset: int = Query(0, ge=0, description="Offset to start from"),
    current_user: JWTPayload = Depends(validate_admin_role),
):
    """
    Lists all students with pagination.
    """
    try:
        # Buscar lista de estudantes
        students = await firestore_client.query_documents(
            "students",
            tenant_id=current_user.tenant,
            limit=limit,
            offset=offset,
        )

        # Buscar total de documentos na coleção
        total = await firestore_client.get_collection_count(
            "students", tenant_id=current_user.tenant
        )

        items = []
        for item in students:
            try:
                items.append(StudentDTO(**item).to_student())
            except ValidationError as e:
                student_id = item.get("id", "unknown")
                logger.error(
                    f"Pydantic Validation Error for student ID {student_id}: {e}, Data: {item}"
                )
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail={
                        "error": {
                            "code": "VALIDATION_ERROR",
                            "msg": f"Validation error for student ID {student_id}: {e}",
                        }
                    },
                ) from e

        return PaginatedResponse[StudentModel](
            items=items,
            total=total,
            page=(offset // limit) + 1,
            per_page=limit,
            pages=(total + limit - 1) // limit,
        )

    except Exception as e:
        logger.error(f"Error listing students: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {"code": "SERVER_ERROR", "msg": "Error listing students"}},
        ) from e


@router.get("/students/{id}", response_model=EntityResponse[StudentModel])
async def get_student_individual(
    id: str,
    current_user: JWTPayload = Depends(validate_admin_role),
):
    """
    Busca um estudante pelo ID.
    """
    try:
        student_data = await firestore_client.get_document(
            "students", id, tenant_id=current_user.tenant
        )
        if not student_data or student_data.get("tenant_id") != current_user.tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": {"code": "NOT_FOUND", "msg": "Estudante não encontrado"}
                },
            )

        student = StudentDTO(**student_data).to_student()
        return EntityResponse[StudentModel](
            data=student, msg="Estudante encontrado com sucesso"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao buscar estudante: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {"code": "SERVER_ERROR", "msg": "Erro ao buscar estudante"}
            },
        ) from e


@router.put("/students/{id}", response_model=EntityResponse[StudentModel])
async def set_student_individual(
    id: str,
    data: StudentUpdateDTO,
    current_user: JWTPayload = Depends(validate_admin_role),
):
    """
    Atualiza um estudante existente.
    """
    try:
        # Verificar se o estudante existe
        existing_student = await firestore_client.get_document(
            "students", id, tenant_id=current_user.tenant
        )
        if (
            not existing_student
            or existing_student.get("tenant_id") != current_user.tenant
        ):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": {"code": "NOT_FOUND", "msg": "Estudante não encontrado"}
                },
            )

        # Mapeamento de campos do DTO para o documento do Firestore
        field_mapping = {
            "name": "name",
            "student_occupation": "occupation",
            "book": "book",
            "active_until": "active_until",
            "email": "contact.email",
            "student_phone": "contact.phone",
            "zip": "address.zip",
            "add_complement": "address.complement",
            "add_neighbor": "address.neighborhood",
            "guardian_name": "guardian.name",
            "guardian_email": "guardian.email",
            "guardian_phone": "guardian.phone",
        }

        update_data = {}
        update_payload = data.model_dump(exclude_unset=True)

        for field, value in update_payload.items():
            if field in field_mapping:
                target_path = field_mapping[field]
                if "." in target_path:
                    parts = target_path.split(".")
                    current_level_update = update_data
                    current_level_existing = existing_student

                    for _, part in enumerate(parts[:-1]):
                        # Garante que o sub-dicionário exista no payload de atualização
                        if part not in current_level_update:
                            # Se já existir no documento original, usa-o para não sobrescrever outros campos
                            current_level_update[part] = current_level_existing.get(
                                part, {}
                            )

                        current_level_update = current_level_update[part]
                        if current_level_existing:
                            current_level_existing = current_level_existing.get(part)

                    current_level_update[parts[-1]] = value
                else:
                    update_data[target_path] = value

        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": {
                        "code": "NO_DATA_TO_UPDATE",
                        "msg": "Nenhum dado fornecido para atualização",
                    }
                },
            )

        update_data["updated_at"] = datetime.now(UTC)

        await firestore_client.update_document(
            "students", id, update_data, tenant_id=current_user.tenant
        )

        # Obter dados atualizados
        updated_student_data = await firestore_client.get_document(
            "students", id, tenant_id=current_user.tenant
        )
        student = StudentDTO(**updated_student_data).to_student()

        return EntityResponse[StudentModel](
            data=student, msg="Estudante atualizado com sucesso"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao atualizar estudante: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {"code": "SERVER_ERROR", "msg": "Erro ao atualizar estudante"}
            },
        ) from e


@router.post("/students", response_model=EntityResponse[StudentModel])
async def create_student(
    student_data: StudentCreationDTO,
    current_user: JWTPayload = Depends(validate_admin_role),
):
    """
    Cria um novo estudante.
    """
    try:
        # O Pydantic já validou os dados de entrada ao converter para StudentCreationDTO
        # Agora, convertemos o DTO de criação para o modelo de domínio Student
        guardian = None
        if student_data.guardian_name and student_data.guardian_email:
            guardian = StudentGuardian(
                name=student_data.guardian_name,
                email=student_data.guardian_email,
                phone=student_data.guardian_phone or "",
            )

        the_student = StudentModel(
            tenant_id=current_user.tenant,
            student_name=student_data.name,
            book=student_data.book,
            student_occupation=student_data.student_occupation,
            student_email=student_data.email,
            student_phone=student_data.student_phone,
            zip=student_data.zip,
            add_neighbor=student_data.add_neighbor,
            add_complement=student_data.add_complement,
            guardian=guardian,
            active_until=student_data.active_until,
        )

        # O ID do estudante é gerado no construtor de Student
        # Agora, convertemos o modelo de domínio para o DTO do Firestore
        dto = StudentDTO.from_student(the_student)

        # Adicionar metadados de tempo
        current_time = datetime.now(UTC)
        dto.created_at = current_time
        dto.updated_at = current_time

        # Criar usuário no Firebase Authentication
        auth_service = AuthService()
        temp_password = generate_temporary_password()
        try:
            auth_service.create_user(email=student_data.email, password=temp_password)
            # Enviar e-mail com a senha temporária
            email_service = EmailService()
            email_service.send_email(
                to_email=student_data.email,
                subject="Bem-vindo ao Journey Club!",
                body=f"Sua senha temporária é: {temp_password}",
            )
        except Exception as e:
            logger.error(f"Erro ao criar usuário no Firebase Auth: {str(e)}")
            # Decidir se a falha na criação do usuário no Auth deve impedir a criação do estudante no Firestore

        # Criar estudante no Firestore
        result = await firestore_client.create_document(
            "students", dto.model_dump(exclude_none=True), the_student.id
        )

        # Atualiza contadores agregados na coleção 'metadata'
        await metrics_service.update_metadata_on_crud(
            "students", current_user.tenant, operation="add", delta=1
        )
        return {"data": the_student, "msg": "Estudante criado com sucesso"}

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error": {"code": "VALIDATION_ERROR", "msg": str(e)}},
        ) from e
    except Exception as e:
        logger.error(f"Erro ao criar estudante: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {"code": "SERVER_ERROR", "msg": "Erro ao criar estudante"}
            },
        ) from e


@router.delete("/students/{id}", response_model=BaseResponse)
async def delete_student(
    id: str,
    current_user: JWTPayload = Depends(validate_admin_role),
):
    """
    Exclui um estudante existente.
    """
    auth_service = AuthService()
    try:
        # Verificar se o estudante existe
        existing_student = await firestore_client.get_document(
            "students", id, tenant_id=current_user.tenant
        )
        if (
            not existing_student
            or existing_student.get("tenant_id") != current_user.tenant
        ):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": {"code": "NOT_FOUND", "msg": "Estudante não encontrado"}
                },
            )

        # Excluir usuário do Firebase Authentication
        try:
            user = auth.get_user_by_email(existing_student["contact"]["email"])
            auth_service.delete_user(user.uid)
        except auth.UserNotFoundError:
            logger.warning(
                f"Usuário com e-mail {existing_student['contact']['email']} não encontrado no Firebase Authentication."
            )
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

        # Excluir estudante do Firestore
        await firestore_client.delete_document("students", id)

        # Atualiza contadores agregados na coleção 'metadata'
        await metrics_service.update_metadata_on_crud(
            "students", current_user.tenant, operation="delete", delta=-1
        )

        return EntityResponse(data={"id": id}, msg="Estudante excluído com sucesso")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao excluir estudante: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {"code": "SERVER_ERROR", "msg": "Erro ao excluir estudante"}
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
    data: EmployeeCreateDTO = Body(..., description="Dados do funcionário"),
    current_user: JWTPayload = Depends(validate_admin_role),
):
    """
    Cria um novo funcionário.
    """
    logger.info(
        f"Recebida requisição para criar funcionário com dados: {data.model_dump()}"
    )
    try:
        # Gerar ID padronizado utilizando gerador específico
        generated_id = IDGenerators.gerar_id_funcionario(
            data.name, data.role, data.zip, data.phone
        )
        logger.info(f"ID de funcionário gerado: {generated_id}")

        # Criar instância do modelo Pydantic para validação e conversão
        logger.info(
            f"Criando EmployeeContactDTO com email: {data.email} e phone: {data.phone}"
        )
        contact = EmployeeContactDTO(email=data.email, phone=data.phone)
        logger.info("EmployeeContactDTO criado com sucesso.")

        logger.info("Criando EmployeeModel...")
        the_employee = EmployeeFirestoreDTO(
            tenant_id=data.tenant_id,
            name=data.name,
            contact=contact,
            zip=data.zip,
            role=data.role,
            active=data.active,
        )
        logger.info(
            f"EmployeeFirestoreDTO instanciado com sucesso: {the_employee.model_dump()}"
        )

        # Criar funcionário no Firestore
        logger.info(f"Criando funcionário no Firestore com ID: {generated_id}")
        result = await firestore_client.create_document(
            "employees", doc_id=generated_id, data=the_employee.model_dump()
        )
        logger.info(f"Funcionário criado com sucesso no Firestore: {result}")

        await create_firebase_user(
            entity=CollectionType.EMPLOYEE,
            entity_name=the_employee.name,
            entity_email=the_employee.contact.email,
            entity_id=the_employee.id,
            tenant_id=the_employee.tenant_id,
        )

        # Atualiza contadores agregados na coleção 'metadata'
        await metrics_service.update_metadata_on_crud(
            "employees", current_user.tenant, operation="add", delta=1
        )
        return {"data": the_employee, "msg": "Funcionário criado com sucesso"}

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error": {"code": "VALIDATION_ERROR", "msg": str(e)}},
        ) from e
    except Exception as e:
        logger.error(f"Erro ao criar funcionário: {str(e)}")
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
    auth_service = AuthService()
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

        # Excluir usuário do Firebase Authentication
        try:
            user = auth.get_user_by_email(existing_employee["contact"]["email"])
            auth_service.delete_user(user.uid)
        except auth.UserNotFoundError:
            # O usuário não existe no Firebase, pode prosseguir com a exclusão no Firestore
            logger.warning(
                f"Usuário com e-mail {existing_employee['contact']['email']} não encontrado no Firebase Authentication."
            )
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

        # Remover funcionário do Firestore
        await firestore_client.delete_document("employees", id)

        # Atualiza contadores agregados na coleção 'metadata'
        await metrics_service.update_metadata_on_crud(
            "employees", current_user.tenant, operation="sub", delta=1
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
    existing = await firestore_client.get_document(collection, entity_id)
    if not existing or existing.get("tenant_id") != user_tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "NOT_FOUND",
                    "msg": f"{mapping.get(collection, 'Entidade')} não encontrado",
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

        # Criar documento na coleção 'users' do Firestore usando UserModel
        user_data = UserModel(
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
            await auth_service.delete_user(user_record.uid)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "FIREBASE_ERROR",
                    "msg": "Erro ao criar usuário de autenticação",
                }
            },
        ) from e
