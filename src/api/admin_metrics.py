"""
Endpoints avançados de métricas para administradores.

Este módulo fornece endpoints especializados para coleta, análise e visualização
de métricas do sistema KNN Portal Journey Club.
"""

from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from src.auth import JWTPayload, validate_admin_role
from src.models import BaseResponse
from src.utils import logger
from src.utils.firebase_analytics import analytics_client
from src.utils.metrics_service import metrics_service

router = APIRouter(prefix="/admin/metrics", tags=["Admin Metrics"])


class MetricsSummary(BaseModel):
    """Resumo de métricas do sistema."""

    active_users: int = Field(description="Usuários ativos")
    total_codes: int = Field(description="Total de códigos gerados")
    redeemed_codes: int = Field(description="Códigos resgatados")
    redemption_rate: float = Field(description="Taxa de resgate (%)")
    top_partners: list[dict[str, Any]] = Field(description="Top parceiros")


class PerformanceMetrics(BaseModel):
    """Métricas de performance do sistema."""

    avg_response_time: float = Field(description="Tempo médio de resposta (ms)")
    error_rate: float = Field(description="Taxa de erro (%)")
    requests_per_minute: float = Field(description="Requisições por minuto")
    uptime: float = Field(description="Uptime (%)")
    database_performance: dict[str, float] = Field(description="Performance do banco")


class BusinessMetrics(BaseModel):
    """Métricas de negócio."""

    total_savings: float = Field(description="Economia total (R$)")
    avg_savings_per_user: float = Field(description="Economia média por usuário (R$)")
    partner_engagement: float = Field(description="Engajamento de parceiros")
    user_growth_rate: float = Field(description="Taxa de crescimento de usuários (%)")
    conversion_rate: float = Field(description="Taxa de conversão (%)")


class DashboardData(BaseModel):
    """Dados completos para dashboard administrativo."""

    summary: MetricsSummary
    performance: PerformanceMetrics
    business: BusinessMetrics
    trends: dict[str, list[dict[str, Any]]]
    alerts: list[dict[str, Any]]
    last_updated: datetime


class DashboardResponse(BaseResponse):
    """Resposta do endpoint de dashboard."""

    data: DashboardData


class CounterItem(BaseModel):
    """Item de contador agregado."""

    total: int = Field(0, description="Quantidade total")
    last_updated: datetime | None = Field(
        default=None, description="Última atualização do contador"
    )
    windows: dict[str, Any] | None = Field(
        default=None, description="Contagem por janelas (24h, 7d, 30d)"
    )


class AdminCountersData(BaseModel):
    """Contadores agregados para entidades do sistema."""

    students: CounterItem
    employees: CounterItem
    partners: CounterItem
    benefits: CounterItem
    last_updated: datetime | None


class AdminCountersResponse(BaseResponse):
    """Resposta do endpoint de contadores agregados."""

    data: AdminCountersData


class HistoricalMetricsResponse(BaseResponse):
    """Resposta de métricas históricas."""

    data: dict[str, list[dict[str, Any]]]


class CustomMetricRequest(BaseModel):
    """Requisição para criar métrica customizada."""

    metric_name: str = Field(description="Nome da métrica")
    metric_value: float = Field(description="Valor da métrica")
    metric_type: str = Field(description="Tipo da métrica (gauge, counter, histogram)")
    tags: dict[str, str] | None = Field(default=None, description="Tags adicionais")


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard_metrics(
    current_user: JWTPayload = Depends(validate_admin_role),
    period: str = Query(
        "30d", regex="^(1d|7d|30d|90d)$", description="Período de análise"
    ),
):
    """
    Retorna dados completos para dashboard administrativo.

    Este endpoint fornece uma visão abrangente das métricas do sistema,
    incluindo resumo, performance, métricas de negócio e tendências.

    Args:
        current_user: Usuário autenticado (admin)
        period: Período de análise (1d, 7d, 30d, 90d)

    Returns:
        DashboardResponse: Dados completos do dashboard

    Raises:
        HTTPException: Erro ao obter métricas
    """
    try:
        logger.info(f"Obtendo métricas do dashboard para tenant {current_user.tenant}")

        # Gerar dados do dashboard
        dashboard_data = await metrics_service.generate_dashboard_data(
            current_user.tenant
        )

        # Rastrear acesso ao dashboard
        await analytics_client.track_event(
            "admin_dashboard_access",
            {
                "admin_id": current_user.sub,
                "tenant_id": current_user.tenant,
                "period": period,
                "timestamp": datetime.utcnow().isoformat(),
            },
            tenant_id=current_user.tenant,
        )

        return DashboardResponse(
            data=dashboard_data, msg="Dashboard carregado com sucesso"
        )

    except Exception as e:
        logger.error(f"Erro ao obter dados do dashboard: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "DASHBOARD_ERROR",
                    "msg": "Erro ao carregar dashboard de métricas",
                }
            },
        )


@router.get("/historical", response_model=HistoricalMetricsResponse)
async def get_historical_metrics(
    current_user: JWTPayload = Depends(validate_admin_role),
    start_date: datetime = Query(description="Data de início"),
    end_date: datetime = Query(description="Data de fim"),
    granularity: str = Query(
        "daily", regex="^(hourly|daily|weekly|monthly)$", description="Granularidade"
    ),
):
    """
    Retorna métricas históricas para análise temporal.

    Args:
        current_user: Usuário autenticado (admin)
        start_date: Data de início da análise
        end_date: Data de fim da análise
        granularity: Granularidade dos dados (hourly, daily, weekly, monthly)

    Returns:
        HistoricalMetricsResponse: Métricas históricas

    Raises:
        HTTPException: Erro ao obter métricas históricas
    """
    try:
        # Validar período
        if end_date <= start_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": {
                        "code": "INVALID_DATE_RANGE",
                        "msg": "Data de fim deve ser posterior à data de início",
                    }
                },
            )

        # Limitar período máximo (1 ano)
        max_period = timedelta(days=365)
        if end_date - start_date > max_period:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": {
                        "code": "PERIOD_TOO_LONG",
                        "msg": "Período máximo permitido é de 1 ano",
                    }
                },
            )

        logger.info(f"Obtendo métricas históricas para tenant {current_user.tenant}")

        # Obter métricas históricas
        historical_data = await metrics_service.get_historical_metrics(
            current_user.tenant, start_date, end_date, granularity
        )

        # Rastrear acesso às métricas históricas
        await analytics_client.track_event(
            "admin_historical_metrics_access",
            {
                "admin_id": current_user.sub,
                "tenant_id": current_user.tenant,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "granularity": granularity,
                "data_points": len(historical_data.get("timeline", [])),
            },
            tenant_id=current_user.tenant,
        )

        return HistoricalMetricsResponse(
            data=historical_data, msg="Métricas históricas obtidas com sucesso"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao obter métricas históricas: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "HISTORICAL_METRICS_ERROR",
                    "msg": "Erro ao obter métricas históricas",
                }
            },
        )


@router.get("/counters", response_model=AdminCountersResponse)
async def get_admin_counters(
    current_user: JWTPayload = Depends(validate_admin_role),
):
    """
    Retorna contadores agregados (students, employees, partners, benefits)
    a partir da coleção 'metadata'.

    Ideal para reduzir múltiplas chamadas no Front, disponibilizando uma única
    resposta com todos os totais e último update.
    """
    try:
        aggregated = await metrics_service.get_aggregated_counters(current_user.tenant)

        return AdminCountersResponse(
            data=AdminCountersData(**aggregated),
            msg="Contadores agregados obtidos com sucesso",
        )

    except Exception as e:
        logger.error(f"Erro ao obter contadores agregados: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "COUNTERS_ERROR",
                    "msg": "Erro ao obter contadores agregados",
                }
            },
        ) from e


@router.get("/realtime", response_model=BaseResponse)
async def get_realtime_metrics(current_user: JWTPayload = Depends(validate_admin_role)):
    """
    Retorna métricas em tempo real do sistema.

    Args:
        current_user: Usuário autenticado (admin)

    Returns:
        BaseResponse: Métricas em tempo real

    Raises:
        HTTPException: Erro ao obter métricas em tempo real
    """
    try:
        logger.info(f"Obtendo métricas em tempo real para tenant {current_user.tenant}")

        # Coletar métricas em tempo real
        realtime_data = await metrics_service.collect_real_time_metrics(
            current_user.tenant
        )

        # Rastrear acesso às métricas em tempo real
        await analytics_client.track_event(
            "admin_realtime_metrics_access",
            {
                "admin_id": current_user.sub,
                "tenant_id": current_user.tenant,
                "timestamp": datetime.utcnow().isoformat(),
            },
            tenant_id=current_user.tenant,
        )

        return BaseResponse(
            data=realtime_data, msg="Métricas em tempo real obtidas com sucesso"
        )

    except Exception as e:
        logger.error(f"Erro ao obter métricas em tempo real: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "REALTIME_METRICS_ERROR",
                    "msg": "Erro ao obter métricas em tempo real",
                }
            },
        )


@router.post("/custom", response_model=BaseResponse)
async def create_custom_metric(
    metric_request: CustomMetricRequest,
    current_user: JWTPayload = Depends(validate_admin_role),
):
    """
    Cria uma métrica customizada.

    Args:
        metric_request: Dados da métrica customizada
        current_user: Usuário autenticado (admin)

    Returns:
        BaseResponse: Confirmação da criação

    Raises:
        HTTPException: Erro ao criar métrica customizada
    """
    try:
        logger.info(
            f"Criando métrica customizada '{metric_request.metric_name}' para tenant {current_user.tenant}"
        )

        # Criar métrica customizada
        await metrics_service.create_custom_metric(
            current_user.tenant,
            metric_request.metric_name,
            metric_request.metric_value,
            metric_request.metric_type,
            metric_request.tags or {},
        )

        # Rastrear criação de métrica customizada
        await analytics_client.track_event(
            "custom_metric_created",
            {
                "admin_id": current_user.sub,
                "tenant_id": current_user.tenant,
                "metric_name": metric_request.metric_name,
                "metric_type": metric_request.metric_type,
                "metric_value": metric_request.metric_value,
            },
            tenant_id=current_user.tenant,
        )

        return BaseResponse(
            data={"metric_name": metric_request.metric_name},
            msg="Métrica customizada criada com sucesso",
        )

    except Exception as e:
        logger.error(f"Erro ao criar métrica customizada: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "CUSTOM_METRIC_ERROR",
                    "msg": "Erro ao criar métrica customizada",
                }
            },
        )


@router.get("/performance", response_model=BaseResponse)
async def get_performance_metrics(
    current_user: JWTPayload = Depends(validate_admin_role),
    endpoint: str | None = Query(None, description="Filtrar por endpoint específico"),
):
    """
    Retorna métricas de performance detalhadas.

    Args:
        current_user: Usuário autenticado (admin)
        endpoint: Endpoint específico para filtrar (opcional)

    Returns:
        BaseResponse: Métricas de performance

    Raises:
        HTTPException: Erro ao obter métricas de performance
    """
    try:
        logger.info(
            f"Obtendo métricas de performance para tenant {current_user.tenant}"
        )

        # Obter métricas de performance
        performance_data = await metrics_service._get_performance_metrics(
            current_user.tenant, endpoint_filter=endpoint
        )

        # Rastrear acesso às métricas de performance
        await analytics_client.track_event(
            "admin_performance_metrics_access",
            {
                "admin_id": current_user.sub,
                "tenant_id": current_user.tenant,
                "endpoint_filter": endpoint,
                "timestamp": datetime.utcnow().isoformat(),
            },
            tenant_id=current_user.tenant,
        )

        return BaseResponse(
            data=performance_data, msg="Métricas de performance obtidas com sucesso"
        )

    except Exception as e:
        logger.error(f"Erro ao obter métricas de performance: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "PERFORMANCE_METRICS_ERROR",
                    "msg": "Erro ao obter métricas de performance",
                }
            },
        )


@router.get("/alerts", response_model=BaseResponse)
async def get_system_alerts(
    current_user: JWTPayload = Depends(validate_admin_role),
    severity: str | None = Query(
        None, regex="^(low|medium|high|critical)$", description="Filtrar por severidade"
    ),
):
    """
    Retorna alertas do sistema baseados em métricas.

    Args:
        current_user: Usuário autenticado (admin)
        severity: Filtrar por severidade (low, medium, high, critical)

    Returns:
        BaseResponse: Lista de alertas

    Raises:
        HTTPException: Erro ao obter alertas
    """
    try:
        logger.info(f"Obtendo alertas do sistema para tenant {current_user.tenant}")

        # Obter alertas do sistema
        alerts = await metrics_service.get_system_alerts(
            current_user.tenant, severity_filter=severity
        )

        # Rastrear acesso aos alertas
        await analytics_client.track_event(
            "admin_alerts_access",
            {
                "admin_id": current_user.sub,
                "tenant_id": current_user.tenant,
                "severity_filter": severity,
                "alert_count": len(alerts),
                "timestamp": datetime.utcnow().isoformat(),
            },
            tenant_id=current_user.tenant,
        )

        return BaseResponse(data={"alerts": alerts}, msg="Alertas obtidos com sucesso")

    except Exception as e:
        logger.error(f"Erro ao obter alertas do sistema: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "ALERTS_ERROR",
                    "msg": "Erro ao obter alertas do sistema",
                }
            },
        )


@router.get("/export", response_model=BaseResponse)
async def export_metrics(
    current_user: JWTPayload = Depends(validate_admin_role),
    start_date: datetime = Query(description="Data de início"),
    end_date: datetime = Query(description="Data de fim"),
    format: str = Query(
        "json", regex="^(json|csv|xlsx)$", description="Formato de exportação"
    ),
):
    """
    Exporta métricas para análise externa.

    Args:
        current_user: Usuário autenticado (admin)
        start_date: Data de início da exportação
        end_date: Data de fim da exportação
        format: Formato de exportação (json, csv, xlsx)

    Returns:
        BaseResponse: Link para download do arquivo

    Raises:
        HTTPException: Erro ao exportar métricas
    """
    try:
        # Validar período
        if end_date <= start_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": {
                        "code": "INVALID_DATE_RANGE",
                        "msg": "Data de fim deve ser posterior à data de início",
                    }
                },
            )

        logger.info(f"Exportando métricas para tenant {current_user.tenant}")

        # Exportar métricas
        export_result = await metrics_service.export_metrics(
            current_user.tenant, start_date, end_date, format
        )

        # Rastrear exportação de métricas
        await analytics_client.track_event(
            "metrics_exported",
            {
                "admin_id": current_user.sub,
                "tenant_id": current_user.tenant,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "format": format,
                "file_size": export_result.get("file_size", 0),
            },
            tenant_id=current_user.tenant,
        )

        return BaseResponse(data=export_result, msg="Métricas exportadas com sucesso")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao exportar métricas: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {"code": "EXPORT_ERROR", "msg": "Erro ao exportar métricas"}
            },
        )
