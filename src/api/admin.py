"""
Implementação dos endpoints para o perfil de administrador (admin).
"""

import uuid
from copy import deepcopy
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query, status

from src.auth import JWTPayload, validate_admin_role
from src.db import firestore_client, postgres_client, with_circuit_breaker
from src.db.firestore import db
from src.models import (
    BaseResponse,
    EntityListResponse,
    EntityResponse,
    MetricsResponse,
    NotificationRequest,
    PartnerDetail,
    PartnerDetailResponse,
    PartnerListResponse,
)
from src.models.benefit import (
    Benefit,
    BenefitConfigurationDTO,
    BenefitCreationDTO,
    BenefitFirestoreDTO,
)
from src.models.student import (
    Student,
    StudentCreationDTO,
    StudentDTO,
    StudentGuardian,
)
from src.utils import logger
from src.utils.id_generators import IDGenerators
from src.utils.metrics_service import metrics_service
from src.utils.partners_service import PartnersService

# Criar router
router = APIRouter(tags=["admin"])


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
        return await PartnersService.list_partners_common(
            current_user=current_user,
            cat=cat,
            ord=ord,
            limit=limit,
            offset=offset,
            use_circuit_breaker=False,  # Desabilitado para usar apenas Firestore
            enable_ordering=True,  # Habilitado após criação do índice composto
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


@router.get("/partners/{id}", response_model=PartnerDetailResponse)
async def get_partner_details(
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


@router.get("/students", response_model=EntityListResponse)
async def list_students(
    current_user: JWTPayload = Depends(validate_admin_role),
):
    """
    Lista todos os estudantes.
    """
    try:
        students = await firestore_client.query_documents(
            "students", tenant_id=current_user.tenant, limit=1000
        )
        return {"data": students, "msg": "Estudantes listados com sucesso"}

    except Exception as e:
        logger.error(f"Erro ao listar estudantes: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {"code": "SERVER_ERROR", "msg": "Erro ao listar estudantes"}
            },
        ) from e


@router.post("/students", response_model=EntityResponse)
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

        the_student = Student(
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

        # Criar estudante no Firestore
        result = await firestore_client.create_document(
            "students", dto.model_dump(exclude_none=True), the_student.id
        )

        # Atualiza contadores agregados na coleção 'metadata'
        await metrics_service.update_metadata_on_crud(
            "students", current_user.tenant, operation="add", delta=1
        )
        return {"data": result, "msg": "Estudante criado com sucesso"}

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


@router.get("/employees", response_model=EntityListResponse)
async def list_employees(
    current_user: JWTPayload = Depends(validate_admin_role),
):
    """
    Lista todos os funcionários.
    """
    try:
        employees = await firestore_client.query_documents(
            "employees", tenant_id=current_user.tenant, limit=1000
        )
        return {"data": employees, "msg": "Funcionários listados com sucesso"}

    except Exception as e:
        logger.error(f"Erro ao listar funcionários: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {"code": "SERVER_ERROR", "msg": "Erro ao listar funcionários"}
            },
        ) from e


@router.post("/employees", response_model=EntityResponse)
async def create_employee(
    data: dict[str, Any] = Body(..., description="Dados do funcionário"),
    current_user: JWTPayload = Depends(validate_admin_role),
):
    """
    Cria um novo funcionário.
    """
    try:
        # Validar dados obrigatórios
        required_fields = ["name", "email"]
        for field in required_fields:
            if field not in data:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail={
                        "error": {
                            "code": "VALIDATION_ERROR",
                            "msg": f"Campo obrigatório: {field}",
                        }
                    },
                )

        # Gerar ID padronizado utilizando gerador específico
        cargo = str(data.get("cargo") or data.get("role") or "").strip()
        cep = str(data.get("cep") or data.get("zip") or "").strip()
        telefone = str(data.get("phone") or data.get("telefone") or "").strip()
        generated_id = IDGenerators.gerar_id_funcionario(
            data["name"], cargo, cep, telefone
        )

        # Não armazenar campo 'id' dentro do documento
        # O ID do documento no Firestore será a chave 'generated_id'
        data.pop("id", None)

        # Adicionar metadados
        current_time = datetime.now(UTC).isoformat()
        data.update(
            {
                "tenant_id": current_user.tenant,
                "created_at": current_time,
                "updated_at": current_time,
                "type": "employee",
            }
        )

        # Criar funcionário
        result = await firestore_client.create_document("employees", data, generated_id)
        # Atualiza contadores agregados na coleção 'metadata'
        await metrics_service.update_metadata_on_crud(
            "employees", current_user.tenant, operation="add", delta=1
        )
        return {"data": result, "msg": "Funcionário criado com sucesso"}

    except HTTPException:
        raise
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
    try:
        # Remover funcionário
        success = await firestore_client.delete_document("employees", id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": {
                        "code": "NOT_FOUND",
                        "msg": "Funcionário não encontrado",
                    }
                },
            )

        # Atualiza contadores agregados na coleção 'metadata'
        await metrics_service.update_metadata_on_crud(
            "employees", current_user.tenant, operation="sub", delta=1
        )

        return {"msg": "Funcionário removido com sucesso"}

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


@router.post("/partners", response_model=EntityResponse)
async def create_partner(
    data: dict[str, Any] = Body(..., description="Dados do parceiro"),
    current_user: JWTPayload = Depends(validate_admin_role),
):
    """
    Cria um novo parceiro.
    """
    try:
        # Validar dados obrigatórios
        required_fields = ["name", "category"]
        for field in required_fields:
            if field not in data:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail={
                        "error": {
                            "code": "VALIDATION_ERROR",
                            "msg": f"Campo obrigatório: {field}",
                        }
                    },
                )

        # Gerar ID se não fornecido
        if "id" not in data:
            data["id"] = str(uuid.uuid4())

        # Adicionar metadados
        current_time = datetime.now(UTC).isoformat()
        data.update(
            {
                "tenant_id": current_user.tenant,
                "created_at": current_time,
                "updated_at": current_time,
                "active": data.get("active", True),
            }
        )

        # Garantir logo_url padrão se não fornecido
        if not data.get("logo_url"):
            data["logo_url"] = "/data/placeholder.png"

        # Criar parceiro
        result = await firestore_client.create_document("partners", data, data["id"])
        # Atualiza contadores agregados na coleção 'metadata'
        await metrics_service.update_metadata_on_crud(
            "partners", current_user.tenant, operation="add", delta=1
        )
        return {"data": result, "msg": "Parceiro criado com sucesso"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao criar parceiro: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {"code": "SERVER_ERROR", "msg": "Erro ao criar parceiro"}},
        ) from e


@router.get("/benefits", response_model=EntityListResponse)
async def list_all_benefits(
    partner_id: str | None = Query(None, description="Filtro por ID do parceiro"),
    category: str | None = Query(None, description="Filtro por categoria"),
    benefit_status: str | None = Query(
        None, description="Filtro por status", enum=["active", "inactive", "expired"]
    ),
    limit: int = Query(
        20, ge=1, le=100, description="Número máximo de itens por página"
    ),
    offset: int = Query(0, ge=0, description="Offset para paginação"),
    current_user: JWTPayload = Depends(validate_admin_role),
):
    """
    Lista todos os benefícios do sistema com filtros e paginação.

    Endpoint específico para administradores com as seguintes características:
    - Lista benefícios de todos os parceiros
    - Inclui partner_id na resposta para filtragem na tela
    - Suporte a filtros por parceiro, categoria e status
    - Paginação para performance
    - Circuit breaker para alta disponibilidade
    """
    try:
        # Obter tenant_id do JWT token
        tenant_id = current_user.tenant
        admin_id = current_user.sub
        logger.info(
            f"Admin {admin_id} listando benefícios - Tenant: {tenant_id} - Filtros: partner_id={partner_id}, category={category}, status={benefit_status}"
        )

        # Buscar todos os documentos da coleção benefits usando a mesma abordagem do partner
        async def get_firestore_all_benefits() -> list[Benefit]:
            composed_filters = []
            if partner_id:
                composed_filters.append(("partner_id", "==", partner_id))
            if category:
                composed_filters.append(("category", "==", category))
            if benefit_status:
                composed_filters.append(("status", "==", benefit_status))

            result = await firestore_client.query_documents(
                collection="benefits",
                tenant_id=tenant_id,
                filters=composed_filters,
                limit=limit,
                offset=offset,
                order_by=[("created_at", "DESCENDING")],
            )

            all_benefits = [
                BenefitFirestoreDTO(**doc).to_benefit(doc["id"])
                for doc in result["items"]
            ]
            # for doc in result["items"]:
            #     logger.info(f"Listando benefício - {doc}")
            #     all_benefits.append(BenefitFirestoreDTO(**doc).to_benefit(doc["id"]))

            return all_benefits

        async def get_postgres_all_benefits() -> list[Benefit]:
            # Fallback para PostgreSQL se necessário
            return []

        # Usar circuit breaker para operações do Firestore
        benefits_list = await with_circuit_breaker(
            get_firestore_all_benefits, get_postgres_all_benefits
        )

        # Ordenar por data de criação (mais recente primeiro)
        benefits_list.sort(key=lambda x: x.created_at, reverse=True)

        # Aplicar paginação
        total_count = len(benefits_list)
        paginated_benefits = benefits_list[offset : offset + limit]

        logger.info(
            f"Retornando {len(paginated_benefits)} benefícios de {total_count} total"
        )

        return {
            "data": {
                "items": paginated_benefits,
                "total": total_count,
                "limit": limit,
                "offset": offset,
            },
            "msg": "Benefícios listados com sucesso",
        }

    except Exception as e:
        logger.error(f"Erro ao listar benefícios: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {"code": "SERVER_ERROR", "msg": "Erro ao listar benefícios"}
            },
        ) from e


@router.get("/benefits/{partner_id}/{benefit_id}", response_model=EntityResponse)
async def get_benefit_details(
    partner_id: str = Path(..., description="ID do parceiro"),
    benefit_id: str = Path(..., description="ID do benefício"),
    current_user: JWTPayload = Depends(validate_admin_role),
):
    """
    Obtém detalhes de um benefício específico.

    Endpoint para administradores visualizarem benefícios específicos
    de qualquer parceiro do sistema.
    """
    try:
        logger.info(
            f"Admin {current_user.sub} buscando benefício {benefit_id} do parceiro {partner_id}"
        )

        async def get_benefit_from_firestore():
            logger.info(
                f"🔍 Iniciando busca do benefício {benefit_id} do parceiro {partner_id}"
            )
            logger.info(f"🔍 Tenant do usuário: {current_user.tenant}")

            # 1. Buscar o documento do parceiro na coleção 'benefits'
            logger.info(
                f"🔍 Buscando documento na coleção 'benefits' com ID: {partner_id}"
            )
            partner_doc = await firestore_client.get_document(
                "benefits", partner_id, current_user.tenant
            )

            logger.info(
                f"🔍 Resultado da busca do documento: {partner_doc is not None}"
            )
            if partner_doc:
                logger.info(
                    f"🔍 Chaves do documento encontrado: {list(partner_doc.keys())}"
                )
                # Verificar se o benefit_id existe
                benefit_keys = [k for k in partner_doc if k.startswith("BNF_")]
                logger.info(f"🔍 Benefícios encontrados no documento: {benefit_keys}")
                logger.info(f"🔍 Procurando por benefício: {benefit_id}")

            if not partner_doc:
                logger.warning(f"❌ Documento do parceiro {partner_id} não encontrado")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "error": {
                            "code": "PARTNER_NOT_FOUND",
                            "msg": "Parceiro não encontrado",
                        }
                    },
                )

            # 2. Acessar o benefício diretamente no documento (não há campo 'data')
            logger.info(f"🔍 Buscando benefício {benefit_id} no documento")
            benefit_data = partner_doc.get(benefit_id)

            logger.info(f"🔍 Benefício encontrado: {benefit_data is not None}")

            if not benefit_data:
                logger.warning(
                    f"❌ Benefício {benefit_id} não encontrado no documento do parceiro {partner_id}"
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

            # Adicionar informações do parceiro e benefício
            benefit_with_ids = {
                **benefit_data,
                "benefit_id": benefit_id,
                "partner_id": partner_id,
            }

            logger.info(
                f"✅ Benefício {benefit_id} encontrado e processado com sucesso"
            )
            return benefit_with_ids

        benefit = await get_benefit_from_firestore()

        logger.info(f"Benefício {benefit_id} encontrado para parceiro {partner_id}")

        return {"data": benefit, "msg": "Benefício encontrado com sucesso"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Erro ao buscar benefício {benefit_id} do parceiro {partner_id}: {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {"code": "SERVER_ERROR", "msg": "Erro ao buscar benefício"}
            },
        ) from e


@router.put("/benefits/{partner_id}/{benefit_id}", response_model=EntityResponse)
async def update_benefit(
    partner_id: str = Path(..., description="ID do parceiro"),
    benefit_id: str = Path(..., description="ID do benefício"),
    benefit_data: BenefitCreationDTO = None,
    current_user: JWTPayload = Depends(validate_admin_role),
):
    """
    Atualiza um benefício específico de um parceiro.

    Endpoint para administradores atualizarem benefícios de qualquer parceiro,
    seguindo a nova estrutura com partner_id e benefit_id na URL.
    """
    try:
        logger.info(
            f"Admin {current_user.sub} atualizando benefício {benefit_id} do parceiro {partner_id}"
        )

        # Validar campos obrigatórios do benefício
        if not benefit_data.title:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "msg": "Campo obrigatório: title",
                    }
                },
            )

        current_time = datetime.now(UTC).isoformat()

        # Função para atualizar no Firestore
        async def update_benefit_firestore():
            # Buscar documento de benefícios do parceiro (seguindo a mesma lógica do partner.py)
            doc_ref = db.collection("benefits").document(partner_id)
            doc = doc_ref.get()

            if not doc.exists:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "error": {
                            "code": "PARTNER_NOT_FOUND",
                            "msg": f"Documento de benefícios não encontrado para parceiro {partner_id}",
                        }
                    },
                )

            # Verificar se o benefício específico existe no documento do parceiro
            benefits_data = doc.to_dict()
            if benefit_id not in benefits_data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "error": {
                            "code": "BENEFIT_NOT_FOUND",
                            "msg": f"Benefício {benefit_id} não encontrado no parceiro {partner_id}",
                        }
                    },
                )

            # Obter o benefício existente e atualizar mantendo a estrutura original
            existing_benefit = benefits_data[benefit_id].copy()

            # Atualizar campos principais
            existing_benefit["title"] = benefit_data.title
            if hasattr(benefit_data, "description") and benefit_data.description:
                existing_benefit["description"] = benefit_data.description

            # Atualizar campos do system
            if "system" not in existing_benefit:
                existing_benefit["system"] = {}
            existing_benefit["system"]["type"] = benefit_data.type
            existing_benefit["system"]["status"] = getattr(
                benefit_data, "status", "active"
            )

            # Converter audience se necessário
            if hasattr(benefit_data, "audience"):
                if isinstance(benefit_data.audience, list):
                    audience_mapping = {
                        frozenset(["student"]): "students",
                        frozenset(["employee"]): "employees",
                        frozenset(["student", "employee"]): "all",
                    }
                    firestore_audience = audience_mapping.get(
                        frozenset(benefit_data.audience), "students"
                    )
                    existing_benefit["system"]["audience"] = firestore_audience
                else:
                    existing_benefit["system"]["audience"] = benefit_data.audience

            # Atualizar campos de datas
            if "dates" not in existing_benefit:
                existing_benefit["dates"] = {}
            existing_benefit["dates"]["updated_at"] = current_time

            if hasattr(benefit_data, "valid_from") and benefit_data.valid_from:
                existing_benefit["dates"][
                    "valid_from"
                ] = benefit_data.valid_from.isoformat()
            if hasattr(benefit_data, "valid_to") and benefit_data.valid_to:
                existing_benefit["dates"][
                    "valid_until"
                ] = benefit_data.valid_to.isoformat()

            # Atualizar configuração se fornecida
            if "configuration" not in existing_benefit:
                existing_benefit["configuration"] = {}

            if hasattr(benefit_data, "value"):
                existing_benefit["configuration"]["value"] = benefit_data.value
            if hasattr(benefit_data, "value_type"):
                existing_benefit["configuration"][
                    "value_type"
                ] = benefit_data.value_type

            # Atualizar o documento com o benefício modificado
            update_data = {benefit_id: existing_benefit}
            doc_ref.update(update_data)

            logger.info(f"Benefício {benefit_id} atualizado no Firestore com sucesso")
            return {
                "success": True,
                "benefit_id": benefit_id,
                "updated_benefit": existing_benefit,
            }

        # Função de fallback para PostgreSQL (placeholder)
        async def update_benefit_postgres():
            # TODO: Implementar fallback para PostgreSQL quando necessário
            logger.warning(
                "Fallback para PostgreSQL não implementado para update_benefit"
            )
            return {"success": True}

        # Usar circuit breaker corretamente
        result = await with_circuit_breaker(
            update_benefit_firestore, update_benefit_postgres
        )

        # Verificar se a atualização foi bem-sucedida
        if not result or not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": {
                        "code": "UPDATE_FAILED",
                        "msg": "Falha ao atualizar benefício",
                    }
                },
            )

        logger.info(
            f"Benefício {benefit_id} atualizado com sucesso para parceiro {partner_id}"
        )

        return {
            "data": {
                "benefit_id": benefit_id,
                "partner_id": partner_id,
                "updated_benefit": result.get("updated_benefit", {}),
            },
            "msg": "Benefício atualizado com sucesso",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Erro ao atualizar benefício {benefit_id} do parceiro {partner_id}: {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {"code": "SERVER_ERROR", "msg": "Erro ao atualizar benefício"}
            },
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
    Remove um benefício específico de um parceiro.

    Endpoint para administradores removerem benefícios de qualquer parceiro.
    Por padrão, realiza hard delete (remoção completa). Use soft_delete=true para manter o benefício marcado como inativo.
    """
    try:
        logger.info(
            f"Admin {current_user.sub} removendo benefício {benefit_id} do parceiro {partner_id} (soft_delete={soft_delete})"
        )

        # Usar circuit breaker para operações do Firestore
        async def delete_benefit_firestore():
            # Acesso direto ao documento sem prefixo de tenant
            from src.db.firestore import db

            doc_ref = db.collection("benefits").document(benefit_id)
            doc = doc_ref.get()

            if not doc.exists:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "error": {
                            "code": "BENEFIT_NOT_FOUND",
                            "msg": f"Benefício {benefit_id} não encontrado",
                        }
                    },
                )

            benefit_doc = doc.to_dict()

            if soft_delete:
                # Soft delete: marcar como inativo
                benefit_data = benefit_doc[benefit_id]
                if isinstance(benefit_data, dict):
                    benefit_data["status"] = "inactive"
                    benefit_data["updated_at"] = datetime.now(UTC).isoformat()
                    benefit_data["deleted_at"] = datetime.now(UTC).isoformat()

                    benefit_doc[benefit_id] = benefit_data

                    # Atualizar documento diretamente
                    doc_ref.set(benefit_doc)

                    logger.info(f"Soft delete realizado para benefício {benefit_id}")
                    return "soft_deleted"
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail={
                            "error": {
                                "code": "INVALID_BENEFIT_STRUCTURE",
                                "msg": "Estrutura do benefício inválida para soft delete",
                            }
                        },
                    )
            else:
                # Hard delete: remover completamente
                del benefit_doc[benefit_id]

                # Atualizar documento diretamente
                # doc_ref.set(benefit_doc)

                logger.info(f"Hard delete realizado para benefício {benefit_id}")
                return "hard_deleted"

        async def delete_benefit_postgres():
            # Fallback para PostgreSQL (ainda não implementado)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "error": {
                        "code": "FIRESTORE_UNAVAILABLE",
                        "msg": "Firestore indisponível e fallback PostgreSQL não implementado",
                    }
                },
            )

        delete_type = await with_circuit_breaker(
            delete_benefit_firestore, delete_benefit_postgres
        )

        # Verificar se o resultado é válido (não é dados vazios do circuit breaker)
        if isinstance(delete_type, dict) and delete_type.get("data") == []:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "error": {
                        "code": "SERVICE_UNAVAILABLE",
                        "msg": "Serviço temporariamente indisponível",
                    }
                },
            )

        action_msg = "inativado" if delete_type == "soft_deleted" else "removido"
        logger.info(
            f"Benefício {benefit_id} {action_msg} com sucesso para parceiro {partner_id}"
        )
        # Atualiza contadores agregados na coleção 'metadata' (benefits)
        if delete_type == "hard_deleted":
            await metrics_service.update_metadata_on_crud(
                "benefits", current_user.tenant, operation="sub", delta=1
            )

        return {"msg": f"Benefício {action_msg} com sucesso"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Erro ao remover benefício {benefit_id} do parceiro {partner_id}: {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {"code": "SERVER_ERROR", "msg": "Erro ao remover benefício"}
            },
        ) from e


@router.post("/benefits", response_model=EntityResponse)
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
            detail={
                "error": {
                    "code": "SERVER_ERROR",
                    "msg": "Erro ao criar benefício",
                }
            },
        ) from e


@router.get("/metrics", response_model=MetricsResponse)
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
