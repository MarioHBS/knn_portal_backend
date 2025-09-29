"""
Implementação dos endpoints para o perfil de administrador (admin).
"""

import uuid
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
from src.models.benefit import BenefitRequest
from src.utils import logger
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


@router.post("/students", response_model=EntityResponse)
async def create_student(
    data: dict[str, Any] = Body(..., description="Dados do estudante"),
    current_user: JWTPayload = Depends(validate_admin_role),
):
    """
    Cria um novo estudante.
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
                "type": "student",
            }
        )

        # Criar estudante
        result = await firestore_client.create_document("students", data, data["id"])
        return {"data": result, "msg": "Estudante criado com sucesso"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao criar estudante: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {"code": "SERVER_ERROR", "msg": "Erro ao criar estudante"}
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
                "type": "employee",
            }
        )

        # Criar funcionário
        result = await firestore_client.create_document("employees", data, data["id"])
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
    status: str | None = Query(
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
            f"Admin {admin_id} listando benefícios - Tenant: {tenant_id} - Filtros: partner_id={partner_id}, category={category}, status={status}"
        )

        # Função auxiliar para converter dados do Firestore
        def convert_firestore_data(data):
            """Converte dados do Firestore para formato compatível com Pydantic."""
            if isinstance(data, dict):
                converted = {k: convert_firestore_data(v) for k, v in data.items()}
                # Normalizar campo audience para string se for lista
                if "system" in converted and "audience" in converted["system"]:
                    audience = converted["system"]["audience"]
                    if isinstance(audience, list):
                        # Converter lista para string separada por vírgula
                        converted["system"]["audience"] = ",".join(audience)
                return converted
            elif hasattr(data, "timestamp"):  # DatetimeWithNanoseconds
                return data.timestamp()
            elif isinstance(data, list):
                return [convert_firestore_data(item) for item in data]
            else:
                return data

        # Buscar todos os documentos da coleção benefits usando a mesma abordagem do partner
        async def get_firestore_all_benefits():
            from src.db.firestore import get_database

            db = get_database()
            all_benefits = []

            # Buscar todos os documentos da coleção benefits
            benefits_collection = db.collection("benefits")
            docs = benefits_collection.stream()

            for doc in docs:
                partner_doc_id = doc.id
                partner_data = doc.to_dict()

                if not isinstance(partner_data, dict):
                    continue

                # Processar benefícios do parceiro
                for benefit_key, benefit_data in partner_data.items():
                    if benefit_key.startswith("BNF_") and isinstance(
                        benefit_data, dict
                    ):
                        try:
                            # Converter dados do Firestore para formato compatível
                            converted_benefit_data = convert_firestore_data(
                                benefit_data
                            )

                            # Adicionar partner_id ao benefício
                            benefit_with_partner = {
                                **converted_benefit_data,
                                "benefit_id": benefit_key,
                                "partner_id": partner_doc_id,
                            }

                            # Aplicar filtros
                            if partner_id and partner_doc_id != partner_id:
                                continue

                            if (
                                category
                                and benefit_data.get("system", {}).get("category")
                                != category
                            ):
                                continue

                            if (
                                status
                                and benefit_data.get("system", {}).get("status")
                                != status
                            ):
                                continue

                            all_benefits.append(benefit_with_partner)

                        except Exception as e:
                            logger.warning(
                                f"Erro ao processar benefício {benefit_key} do parceiro {partner_doc_id}: {str(e)}"
                            )
                            continue

            return {"data": all_benefits}

        async def get_postgres_all_benefits():
            # Fallback para PostgreSQL se necessário
            return {"data": []}

        # Usar circuit breaker para operações do Firestore
        benefits_result = await with_circuit_breaker(
            get_firestore_all_benefits, get_postgres_all_benefits
        )

        benefits_list = benefits_result.get("data", [])

        # Ordenar por data de criação (mais recente primeiro)
        benefits_list.sort(
            key=lambda x: x.get("dates", {}).get("created_at", ""), reverse=True
        )

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

        # Usar circuit breaker para operações do Firestore
        @with_circuit_breaker
        async def get_benefit():
            partner_doc = await firestore_client.get_document(
                "benefits", partner_id, current_user.tenant
            )

            if not partner_doc:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "error": {
                            "code": "PARTNER_NOT_FOUND",
                            "msg": f"Parceiro {partner_id} não encontrado",
                        }
                    },
                )

            if benefit_id not in partner_doc:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "error": {
                            "code": "BENEFIT_NOT_FOUND",
                            "msg": f"Benefício {benefit_id} não encontrado para o parceiro {partner_id}",
                        }
                    },
                )

            benefit_data = partner_doc[benefit_id]

            # Adicionar informações do parceiro e benefício
            benefit_with_ids = {
                **benefit_data,
                "benefit_id": benefit_id,
                "partner_id": partner_id,
            }

            return benefit_with_ids

        benefit = await get_benefit()

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
    benefit_data: BenefitRequest = None,
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

        benefit_structure = {
            "metadata": {
                "tags": getattr(
                    benefit_data,
                    "tags",
                    [getattr(benefit_data, "category", "").lower(), "desconto"],
                )
            },
            "title": benefit_data.title,
            "description": getattr(benefit_data, "description", ""),
            "configuration": {
                "value": getattr(benefit_data, "value", 0),
                "value_type": getattr(benefit_data, "value_type", "percentage"),
                "calculation_method": getattr(
                    benefit_data, "calculation_method", "final_amount"
                ),
                "description": getattr(benefit_data, "description", ""),
                "terms_conditions": getattr(benefit_data, "terms_conditions", ""),
                "requirements": getattr(
                    benefit_data, "requirements", ["comprovante_vinculo_knn"]
                ),
                "applicable_services": getattr(benefit_data, "applicable_services", []),
                "excluded_services": getattr(benefit_data, "excluded_services", []),
                "additional_benefits": getattr(benefit_data, "additional_benefits", []),
                "restrictions": {
                    "minimum_purchase": getattr(benefit_data, "minimum_purchase", 0),
                    "maximum_discount_amount": getattr(
                        benefit_data, "maximum_discount_amount", None
                    ),
                    "valid_locations": getattr(
                        benefit_data, "valid_locations", ["todas"]
                    ),
                },
            },
            "limits": {
                "usage": {
                    "per_day": getattr(benefit_data, "per_day", -1),
                    "per_week": getattr(benefit_data, "per_week", -1),
                    "per_month": getattr(benefit_data, "per_month", 1),
                    "per_year": getattr(benefit_data, "per_year", -1),
                    "lifetime": getattr(benefit_data, "lifetime", -1),
                },
                "temporal": {
                    "cooldown_period": {
                        "days": getattr(benefit_data, "cooldown_days", 0),
                        "weeks": getattr(benefit_data, "cooldown_weeks", 0),
                        "months": getattr(benefit_data, "cooldown_months", 0),
                        "description": getattr(
                            benefit_data,
                            "cooldown_description",
                            "Sem período de carência",
                        ),
                    },
                    "valid_hours": {
                        "start": getattr(benefit_data, "valid_hours_start", "00:00"),
                        "end": getattr(benefit_data, "valid_hours_end", "23:59"),
                    },
                    "valid_days": getattr(
                        benefit_data,
                        "valid_days",
                        [
                            "monday",
                            "tuesday",
                            "wednesday",
                            "thursday",
                            "friday",
                            "saturday",
                            "sunday",
                        ],
                    ),
                },
                "financial": {
                    "max_discount_amount": getattr(
                        benefit_data, "max_discount_amount", None
                    ),
                    "min_purchase_amount": getattr(
                        benefit_data, "min_purchase_amount", 0
                    ),
                    "max_purchase_amount": getattr(
                        benefit_data, "max_purchase_amount", None
                    ),
                },
            },
            "dates": {
                "created_at": getattr(benefit_data, "created_at", current_time),
                "updated_at": current_time,
                "valid_from": benefit_data.valid_from.isoformat()
                if hasattr(benefit_data, "valid_from") and benefit_data.valid_from
                else current_time,
                "valid_until": benefit_data.valid_to.isoformat()
                if hasattr(benefit_data, "valid_to") and benefit_data.valid_to
                else None,
            },
            "system": {
                "tenant_id": current_user.tenant,
                "status": getattr(benefit_data, "status", "active"),
                "type": benefit_data.type,
                "audience": benefit_data.audience,
                "category": getattr(benefit_data, "category", "desconto"),
            },
        }

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
                existing_benefit["dates"]["valid_from"] = (
                    benefit_data.valid_from.isoformat()
                )
            if hasattr(benefit_data, "valid_to") and benefit_data.valid_to:
                existing_benefit["dates"]["valid_until"] = (
                    benefit_data.valid_to.isoformat()
                )

            # Atualizar configuração se fornecida
            if "configuration" not in existing_benefit:
                existing_benefit["configuration"] = {}

            if hasattr(benefit_data, "value"):
                existing_benefit["configuration"]["value"] = benefit_data.value
            if hasattr(benefit_data, "value_type"):
                existing_benefit["configuration"]["value_type"] = (
                    benefit_data.value_type
                )

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
    soft_delete: bool = Query(False, description="Usar soft delete (padrão: False - Hard Delete)"),
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

            doc_ref = db.collection("benefits").document(partner_id)
            doc = doc_ref.get()

            if not doc.exists:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "error": {
                            "code": "PARTNER_NOT_FOUND",
                            "msg": f"Parceiro {partner_id} não encontrado",
                        }
                    },
                )

            partner_doc = doc.to_dict()

            if benefit_id not in partner_doc:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "error": {
                            "code": "BENEFIT_NOT_FOUND",
                            "msg": f"Benefício {benefit_id} não encontrado para o parceiro {partner_id}",
                        }
                    },
                )

            if soft_delete:
                # Soft delete: marcar como inativo
                benefit_data = partner_doc[benefit_id]
                if isinstance(benefit_data, dict):
                    benefit_data["system"]["status"] = "inactive"
                    benefit_data["dates"]["updated_at"] = datetime.now(UTC).isoformat()
                    benefit_data["dates"]["deleted_at"] = datetime.now(UTC).isoformat()

                    partner_doc[benefit_id] = benefit_data

                    # Atualizar documento diretamente
                    doc_ref.set(partner_doc)

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
                del partner_doc[benefit_id]

                # Atualizar documento diretamente
                doc_ref.set(partner_doc)

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
    data: dict[str, Any] = Body(..., description="Dados do benefício"),
    current_user: JWTPayload = Depends(validate_admin_role),
):
    """
    Cria um novo benefício para um parceiro específico.
    Segue a estrutura do Firestore onde benefícios são agrupados por parceiro.
    """
    try:
        # Validar se partner_id está presente
        if "partner_id" not in data:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "msg": "partner_id é obrigatório para benefícios",
                    }
                },
            )

        # Validar campos obrigatórios do benefício
        required_fields = ["title", "description", "value", "category"]
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

        partner_id = data["partner_id"]

        # Gerar ID único para o benefício
        benefit_id = f"BNF_{str(uuid.uuid4()).replace('-', '')[:6].upper()}_DC"

        logger.info(
            f"🆔 Gerando novo benefício com ID: {benefit_id} para parceiro: {partner_id}"
        )

        # Criar estrutura do benefício baseada no schema do JSON
        current_time = datetime.now(UTC).isoformat()

        benefit_structure = {
            "metadata": {
                "tags": data.get("tags", [data.get("category", "").lower(), "desconto"])
            },
            "title": data["title"],
            "description": data["description"],
            "configuration": {
                "value": data["value"],
                "value_type": data.get("value_type", "percentage"),
                "calculation_method": data.get("calculation_method", "final_amount"),
                "description": data["description"],
                "terms_conditions": data.get("terms_conditions", ""),
                "requirements": data.get("requirements", ["comprovante_vinculo_knn"]),
                "applicable_services": data.get("applicable_services", []),
                "excluded_services": data.get("excluded_services", []),
                "additional_benefits": data.get("additional_benefits", []),
                "restrictions": {
                    "minimum_purchase": data.get("minimum_purchase", 0),
                    "maximum_discount_amount": data.get("maximum_discount_amount"),
                    "valid_locations": data.get("valid_locations", ["todas"]),
                },
            },
            "limits": {
                "usage": {
                    "per_day": data.get("per_day", -1),
                    "per_week": data.get("per_week", -1),
                    "per_month": data.get("per_month", 1),
                    "per_year": data.get("per_year", -1),
                    "lifetime": data.get("lifetime", -1),
                },
                "temporal": {
                    "cooldown_period": {
                        "days": data.get("cooldown_days", 0),
                        "weeks": data.get("cooldown_weeks", 0),
                        "months": data.get("cooldown_months", 0),
                        "description": data.get(
                            "cooldown_description", "Sem período de carência"
                        ),
                    },
                    "valid_hours": {
                        "start": data.get("valid_hours_start", "00:00"),
                        "end": data.get("valid_hours_end", "23:59"),
                    },
                    "valid_days": data.get(
                        "valid_days",
                        [
                            "monday",
                            "tuesday",
                            "wednesday",
                            "thursday",
                            "friday",
                            "saturday",
                            "sunday",
                        ],
                    ),
                },
                "financial": {
                    "max_discount_amount": data.get("max_discount_amount"),
                    "min_purchase_amount": data.get("min_purchase_amount", 0),
                    "max_purchase_amount": data.get("max_purchase_amount"),
                },
            },
            "dates": {
                "created_at": current_time,
                "updated_at": current_time,
                "valid_from": data.get("valid_from", current_time),
                "valid_until": data.get("valid_until"),
            },
            "system": {
                "tenant_id": current_user.tenant,
                "status": data.get("status", "active"),
                "type": data.get("type", "discount"),
                "audience": data.get("audience", "students"),
                "category": data["category"],
            },
        }

        # Verificar se já existe documento do parceiro na coleção benefits
        try:
            # Buscar documento diretamente pelo partner_id (sem tenant prefix)
            # O tenant está armazenado dentro dos dados do benefício em system.tenant_id
            doc_ref = db.collection("benefits").document(partner_id)
            doc = doc_ref.get()
            partner_doc = {**doc.to_dict(), "id": doc.id} if doc.exists else None

            logger.info(
                f"📄 Documento do parceiro {partner_id} {'encontrado' if partner_doc else 'não encontrado'}"
            )

            if partner_doc:
                logger.info(
                    f"📊 Benefícios existentes no documento: {list(partner_doc.keys()) if isinstance(partner_doc, dict) else 'N/A'}"
                )

                # Documento existe, adicionar apenas o novo benefício
                update_data = {
                    benefit_id: benefit_structure,
                    "updated_at": current_time,
                }

                logger.info(
                    f"🔄 Atualizando documento existente com novo benefício {benefit_id}"
                )

                # Atualizar documento usando o firestore_client
                await firestore_client.update_document(
                    "benefits", partner_id, update_data
                )

                logger.info(
                    f"✅ Benefício {benefit_id} adicionado ao documento existente"
                )
            else:
                # Documento não existe, criar novo com benefício diretamente
                new_doc = {
                    benefit_id: benefit_structure,
                    "created_at": current_time,
                    "updated_at": current_time,
                }

                logger.info(
                    f"🆕 Criando novo documento para parceiro {partner_id} com benefício {benefit_id}"
                )

                # Usar apenas o partner_id como ID do documento (sem tenant prefix)
                # A informação do tenant está dentro dos dados do benefício em system.tenant_id

                await firestore_client.create_document(
                    "benefits", new_doc, doc_id=partner_id
                )

                logger.info(
                    f"✅ Novo documento criado com ID {partner_id} e benefício {benefit_id}"
                )

            return {
                "data": {
                    "benefit_id": benefit_id,
                    "partner_id": partner_id,
                    "structure": benefit_structure,
                },
                "msg": "Benefício criado com sucesso",
            }

        except Exception as e:
            logger.error(
                f"Erro ao criar benefício para parceiro {partner_id}: {str(e)}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": {
                        "code": "SERVER_ERROR",
                        "msg": f"Erro ao criar benefício para parceiro {partner_id}",
                    }
                },
            ) from e

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao criar benefício: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {"code": "SERVER_ERROR", "msg": "Erro ao criar benefício"}
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
                "students", filters=[("active_until", ">=", today)]
            )
            return result.get("total", 0)

        async def count_postgres_active_students():
            from datetime import date

            today = date.today().isoformat()

            result = await postgres_client.query_documents(
                "students", filters=[("active_until", ">=", today)]
            )
            return result.get("total", 0)

        active_students = await with_circuit_breaker(
            count_firestore_active_students, count_postgres_active_students
        )

        # Contar códigos gerados
        async def count_firestore_codes():
            result = await firestore_client.query_documents("validation_codes")
            return result.get("total", 0)

        async def count_postgres_codes():
            result = await postgres_client.query_documents("validation_codes")
            return result.get("total", 0)

        codes_generated = await with_circuit_breaker(
            count_firestore_codes, count_postgres_codes
        )

        # Contar códigos resgatados
        async def count_firestore_redeemed_codes():
            result = await firestore_client.query_documents(
                "validation_codes", filters=[("used_at", "!=", None)]
            )
            return result.get("total", 0)

        async def count_postgres_redeemed_codes():
            result = await postgres_client.query_documents(
                "validation_codes", filters=[("used_at", "!=", None)]
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
                "partners", filters=[("active", "==", True)], limit=5
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
