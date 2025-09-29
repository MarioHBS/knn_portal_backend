"""
Endpoints para sincronização automática de dados.

Este módulo fornece endpoints administrativos para gerenciar
a sincronização de URLs de logos dos parceiros.
"""

from datetime import datetime
from typing import Any

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Path,
    Query,
    UploadFile,
    status,
)

from src.auth import JWTPayload, validate_admin_role
from src.utils.logging import logger
from src.utils.partners_sync_service import partners_sync_service
from src.utils.upload_service import upload_service

# Criar router
router = APIRouter(tags=["sync"], prefix="/sync")

# Dependência para validação de usuário administrador
admin_dependency = Depends(validate_admin_role)


@router.post("/partners/logos", response_model=dict[str, Any])
async def sync_all_partner_logos(
    force_update: bool = Query(
        False, description="Forçar atualização de todos os parceiros"
    ),
    current_user: JWTPayload = admin_dependency,
) -> dict[str, Any]:
    """
    Sincroniza as URLs de logos de todos os parceiros (apenas administradores).

    Este endpoint atualiza as URLs de logos na coleção partners,
    garantindo que apontem para as imagens corretas no Firebase Storage.

    Args:
        force_update: Se True, atualiza todos os parceiros independente da data
        current_user: Dados do usuário administrador autenticado

    Returns:
        Relatório da sincronização:
        {
            "status": "completed",
            "total_partners": 150,
            "updated_count": 45,
            "errors": [],
            "duration_seconds": 12.5,
            "timestamp": "2025-01-15T10:30:00Z"
        }

    Raises:
        HTTPException: 401 se não autenticado, 403 se não for admin, 500 em caso de erro
    """
    try:
        logger.info(
            f"Admin {current_user.sub} iniciou sincronização de logos - force_update: {force_update}"
        )

        # Executar sincronização
        result = await partners_sync_service.sync_all_partner_logos(
            force_update=force_update
        )

        # Adicionar informações do usuário
        result["requested_by"] = current_user.sub
        result["force_update"] = force_update

        logger.info(
            f"Sincronização concluída por admin {current_user.sub}: "
            f"{result['updated_count']}/{result['total_partners']} atualizados"
        )

        return result

    except Exception as e:
        logger.error(f"Erro na sincronização para admin {current_user.sub}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "SYNC_ERROR",
                    "msg": "Erro durante sincronização de logos",
                }
            },
        ) from e


@router.post("/partners/{partner_id}/logo", response_model=dict[str, Any])
async def sync_partner_logo(
    partner_id: str,
    current_user: JWTPayload = admin_dependency,
) -> dict[str, Any]:
    """
    Sincroniza a URL do logo de um parceiro específico (apenas administradores).

    Args:
        partner_id: ID do parceiro a ser sincronizado
        current_user: Dados do usuário administrador autenticado

    Returns:
        Resultado da sincronização:
        {
            "partner_id": "PTN_A1E3018_AUT",
            "updated": true,
            "logo_url": "https://...",
            "previous_url": "https://...",
            "timestamp": "2025-01-15T10:30:00Z"
        }

    Raises:
        HTTPException: 401 se não autenticado, 403 se não for admin, 404 se parceiro não encontrado
    """
    try:
        logger.info(
            f"Admin {current_user.sub} solicitou sincronização do parceiro {partner_id}"
        )

        # Executar sincronização do parceiro específico
        result = await partners_sync_service.sync_partner_logo(partner_id)

        # Adicionar informações do usuário
        result["requested_by"] = current_user.sub

        logger.info(
            f"Sincronização do parceiro {partner_id} por admin {current_user.sub}: "
            f"{'atualizado' if result['updated'] else 'já atualizado'}"
        )

        return result

    except ValueError as e:
        logger.warning(
            f"Parceiro {partner_id} não encontrado (admin {current_user.sub})"
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "PARTNER_NOT_FOUND",
                    "msg": f"Parceiro {partner_id} não encontrado",
                }
            },
        ) from e
    except Exception as e:
        logger.error(
            f"Erro na sincronização do parceiro {partner_id} para admin {current_user.sub}: {e}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "SYNC_ERROR",
                    "msg": f"Erro ao sincronizar logo do parceiro {partner_id}",
                }
            },
        ) from e


@router.get("/partners/logos/outdated", response_model=dict[str, Any])
async def check_outdated_logos(
    max_age_hours: int = Query(
        24, description="Idade máxima em horas para considerar o logo atualizado"
    ),
    current_user: JWTPayload = admin_dependency,
) -> dict[str, Any]:
    """
    Verifica parceiros com logos desatualizados (apenas administradores).

    Args:
        max_age_hours: Idade máxima em horas para considerar o logo atualizado
        current_user: Dados do usuário administrador autenticado

    Returns:
        Lista de parceiros com logos desatualizados:
        {
            "outdated_partners": ["PTN_A1E3018_AUT", "PTN_B2F4019_EDU"],
            "total_outdated": 2,
            "max_age_hours": 24,
            "checked_at": "2025-01-15T10:30:00Z"
        }

    Raises:
        HTTPException: 401 se não autenticado, 403 se não for admin, 500 em caso de erro
    """
    try:
        logger.info(
            f"Admin {current_user.sub} verificou logos desatualizados (>{max_age_hours}h)"
        )

        # Verificar logos desatualizados
        outdated_partners = await partners_sync_service.check_outdated_logos(
            max_age_hours=max_age_hours
        )

        result = {
            "outdated_partners": outdated_partners,
            "total_outdated": len(outdated_partners),
            "max_age_hours": max_age_hours,
            "checked_at": datetime.now().isoformat(),
            "checked_by": current_user.sub,
        }

        logger.info(
            f"Verificação concluída por admin {current_user.sub}: "
            f"{len(outdated_partners)} logos desatualizados"
        )

        return result

    except Exception as e:
        logger.error(
            f"Erro na verificação de logos desatualizados para admin {current_user.sub}: {e}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "CHECK_ERROR",
                    "msg": "Erro ao verificar logos desatualizados",
                }
            },
        ) from e


@router.get("/status", summary="Status da sincronização")
async def get_sync_status(
    current_user: dict = Depends(validate_admin_role),
) -> dict[str, str]:
    """
    Obtém status atual da sincronização de logos.

    **Acesso restrito a administradores.**
    """
    try:
        logger.info(
            f"Consultando status da sincronização - Admin: {current_user.get('email')}"
        )

        # Aqui você pode implementar lógica para verificar status
        # Por exemplo, última sincronização, número de logos, etc.

        return {
            "status": "active",
            "message": "Serviço de sincronização operacional",
            "last_sync": "N/A",  # Implementar quando necessário
            "total_logos": "N/A",  # Implementar quando necessário
        }

    except Exception as e:
        logger.error(f"Erro ao obter status da sincronização: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "SYNC_STATUS_ERROR",
                    "msg": "Erro ao obter status da sincronização",
                }
            },
        ) from e


@router.post("/upload", summary="Upload de logo de parceiro")
async def upload_partner_logo(
    partner_id: str = Form(..., description="ID do parceiro"),
    category: str = Form(..., description="Categoria do parceiro (EDU, SAU, etc.)"),
    overwrite: bool = Form(False, description="Sobrescrever arquivo existente"),
    file: UploadFile = File(..., description="Arquivo de logo"),
    current_user: dict = Depends(validate_admin_role),
) -> dict[str, str]:
    """
    Faz upload de logo para um parceiro específico.

    **Acesso restrito a administradores.**

    **Validações aplicadas:**
    - Formato: PNG, JPG, JPEG, WEBP, SVG
    - Tamanho máximo: 5MB
    - Dimensões: 100x100 até 2000x2000 pixels
    - Nomenclatura: PTN_{partner_id}_{category}.{ext}
    """
    try:
        logger.info(
            f"Iniciando upload de logo - Admin: {current_user.get('email')}, "
            f"Parceiro: {partner_id}, Categoria: {category}"
        )

        result = await upload_service.upload_partner_logo(
            file=file, partner_id=partner_id, category=category, overwrite=overwrite
        )

        logger.info(f"Upload concluído com sucesso para parceiro {partner_id}")
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro no upload: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": {"code": "UPLOAD_ERROR", "msg": "Erro interno no upload"}},
        ) from e


@router.delete("/logo/{partner_id}", summary="Remover logo de parceiro")
async def delete_partner_logo(
    partner_id: str = Path(..., description="ID do parceiro"),
    current_user: dict = Depends(validate_admin_role),
) -> dict[str, str]:
    """
    Remove logo de um parceiro específico.

    **Acesso restrito a administradores.**
    """
    try:
        logger.info(
            f"Removendo logo - Admin: {current_user.get('email')}, "
            f"Parceiro: {partner_id}"
        )

        result = await upload_service.delete_partner_logo(partner_id=partner_id)

        logger.info(f"Logo removido com sucesso para parceiro {partner_id}")
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao remover logo: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": {"code": "DELETE_ERROR", "msg": "Erro interno ao remover logo"}
            },
        ) from e
