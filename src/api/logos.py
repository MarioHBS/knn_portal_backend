"""
Endpoints para gerenciamento de logos de parceiros.

Este módulo fornece endpoints seguros para acesso às imagens de logos
dos parceiros armazenadas no Firebase Storage.
"""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.auth import JWTPayload, validate_authenticated_user
from src.utils.logging import logger
from src.utils.logos_service import logos_service

# Criar router
router = APIRouter(tags=["logos"], prefix="/logos")

# Dependência para validação de usuário autenticado
auth_dependency = Depends(validate_authenticated_user)


@router.get("/", response_model=list[dict[str, str]])
async def list_partner_logos(
    category: str | None = Query(
        None, description="Filtrar por categoria (EDU, AUT, TEC, etc.)"
    ),
    force_refresh: bool = Query(False, description="Forçar atualização do cache"),
    current_user: JWTPayload | None = Depends(
        lambda: None
    ),  # Tornar opcional para teste
) -> list[dict[str, str]]:
    """
    Lista todos os logos de parceiros disponíveis.

    Este endpoint retorna uma lista de logos com URLs assinadas para acesso seguro.
    Temporariamente público para testes.

    Args:
        category: Filtro opcional por categoria de parceiro
        force_refresh: Se True, força atualização do cache
        current_user: Dados do usuário autenticado (opcional para teste)

    Returns:
        Lista de logos com informações detalhadas:
        [
            {
                "partner_id": "PTN_A1E3018_AUT",
                "filename": "PTN_A1E3018_AUT.png",
                "url": "https://...",
                "category": "AUT",
                "size": 12345,
                "updated_at": "2025-01-15T10:30:00Z"
            }
        ]

    Raises:
        HTTPException: 500 se houver erro interno
    """
    try:
        logger.info(
            f"Listagem de logos solicitada - categoria: {category}, force_refresh: {force_refresh}"
        )

        # Obter logos do serviço
        if category:
            logos_data = await logos_service.get_logos_by_category(category)
        else:
            logos_data = await logos_service.list_available_logos(
                force_refresh=force_refresh
            )

        logger.info(f"Retornando {len(logos_data)} logos")
        return logos_data

    except Exception as e:
        logger.error(f"Erro ao listar logos: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "LOGOS_LIST_ERROR",
                    "msg": "Erro interno ao listar logos",
                }
            },
        ) from e


@router.get("/{partner_id}", response_model=dict[str, str])
async def get_partner_logo(
    partner_id: str,
    current_user: JWTPayload = auth_dependency,
) -> dict[str, str]:
    """
    Obtém o logo de um parceiro específico.

    Args:
        partner_id: ID do parceiro (ex: "PTN_A1E3018_AUT")
        current_user: Dados do usuário autenticado (injetado automaticamente)

    Returns:
        Informações do logo do parceiro:
        {
            "partner_id": "PTN_A1E3018_AUT",
            "url": "https://...",
            "found": true
        }

    Raises:
        HTTPException: 401 se não autenticado, 404 se logo não encontrado
    """
    try:
        logger.info(
            f"Usuário {current_user.sub} solicitou logo do parceiro {partner_id}"
        )

        # Buscar URL do logo
        logo_url = await logos_service.get_partner_logo_url(partner_id)

        if not logo_url:
            logger.warning(f"Logo não encontrado para parceiro {partner_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": {
                        "code": "LOGO_NOT_FOUND",
                        "msg": f"Logo não encontrado para o parceiro {partner_id}",
                    }
                },
            )

        logger.info(f"Logo encontrado para parceiro {partner_id}")

        return {"partner_id": partner_id, "url": logo_url, "found": True}

    except HTTPException:
        # Re-raise HTTPExceptions
        raise
    except Exception as e:
        logger.error(f"Erro inesperado ao buscar logo do parceiro {partner_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {"code": "INTERNAL_ERROR", "msg": "Erro interno do servidor"}
            },
        ) from e


@router.get("/categories", response_model=list[str])
async def list_logo_categories(
    current_user: JWTPayload = auth_dependency,
) -> list[str]:
    """
    Lista todas as categorias de logos disponíveis.

    Args:
        current_user: Dados do usuário autenticado (injetado automaticamente)

    Returns:
        Lista de categorias únicas encontradas nos logos

    Raises:
        HTTPException: 401 se não autenticado, 500 em caso de erro interno
    """
    try:
        logger.info(f"Usuário {current_user.sub} solicitou lista de categorias")

        # Obter todos os logos
        logos = await logos_service.list_available_logos()

        # Extrair categorias únicas
        categories = list({logo["category"] for logo in logos})
        categories.sort()

        logger.info(f"Encontradas {len(categories)} categorias: {categories}")

        return categories

    except Exception as e:
        logger.error(f"Erro ao listar categorias para {current_user.sub}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {"code": "INTERNAL_ERROR", "msg": "Erro interno do servidor"}
            },
        ) from e


@router.post("/refresh")
async def refresh_logo_urls(
    current_user: JWTPayload = auth_dependency,
) -> dict[str, Any]:
    """
    Força a regeneração de todas as URLs de logos.
    Útil quando URLs começam a expirar.

    Args:
        current_user: Dados do usuário autenticado (injetado automaticamente)

    Returns:
        Resultado da operação de refresh

    Raises:
        HTTPException: 401 se não autenticado, 500 em caso de erro interno
    """
    try:
        logger.info(f"Usuário {current_user.sub} solicitou refresh das URLs de logos")

        # Regenerar URLs
        refreshed_count = await logos_service.refresh_expired_urls()

        logger.info(f"Refresh concluído: {refreshed_count} URLs regeneradas")

        return {
            "message": "URLs de logos regeneradas com sucesso",
            "refreshed_count": refreshed_count,
            "requested_by": current_user.sub,
            "timestamp": str(datetime.now()),
        }

    except Exception as e:
        logger.error(f"Erro ao fazer refresh das URLs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "REFRESH_ERROR",
                    "msg": "Erro ao regenerar URLs de logos",
                }
            },
        ) from e


@router.post("/cache/clear")
async def clear_logos_cache(
    current_user: JWTPayload = auth_dependency,
) -> dict[str, str]:
    """
    Limpa o cache de logos (apenas para administradores).

    Args:
        current_user: Dados do usuário autenticado (injetado automaticamente)

    Returns:
        Confirmação da operação

    Raises:
        HTTPException: 401 se não autenticado, 403 se não for admin
    """
    try:
        # Verificar se é administrador
        if current_user.role != "admin":
            logger.warning(
                f"Usuário {current_user.sub} tentou limpar cache sem permissão"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": {
                        "code": "INSUFFICIENT_PERMISSIONS",
                        "msg": "Apenas administradores podem limpar o cache",
                    }
                },
            )

        logger.info(f"Admin {current_user.sub} limpou cache de logos")

        # Limpar cache
        logos_service.clear_cache()

        return {
            "message": "Cache de logos limpo com sucesso",
            "cleared_by": current_user.sub,
            "timestamp": str(datetime.now()),
        }

    except HTTPException:
        # Re-raise HTTPExceptions
        raise
    except Exception as e:
        logger.error(f"Erro ao limpar cache: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {"code": "INTERNAL_ERROR", "msg": "Erro interno do servidor"}
            },
        ) from e


@router.get("/health")
async def logos_health_check(
    current_user: JWTPayload = auth_dependency,
) -> dict[str, Any]:
    """
    Verifica a saúde do serviço de logos.

    Args:
        current_user: Dados do usuário autenticado (injetado automaticamente)

    Returns:
        Status do serviço de logos

    Raises:
        HTTPException: 401 se não autenticado
    """
    try:
        logger.debug(f"Health check solicitado por {current_user.sub}")

        health_status = await logos_service.health_check()

        return health_status

    except Exception as e:
        logger.error(f"Erro no health check: {e}")
        return {"status": "error", "error": str(e), "timestamp": str(datetime.now())}
