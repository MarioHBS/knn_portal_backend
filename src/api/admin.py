"""
Implementação dos endpoints para o perfil de administrador (admin).
"""

import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query, status

from src.auth import JWTPayload, validate_admin_role
from src.db import firestore_client, postgres_client, with_circuit_breaker
from src.models import (
    BaseResponse,
    EntityListResponse,
    EntityResponse,
    MetricsResponse,
    NotificationRequest,
    Partner,
    PartnerDetail,
    PartnerDetailResponse,
    PartnerListResponse,
)
from src.utils import logger

# Criar router
router = APIRouter(tags=["admin"])


@router.get("/partners", response_model=PartnerListResponse)
async def list_partners(
    cat: str | None = Query(None, description="Filtro por categoria"),
    ord: str | None = Query("name", description="Ordenação (name, category)"),
    limit: int = Query(20, ge=1, le=100, description="Limite de resultados"),
    offset: int = Query(0, ge=0, description="Offset para paginação"),
    current_user: JWTPayload = Depends(validate_admin_role),
) -> PartnerListResponse:
    """
    Lista todos os parceiros disponíveis para administradores com filtros e paginação.
    Administradores podem ver todos os parceiros (ativos e inativos).
    """
    try:
        # Construir filtros (administradores podem ver todos os parceiros)
        filters = {}
        if cat:
            filters["category"] = cat

        # Buscar parceiros
        async def get_firestore_partners():
            return await firestore_client.query_documents(
                "partners",
                tenant_id=current_user.tenant,
                filters=list(filters.items()) if filters else None,
                order_by=[(ord, "ASCENDING")] if ord else None,
                limit=limit,
                offset=offset,
            )

        async def get_postgres_partners():
            return await postgres_client.query_documents(
                "partners",
                filters=list(filters.items()) if filters else None,
                order_by=[(ord, "ASCENDING")] if ord else None,
                limit=limit,
                offset=offset,
                tenant_id=current_user.tenant,
            )

        partners_result = await with_circuit_breaker(
            get_firestore_partners, get_postgres_partners
        )

        # Contar total
        async def count_firestore_partners():
            return await firestore_client.count_documents(
                "partners",
                filters=list(filters.items()) if filters else None,
                tenant_id=current_user.tenant,
            )

        async def count_postgres_partners():
            return await postgres_client.count_documents(
                "partners",
                filters=list(filters.items()) if filters else None,
                tenant_id=current_user.tenant,
            )

        # Converter dados brutos para objetos Partner (garantindo logo_url)
        partner_objects = []
        for partner_data in partners_result.get("items", []):
            try:
                # Garantir que logo_url esteja presente, usando placeholder se necessário
                if not partner_data.get("logo_url"):
                    partner_data["logo_url"] = "/data/placeholder.png"

                partner_obj = Partner(**partner_data)
                partner_objects.append(partner_obj)
            except Exception as e:
                logger.warning(
                    f"Erro ao converter parceiro {partner_data.get('id', 'N/A')}: {e}"
                )
                continue

        return PartnerListResponse(data=partner_objects)

    except Exception as e:
        logger.error(
            f"Erro ao listar parceiros para administrador {current_user.sub}: {e}"
        )
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


@router.get("/{entity}", response_model=EntityListResponse)
async def list_entities(
    entity: str = Path(..., description="Tipo de entidade"),
    limit: int = Query(
        20, ge=1, le=100, description="Número máximo de itens por página"
    ),
    offset: int = Query(0, ge=0, description="Offset para paginação"),
    current_user: JWTPayload = Depends(validate_admin_role),
):
    """
    Retorna lista de entidades (students, partners, promotions, etc.).
    """
    try:
        # Validar tipo de entidade
        valid_entities = [
            "students",
            "employees",
            "partners",
            "promotions",
            "validation_codes",
            "redemptions",
        ]
        if entity not in valid_entities:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": {
                        "code": "INVALID_ENTITY",
                        "msg": f"Entidade inválida. Use: {', '.join(valid_entities)}",
                    }
                },
            )

        # Consultar entidades
        async def get_firestore_entities():
            return await firestore_client.query_documents(
                entity, limit=limit, offset=offset, tenant_id=current_user.tenant
            )

        async def get_postgres_entities():
            return await postgres_client.query_documents(
                entity, limit=limit, offset=offset, tenant_id=current_user.tenant
            )

        entities_data = await with_circuit_breaker(
            get_firestore_entities, get_postgres_entities
        )

        # Contar total
        async def count_firestore_entities():
            return await firestore_client.count_documents(
                entity, tenant_id=current_user.tenant
            )

        async def count_postgres_entities():
            return await postgres_client.count_documents(
                entity, tenant_id=current_user.tenant
            )

        total = await with_circuit_breaker(
            count_firestore_entities, count_postgres_entities
        )

        return EntityListResponse(
            data={
                "items": entities_data.get("items", []),
                "total": total,
                "limit": limit,
                "offset": offset,
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao listar entidades {entity}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "SERVER_ERROR",
                    "msg": f"Erro ao listar entidades {entity}",
                }
            },
        ) from e


@router.post("/{entity}", response_model=EntityResponse)
async def create_entity(
    entity: str = Path(..., description="Tipo de entidade"),
    data: dict[str, Any] = Body(..., description="Dados da entidade"),
    current_user: JWTPayload = Depends(validate_admin_role),
):
    """
    Cria uma nova entidade (student, partner, promotion, etc.).
    """
    try:
        # Validar tipo de entidade
        valid_entities = ["students", "employees", "partners", "promotions", "benefits"]
        if entity not in valid_entities:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": {
                        "code": "INVALID_ENTITY",
                        "msg": f"Entidade inválida. Use: {', '.join(valid_entities)}",
                    }
                },
            )

        # Validar dados
        if not data:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": {"code": "VALIDATION_ERROR", "msg": "Dados inválidos"}
                },
            )

        # Tratamento especial para benefícios - estrutura baseada no documento PTN_A7E6314_EDU
        if entity == "benefits":
            # Validar se partner_id está presente
            if "partner_id" not in data:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail={
                        "error": {"code": "VALIDATION_ERROR", "msg": "partner_id é obrigatório para benefícios"}
                    },
                )
            
            partner_id = data["partner_id"]
            benefit_id = f"BNF_AE_{str(uuid.uuid4()).replace('-', '')[:2]}_DC"
            
            # Criar estrutura do benefício baseada no schema
            current_time = datetime.now(timezone.utc).isoformat()
            
            benefit_structure = {
                "metadata": {
                    "tags": ["educação", "desconto", "funcionário"]
                },
                "title": benefit_id,
                "description": data.get("description", "Benefício criado via admin"),
                "configuration": {
                    "value": data.get("value", 10),
                    "value_type": "percentage",
                    "calculation_method": "final_amount",
                    "description": data.get("description", "Benefício criado via admin"),
                    "terms_conditions": data.get("terms_conditions", ""),
                    "requirements": ["comprovante_vinculo_knn"],
                    "applicable_services": [],
                    "excluded_services": [],
                    "additional_benefits": [],
                    "restrictions": {
                        "minimum_purchase": 0,
                        "maximum_discount_amount": None,
                        "valid_locations": ["todas"]
                    }
                },
                "limits": {
                    "usage": {
                        "per_day": -1,
                        "per_week": -1,
                        "per_month": 1,
                        "per_year": -1,
                        "lifetime": -1
                    },
                    "temporal": {
                        "cooldown_period": {
                            "days": 0,
                            "weeks": 0,
                            "months": 0,
                            "description": "Sem período de carência"
                        },
                        "valid_hours": {
                            "start": "00:00",
                            "end": "23:59"
                        },
                        "valid_days": ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
                    },
                    "financial": {
                        "max_discount_amount": None,
                        "min_purchase_amount": 0,
                        "max_purchase_amount": None
                    }
                },
                "dates": {
                    "created_at": current_time,
                    "updated_at": current_time,
                    "valid_from": current_time,
                    "valid_until": None
                }
            }
            
            # Verificar se já existe documento do parceiro
            try:
                partner_doc = await firestore_client.get_document("benefits", partner_id, current_user.tenant)
                if partner_doc:
                    # Documento existe, adicionar novo benefício na seção data
                    if "data" not in partner_doc:
                        partner_doc["data"] = {}
                    partner_doc["data"][benefit_id] = benefit_structure
                    partner_doc["updated_at"] = current_time
                    result = await firestore_client.update_document("benefits", partner_id, partner_doc, current_user.tenant)
                else:
                    # Documento não existe, criar novo seguindo o schema
                    new_doc = {
                        "data": {
                            benefit_id: benefit_structure
                        },
                        "tenant_id": current_user.tenant,
                        "partner_id": partner_id,
                        "created_at": current_time,
                        "updated_at": current_time
                    }
                    result = await firestore_client.create_document("benefits", new_doc, doc_id=partner_id)
                
                return {"data": {"benefit_id": benefit_id, "structure": benefit_structure}, "msg": "ok"}
                
            except Exception as e:
                logger.error(f"Erro ao criar benefício para parceiro {partner_id}: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail={
                        "error": {
                            "code": "SERVER_ERROR",
                            "msg": f"Erro ao criar benefício para parceiro {partner_id}",
                        }
                    },
                ) from e

        # Gerar ID se não fornecido
        if "id" not in data:
            data["id"] = str(uuid.uuid4())

        # Criar entidade (comportamento padrão para outras entidades)
        result = await firestore_client.create_document(
            entity, data, data["id"]
        )

        return {"data": result, "msg": "ok"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao criar entidade {entity}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "SERVER_ERROR",
                    "msg": f"Erro ao criar entidade {entity}",
                }
            },
        ) from e


@router.get("/{entity}/{id}", response_model=EntityResponse)
async def get_entity(
    entity: str = Path(..., description="Tipo de entidade"),
    id: str = Path(..., description="ID da entidade"),
    current_user: JWTPayload = Depends(validate_admin_role),
):
    """
    Busca uma entidade específica por ID (student, partner, promotion, etc.).
    """
    try:
        # Validar tipo de entidade
        valid_entities = ["students", "employees", "partners", "promotions"]
        if entity not in valid_entities:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": {
                        "code": "INVALID_ENTITY",
                        "msg": f"Entidade inválida. Use: {', '.join(valid_entities)}",
                    }
                },
            )

        # Buscar entidade
        async def get_firestore_entity():
            return await firestore_client.get_document(
                entity, id, tenant_id=current_user.tenant
            )

        async def get_postgres_entity():
            return await postgres_client.get_document(
                entity, id, tenant_id=current_user.tenant
            )

        result = await with_circuit_breaker(get_firestore_entity, get_postgres_entity)

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": {
                        "code": "NOT_FOUND",
                        "msg": f"Entidade {entity} com ID {id} não encontrada",
                    }
                },
            )

        return {"data": result, "msg": "ok"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao buscar entidade {entity}/{id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "SERVER_ERROR",
                    "msg": f"Erro ao buscar entidade {entity}/{id}",
                }
            },
        ) from e


@router.put("/{entity}/{id}", response_model=EntityResponse)
async def update_entity(
    entity: str = Path(..., description="Tipo de entidade"),
    id: str = Path(..., description="ID da entidade"),
    data: dict[str, Any] = Body(..., description="Dados da entidade"),
    current_user: JWTPayload = Depends(validate_admin_role),
):
    """
    Atualiza uma entidade existente (student, partner, promotion, etc.).
    """
    try:
        # Validar tipo de entidade
        valid_entities = ["students", "employees", "partners", "promotions"]
        if entity not in valid_entities:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": {
                        "code": "INVALID_ENTITY",
                        "msg": f"Entidade inválida. Use: {', '.join(valid_entities)}",
                    }
                },
            )

        # Validar dados
        if not data:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": {"code": "VALIDATION_ERROR", "msg": "Dados inválidos"}
                },
            )

        # Verificar se a entidade existe
        async def get_firestore_entity():
            return await firestore_client.get_document(
                entity, id, tenant_id=current_user.tenant
            )

        async def get_postgres_entity():
            return await postgres_client.get_document(
                entity, id, tenant_id=current_user.tenant
            )

        existing_entity = await with_circuit_breaker(
            get_firestore_entity, get_postgres_entity
        )

        if not existing_entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": {
                        "code": "NOT_FOUND",
                        "msg": f"Entidade {entity} com ID {id} não encontrada",
                    }
                },
            )

        # Atualizar entidade
        result = await firestore_client.update_document(
            entity, id, data, tenant_id=current_user.tenant
        )

        return {"data": result, "msg": "ok"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao atualizar entidade {entity}/{id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "SERVER_ERROR",
                    "msg": f"Erro ao atualizar entidade {entity}/{id}",
                }
            },
        ) from e


@router.delete("/{entity}/{id}", response_model=BaseResponse)
async def delete_entity(
    entity: str = Path(..., description="Tipo de entidade"),
    id: str = Path(..., description="ID da entidade"),
    current_user: JWTPayload = Depends(validate_admin_role),
):
    """
    Remove ou inativa uma entidade existente (student, partner, promotion, etc.).
    """
    try:
        # Validar tipo de entidade
        valid_entities = ["students", "employees", "partners", "promotions"]
        if entity not in valid_entities:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": {
                        "code": "INVALID_ENTITY",
                        "msg": f"Entidade inválida. Use: {', '.join(valid_entities)}",
                    }
                },
            )

        # Verificar se a entidade existe
        async def get_firestore_entity():
            return await firestore_client.get_document(
                entity, id, tenant_id=current_user.tenant
            )

        async def get_postgres_entity():
            return await postgres_client.get_document(
                entity, id, tenant_id=current_user.tenant
            )

        existing_entity = await with_circuit_breaker(
            get_firestore_entity, get_postgres_entity
        )

        if not existing_entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": {
                        "code": "NOT_FOUND",
                        "msg": f"Entidade {entity} com ID {id} não encontrada",
                    }
                },
            )

        # Para entidades que suportam soft delete, apenas inativar
        if entity in ["students", "employees", "partners", "promotions"]:
            await firestore_client.update_document(
                entity, id, {"active": False}, tenant_id=current_user.tenant
            )
        else:
            # Para outras entidades, remover completamente
            await firestore_client.delete_document(
                entity, id, tenant_id=current_user.tenant
            )

        return {"msg": "ok"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao remover entidade {entity}/{id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "SERVER_ERROR",
                    "msg": f"Erro ao remover entidade {entity}/{id}",
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
