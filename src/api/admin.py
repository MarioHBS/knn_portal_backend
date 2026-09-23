"""
Implementação dos endpoints para o perfil de administrador (admin).
"""

import os
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from firebase_admin import auth
from pydantic import BaseModel

from src.auth import JWTPayload, validate_admin_role
from src.config import EMAIL_SERVICE_ENABLED
from src.db import firestore_client, postgres_client, with_circuit_breaker
from src.models import (
    BaseResponse,
    CollectionType,
    EntityResponse,
    EntityType,
    NotificationRequest,
    UserModel,
)
from src.models.user import UserFirestoreDTO
from src.utils.auth_service import AuthService
from src.utils.email_service import EmailService
from src.utils.logging import logger
from src.utils.metrics_service import MetricsService

metrics_service_instance = MetricsService()

# Criar router
router = APIRouter(tags=["admin"])

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
    collection: CollectionType,
    entity_id: str,
    user_tenant: str,
    should_exist: bool = True,
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

    if should_exist:
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
    else:
        if existing and existing.get("tenant_id") == user_tenant:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": {
                        "code": "DUPLICATE_ENTITY",
                        "msg": f"O {mapping.get(collection, 'Entidade')} com ID {entity_id} já existe.",
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

        # Log da senha temporária para fins de desenvolvimento
        if os.getenv("ENVIRONMENT") == "development":
            logger.info(f"Senha temporária para {entity_email}: {temp_password}")

        auth.set_custom_user_claims(
            user_record.uid,
            {
                "role": entity.name.lower(),
                "tenant": tenant_id,
                "entity_id": entity_id,
            },
        )

        # Criar documento na coleção 'users' do Firestore usando UserFirestoreDTO
        user_data = UserFirestoreDTO(
            email=entity_email,
            entity_id=entity_id,
            first_access=True,
            name=entity_name,
            role=entity.name.lower(),
            tenant_id=tenant_id,
            updated_at=datetime.now(UTC),
        )
        await firestore_client.create_document(
            CollectionType.USER, doc_id=user_record.uid, data=user_data.model_dump()
        )

        if EMAIL_SERVICE_ENABLED:
            # Enviar e-mail com a senha temporária
            logger.info(f"Iniciando envio de e-mail de boas-vindas para {entity_email}")
            email_service = EmailService()

            body_text = f"Olá {entity_name}, sua conta foi criada com sucesso. Sua senha temporária é: {temp_password}"
            body_html = f"""
                <p>Olá <strong>{entity_name}</strong>,</p>
                <p>Sua conta foi criada com sucesso no KNN Portal Journey Club.</p>
                <p>Sua senha temporária é: <strong>{temp_password}</strong></p>
                <p>Recomendamos que você altere sua senha no primeiro acesso.</p>
            """

            try:
                email_service.send_email(
                    to_email=entity_email,
                    subject="Bem-vindo ao KNN Portal Journey Club!",
                    body_html=body_html,
                    body_text=body_text,
                )
                logger.info(f"E-mail de boas-vindas enviado para {entity_email}")
            except Exception as e:
                logger.error(f"Falha ao enviar e-mail para {entity_email}: {str(e)}")
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


async def update_entity(
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
        result = await firestore_client.update_document(
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
