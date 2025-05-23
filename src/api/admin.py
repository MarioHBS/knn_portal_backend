"""
Implementação dos endpoints para o perfil de administrador (admin).
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime

from src.auth import validate_admin_role, JWTPayload
from src.models import (
    Student, Partner, Promotion, ValidationCode, Redemption,
    EntityResponse, EntityListResponse, MetricsResponse, NotificationRequest, BaseResponse
)
from src.db import firestore_client, postgres_client, with_circuit_breaker
from src.utils import logger

# Criar router
router = APIRouter(tags=["admin"])

@router.get("/admin/{entity}", response_model=EntityListResponse)
async def list_entities(
    entity: str = Path(..., description="Tipo de entidade"),
    limit: int = Query(20, ge=1, le=100, description="Número máximo de itens por página"),
    offset: int = Query(0, ge=0, description="Offset para paginação"),
    current_user: JWTPayload = Depends(validate_admin_role)
):
    """
    Retorna lista de entidades (students, partners, promotions, etc.).
    """
    try:
        # Validar tipo de entidade
        valid_entities = ["students", "partners", "promotions", "validation_codes", "redemptions"]
        if entity not in valid_entities:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": {"code": "INVALID_ENTITY", "msg": f"Entidade inválida. Use: {', '.join(valid_entities)}"}}
            )
        
        # Consultar entidades
        async def get_firestore_entities():
            return await firestore_client.query_documents(
                entity,
                limit=limit,
                offset=offset
            )
        
        async def get_postgres_entities():
            return await postgres_client.query_documents(
                entity,
                limit=limit,
                offset=offset
            )
        
        result = await with_circuit_breaker(get_firestore_entities, get_postgres_entities)
        
        return {"data": result, "msg": "ok"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao listar entidades {entity}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {"code": "SERVER_ERROR", "msg": f"Erro ao listar entidades {entity}"}}
        )

@router.post("/admin/{entity}", response_model=EntityResponse)
async def create_entity(
    entity: str = Path(..., description="Tipo de entidade"),
    data: Dict[str, Any] = None,
    current_user: JWTPayload = Depends(validate_admin_role)
):
    """
    Cria uma nova entidade (student, partner, promotion, etc.).
    """
    try:
        # Validar tipo de entidade
        valid_entities = ["students", "partners", "promotions"]
        if entity not in valid_entities:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": {"code": "INVALID_ENTITY", "msg": f"Entidade inválida. Use: {', '.join(valid_entities)}"}}
            )
        
        # Validar dados
        if not data:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"error": {"code": "VALIDATION_ERROR", "msg": "Dados inválidos"}}
            )
        
        # Gerar ID se não fornecido
        if "id" not in data:
            data["id"] = str(uuid.uuid4())
        
        # Criar entidade
        result = await firestore_client.create_document(entity, data, data["id"])
        
        return {"data": result, "msg": "ok"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao criar entidade {entity}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {"code": "SERVER_ERROR", "msg": f"Erro ao criar entidade {entity}"}}
        )

@router.put("/admin/{entity}/{id}", response_model=EntityResponse)
async def update_entity(
    entity: str = Path(..., description="Tipo de entidade"),
    id: str = Path(..., description="ID da entidade"),
    data: Dict[str, Any] = None,
    current_user: JWTPayload = Depends(validate_admin_role)
):
    """
    Atualiza uma entidade existente (student, partner, promotion, etc.).
    """
    try:
        # Validar tipo de entidade
        valid_entities = ["students", "partners", "promotions"]
        if entity not in valid_entities:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": {"code": "INVALID_ENTITY", "msg": f"Entidade inválida. Use: {', '.join(valid_entities)}"}}
            )
        
        # Validar dados
        if not data:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"error": {"code": "VALIDATION_ERROR", "msg": "Dados inválidos"}}
            )
        
        # Verificar se a entidade existe
        async def get_firestore_entity():
            return await firestore_client.get_document(entity, id)
        
        async def get_postgres_entity():
            return await postgres_client.get_document(entity, id)
        
        existing_entity = await with_circuit_breaker(get_firestore_entity, get_postgres_entity)
        
        if not existing_entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": {"code": "NOT_FOUND", "msg": f"Entidade {entity} com ID {id} não encontrada"}}
            )
        
        # Atualizar entidade
        result = await firestore_client.update_document(entity, id, data)
        
        return {"data": result, "msg": "ok"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao atualizar entidade {entity}/{id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {"code": "SERVER_ERROR", "msg": f"Erro ao atualizar entidade {entity}/{id}"}}
        )

@router.delete("/admin/{entity}/{id}", response_model=BaseResponse)
async def delete_entity(
    entity: str = Path(..., description="Tipo de entidade"),
    id: str = Path(..., description="ID da entidade"),
    current_user: JWTPayload = Depends(validate_admin_role)
):
    """
    Remove ou inativa uma entidade existente (student, partner, promotion, etc.).
    """
    try:
        # Validar tipo de entidade
        valid_entities = ["students", "partners", "promotions"]
        if entity not in valid_entities:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": {"code": "INVALID_ENTITY", "msg": f"Entidade inválida. Use: {', '.join(valid_entities)}"}}
            )
        
        # Verificar se a entidade existe
        async def get_firestore_entity():
            return await firestore_client.get_document(entity, id)
        
        async def get_postgres_entity():
            return await postgres_client.get_document(entity, id)
        
        existing_entity = await with_circuit_breaker(get_firestore_entity, get_postgres_entity)
        
        if not existing_entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": {"code": "NOT_FOUND", "msg": f"Entidade {entity} com ID {id} não encontrada"}}
            )
        
        # Para entidades que suportam soft delete, apenas inativar
        if entity in ["students", "partners", "promotions"]:
            await firestore_client.update_document(entity, id, {"active": False})
        else:
            # Para outras entidades, remover completamente
            await firestore_client.delete_document(entity, id)
        
        return {"msg": "ok"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao remover entidade {entity}/{id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {"code": "SERVER_ERROR", "msg": f"Erro ao remover entidade {entity}/{id}"}}
        )

@router.get("/admin/metrics", response_model=MetricsResponse)
async def get_metrics(
    current_user: JWTPayload = Depends(validate_admin_role)
):
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
                filters=[("active_until", ">=", today)]
            )
            return result.get("total", 0)
        
        async def count_postgres_active_students():
            from datetime import date
            today = date.today().isoformat()
            
            result = await postgres_client.query_documents(
                "students",
                filters=[("active_until", ">=", today)]
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
                "validation_codes",
                filters=[("used_at", "!=", None)]
            )
            return result.get("total", 0)
        
        async def count_postgres_redeemed_codes():
            result = await postgres_client.query_documents(
                "validation_codes",
                filters=[("used_at", "!=", None)]
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
                filters=[("active", "==", True)],
                limit=5
            )
        
        async def get_postgres_partners():
            return await postgres_client.query_documents(
                "partners",
                filters=[("active", "==", True)],
                limit=5
            )
        
        partners_result = await with_circuit_breaker(
            get_firestore_partners, get_postgres_partners
        )
        
        for partner in partners_result.get("items", []):
            # Contar resgates para este parceiro
            async def count_firestore_partner_redemptions():
                codes_result = await firestore_client.query_documents(
                    "validation_codes",
                    filters=[
                        ("partner_id", "==", partner["id"]),
                        ("used_at", "!=", None)
                    ]
                )
                return codes_result.get("total", 0)
            
            async def count_postgres_partner_redemptions():
                codes_result = await postgres_client.query_documents(
                    "validation_codes",
                    filters=[
                        ("partner_id", "==", partner["id"]),
                        ("used_at", "!=", None)
                    ]
                )
                return codes_result.get("total", 0)
            
            redemptions = await with_circuit_breaker(
                count_firestore_partner_redemptions, count_postgres_partner_redemptions
            )
            
            top_partners.append({
                "partner_id": partner["id"],
                "trade_name": partner.get("trade_name", ""),
                "redemptions": redemptions
            })
        
        # Ordenar por número de resgates (decrescente)
        top_partners.sort(key=lambda x: x["redemptions"], reverse=True)
        
        return {
            "data": {
                "active_students": active_students,
                "codes_generated": codes_generated,
                "codes_redeemed": codes_redeemed,
                "top_partners": top_partners
            },
            "msg": "ok"
        }
    
    except Exception as e:
        logger.error(f"Erro ao obter métricas: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {"code": "SERVER_ERROR", "msg": "Erro ao obter métricas"}}
        )

@router.post("/admin/notifications", response_model=BaseResponse)
async def send_notifications(
    request: NotificationRequest,
    current_user: JWTPayload = Depends(validate_admin_role)
):
    """
    Envia notificações push/e-mail para alunos ou parceiros.
    """
    try:
        # Validar target
        if request.target not in ["students", "partners"]:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"error": {"code": "INVALID_TARGET", "msg": "Target deve ser 'students' ou 'partners'"}}
            )
        
        # Validar tipo de notificação
        if request.type not in ["email", "push", "both"]:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"error": {"code": "INVALID_TYPE", "msg": "Type deve ser 'email', 'push' ou 'both'"}}
            )
        
        # Obter destinatários
        filters = []
        
        # Aplicar filtros adicionais
        for key, value in request.filter.items():
            filters.append((key, "==", value))
        
        async def get_firestore_recipients():
            return await firestore_client.query_documents(
                request.target,
                filters=filters
            )
        
        async def get_postgres_recipients():
            return await postgres_client.query_documents(
                request.target,
                filters=filters
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
            message=request.message
        )
        
        return {
            "data": {
                "recipients": len(recipients),
                "message_id": message_id
            },
            "msg": "ok"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao enviar notificações: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {"code": "SERVER_ERROR", "msg": "Erro ao enviar notificações"}}
        )
