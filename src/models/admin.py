"""
Modelos de dados para operações administrativas.

Este módulo define os modelos Pydantic utilizados pelos endpoints
administrativos para validação de entrada e formatação de resposta.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

from src.models import BaseResponse


class EntityCreateRequest(BaseModel):
    """Modelo para criação de entidades administrativas."""

    name: str = Field(..., min_length=1, max_length=255, description="Nome da entidade")
    description: str | None = Field(
        None, max_length=1000, description="Descrição da entidade"
    )
    active: bool = Field(True, description="Status ativo da entidade")
    metadata: dict[str, Any] | None = Field(None, description="Metadados adicionais")


class EntityUpdateRequest(BaseModel):
    """Modelo para atualização de entidades administrativas."""

    name: str | None = Field(
        None, min_length=1, max_length=255, description="Nome da entidade"
    )
    description: str | None = Field(
        None, max_length=1000, description="Descrição da entidade"
    )
    active: bool | None = Field(None, description="Status ativo da entidade")
    metadata: dict[str, Any] | None = Field(None, description="Metadados adicionais")


class NotificationRequest(BaseModel):
    """Modelo para envio de notificações administrativas."""

    title: str = Field(
        ..., min_length=1, max_length=255, description="Título da notificação"
    )
    message: str = Field(
        ..., min_length=1, max_length=1000, description="Mensagem da notificação"
    )
    target_audience: list[str] = Field(..., description="Público-alvo da notificação")
    priority: str = Field("normal", description="Prioridade da notificação")

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v):
        """Valida a prioridade da notificação."""
        allowed_priorities = ["low", "normal", "high", "urgent"]
        if v not in allowed_priorities:
            raise ValueError(f"Priority must be one of: {allowed_priorities}")
        return v


class MetricsResponse(BaseModel):
    """Modelo de resposta para métricas administrativas."""

    total_users: int = Field(..., description="Total de usuários")
    active_users: int = Field(..., description="Usuários ativos")
    total_partners: int = Field(..., description="Total de parceiros")
    active_partners: int = Field(..., description="Parceiros ativos")
    total_promotions: int = Field(..., description="Total de promoções")
    active_promotions: int = Field(..., description="Promoções ativas")
    redemptions_today: int = Field(..., description="Resgates hoje")
    redemptions_month: int = Field(..., description="Resgates no mês")
    last_updated: datetime = Field(..., description="Última atualização das métricas")


class AdminEntityResponse(BaseModel):
    """Modelo de resposta para entidades administrativas."""

    id: str = Field(..., description="ID da entidade")
    name: str = Field(..., description="Nome da entidade")
    description: str | None = Field(None, description="Descrição da entidade")
    active: bool = Field(..., description="Status ativo da entidade")
    created_at: datetime = Field(..., description="Data de criação")
    updated_at: datetime | None = Field(None, description="Data de atualização")
    metadata: dict[str, Any] | None = Field(None, description="Metadados adicionais")


class AdminListResponse(BaseResponse):
    """Modelo de resposta paginada para listas administrativas."""

    items: list[AdminEntityResponse] = Field(..., description="Lista de entidades")
    total: int = Field(..., description="Total de itens")
    page: int = Field(..., description="Página atual")
    per_page: int = Field(..., description="Itens por página")


class AdminDetailResponse(BaseResponse):
    """Modelo de resposta para detalhes de entidade administrativa."""

    data: AdminEntityResponse = Field(..., description="Dados da entidade")
