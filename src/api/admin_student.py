from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from pydantic import ValidationError

from src.api.admin import (
    create_firebase_user,
    delete_firebase_user,
    update_entity,
    verify_existence,
)
from src.auth import JWTPayload, validate_admin_role
from src.db.firestore import firestore_client
from src.models import BaseResponse, CollectionType, EntityResponse, EntityType
from src.models.pagination import PaginatedResponse
from src.models.student import (
    StudentCreateDTO,
    StudentFirestoreDTO,
    StudentModel,
    StudentUpdateDTO,
)
from src.utils.id_generators import IDGenerators
from src.utils.logging import logger
from src.utils.metrics_service import CrudOperation, MetricsService

metrics_service_instance = MetricsService()

router = APIRouter(
    tags=["Admin - Students"], dependencies=[Depends(validate_admin_role)]
)


# .C. R U D
@router.post(
    "/students",
    response_model=EntityResponse[StudentModel],
    status_code=status.HTTP_201_CREATED,
)
async def create_student(
    student_data: StudentCreateDTO,
    current_user: JWTPayload = Depends(validate_admin_role),
):
    """
    Cria um novo Aluno.
    """
    try:
        # 1. Gerar ID do aluno
        student_id = IDGenerators.generate_student_id(
            nome=student_data.name,
            curso=student_data.book,  # Assumindo que 'book' é o curso
            cep=student_data.zip or "",
            celular=student_data.student_phone or "",
            email=student_data.email,
        )
        logger.debug(f"ID do aluno gerado: {student_id}")

        # 2. Verificar se o estudante já existe (pelo ID gerado ou e-mail)
        verify_existence(
            collection=CollectionType.STUDENT,
            entity_id=student_id,
            user_tenant=current_user.tenant,
        )

        student_dto = StudentFirestoreDTO.from_create(
            create_data=student_data, tenant=current_user.tenant
        )

        # 3. Cria Aluno na coleção 'students'
        logger.info(f"Criando Aluno no Firestore com ID: {student_id}")
        await firestore_client.create_document(
            collection=CollectionType.STUDENT,
            doc_id=student_id,
            data=student_dto.model_dump(),
        )
        logger.info(f"Aluno criado com sucesso no Firestore: {student_id}")

        # 4. Criar usuário no Firebase Authentication e na coleção 'users' do Firestore
        await create_firebase_user(
            entity=EntityType.STUDENT,
            entity_name=student_dto.name,
            entity_email=student_dto.contact.email,
            entity_id=student_id,
            tenant_id=student_dto.tenant_id,
        )
        # logger.info(f"Usuário Firebase criado para {student_id}")

        # 5. Atualizar contadores agregados na coleção 'metadata'
        await metrics_service_instance.update_metadata_on_crud(
            CollectionType.STUDENT,
            student_dto.tenant_id,
            operation=CrudOperation.ADD,
        )

        # 5. Retornar resposta
        return EntityResponse[StudentModel](
            data=student_dto.to_model(student_id), msg="Estudante criado com sucesso"
        )

    except ValueError as e:
        logger.error(f"Erro de validação ao criar aluno: {str(e)}")
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
        logger.error(f"Erro inesperado ao criar aluno: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "SERVER_ERROR",
                    "msg": "Erro interno do servidor ao criar aluno",
                }
            },
        ) from e


# C .R. U D
@router.get("/students", response_model=PaginatedResponse[StudentModel])
async def get_student_list(
    limit: int = Query(10, ge=1, le=100, description="Limit per page"),
    offset: int = Query(0, ge=0, description="Offset to start from"),
    current_user: JWTPayload = Depends(validate_admin_role),
):
    """
    Lista todos os estudantes com paginação.
    """
    try:
        logger.info("🔍 INICIANDO BUSCA DE ESTUDANTES")
        logger.info(
            f"📋 Parâmetros: limit={limit}, offset={offset}, tenant={current_user.tenant}"
        )

        # 1. Buscar lista de estudantes
        logger.info("🔄 Executando query_documents...")
        items = await firestore_client.query_documents(
            CollectionType.STUDENT.value,
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

        students = []
        for i, item in enumerate(items):
            try:
                logger.info(
                    f"🔄 Processando estudante {i+1}/{len(items)}: {item.get('id', 'sem_id')}"
                )
                student_model = StudentFirestoreDTO(**item).to_model(
                    item.get("id", "unknown")
                )
                students.append(student_model)
                logger.info(f"✅ Estudante {i+1} processado com sucesso")
            except ValidationError as e:
                student_id = item.get("id", "unknown")
                logger.error(
                    f"❌ Pydantic Validation Error for student ID {student_id}: {e}, Data: {item}"
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

        logger.info(f"📊 Total de estudantes processados: {len(students)}")

        # 2. Obter a contagem total de estudantes
        logger.info("🔄 Obtendo contagem total...")
        total = await firestore_client.get_collection_count(
            CollectionType.STUDENT.value, tenant_id=current_user.tenant
        )
        logger.info(f"📊 Contagem total: {total}")

        # 3. Criar resposta paginada
        pages = (total + limit - 1) // limit if limit > 0 else 0
        page = (offset // limit) + 1

        logger.info(
            f"📄 Criando resposta paginada: items={len(students)}, total={total}, page={page}, per_page={limit}, pages={pages}"
        )

        response = PaginatedResponse[StudentModel](
            items=students,
            total=total,
            page=page,
            per_page=limit,
            pages=pages,
        )

        logger.info(f"✅ RESPOSTA FINAL: {len(response.items)} estudantes retornados")
        return response

    except Exception as e:
        logger.error(f"❌ Error listing students: {str(e)}")
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
            CollectionType.STUDENT.value, id, tenant_id=current_user.tenant
        )
        if not student_data or student_data.get("tenant_id") != current_user.tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": {"code": "NOT_FOUND", "msg": "Estudante não encontrado"}
                },
            )

        student = StudentFirestoreDTO(**student_data).to_model()
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


# C R .U. D
@router.put("/students/{id}", response_model=EntityResponse[StudentModel])
async def set_student_individual(
    id: str,
    data: StudentUpdateDTO = Body(
        ..., description="Dados para atualização do estudante"
    ),
    current_user: JWTPayload = Depends(validate_admin_role),
):
    """
    Atualiza todos os campos de um estudante existente.

    - **id**: Identificador único do estudante a ser atualizado.
    - **data**: Payload contendo os novos valores dos campos a serem substituídos.
    """
    try:
        # Verificar se o estudante existe
        verify_existence(
            CollectionType.STUDENT.value,
            id,
            current_user.tenant,
            "Estudante não encontrado",
        )

        return update_entity(
            entity_id=id,
            model=data,
            collection=CollectionType.STUDENT,
            tenant=current_user.tenant,
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


# C R U .D.
@router.delete(
    "/students/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_student(
    id: str,
    current_user: JWTPayload = Depends(validate_admin_role),
):
    """
    Exclui um estudante pelo ID.
    """
    try:
        # 1. Verificar a existência do estudante
        await verify_existence(CollectionType.STUDENT, id, current_user.tenant)

        # 2. Excluir usuário do Firebase Authentication e da coleção 'users' do Firestore
        await delete_firebase_user(EntityType.STUDENT, id, current_user.tenant)

        # 3. Excluir o documento do estudante da coleção 'students' do Firestore
        await firestore_client.delete_document(CollectionType.STUDENT.value, id)

        # 4. Atualizar contadores agregados na coleção 'metadata'
        await metrics_service_instance.update_metadata_on_crud(
            CollectionType.STUDENT,
            current_user.tenant,
            operation=CrudOperation.SUB,
        )

        return BaseResponse(msg="Estudante excluído com sucesso")

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


# =================================================================
# AUXILIARES


@router.post("/students/{student_id}/activate", response_model=StudentModel)
async def activate_student(student_id: str):
    """
    Ativa um estudante.
    """
    student_dto = await firestore_client.get_document(
        "students", student_id, dto_type=StudentFirestoreDTO
    )
    if not student_dto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Estudante não encontrado"
        )

    if student_dto.is_active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Estudante já está ativo"
        )

    await firestore_client.update_document(
        "students",
        student_id,
        {"is_active": True, "updated_at": firestore_client.get_server_timestamp()},
    )
    updated_student_dto = student_dto.model_copy(update={"is_active": True})
    return StudentModel.from_firestore_dto(updated_student_dto)


@router.post("/students/{student_id}/deactivate", response_model=StudentModel)
async def deactivate_student(student_id: str):
    """
    Desativa um estudante.
    """
    student_dto = await firestore_client.get_document(
        "students", student_id, dto_type=StudentFirestoreDTO
    )
    if not student_dto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Estudante não encontrado"
        )

    if not student_dto.is_active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Estudante já está inativo"
        )

    await firestore_client.update_document(
        "students",
        student_id,
        {"is_active": False, "updated_at": firestore_client.get_server_timestamp()},
    )
    updated_student_dto = student_dto.model_copy(update={"is_active": False})
    return StudentModel.from_firestore_dto(updated_student_dto)
