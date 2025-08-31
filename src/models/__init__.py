"""
Modelos de dados para o Portal de Benefícios KNN.
"""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field, validator


# Modelos base
class BaseResponse(BaseModel):
    """Modelo base para respostas da API."""

    msg: str = "ok"


class ErrorResponse(BaseModel):
    """Modelo para respostas de erro."""

    error: dict


# Modelos de entidades
class Student(BaseModel):
    """Modelo para alunos."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    cpf_hash: str
    nome_aluno: str
    curso: str
    ocupacao_aluno: str | None = None
    email_aluno: str | None = None
    celular_aluno: str | None = None
    cep_aluno: str | None = None
    bairro: str | None = None
    complemento_aluno: str | None = None
    nome_responsavel: str | None = None
    email_responsavel: str | None = None
    active_until: date

    class Config:
        orm_mode = True


class Employee(BaseModel):
    """Modelo para funcionários."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    cpf_hash: str
    name: str
    email: str
    department: str
    active: bool = True
    favorite_partners: list[str] = Field(default_factory=list)

    class Config:
        orm_mode = True


class Partner(BaseModel):
    """Modelo para parceiros."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    cnpj_hash: str
    trade_name: str
    category: str
    address: str
    active: bool = True

    class Config:
        orm_mode = True


class Promotion(BaseModel):
    """Modelo para promoções."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    partner_id: str
    title: str
    type: str
    valid_from: datetime
    valid_to: datetime
    active: bool = True
    audience: list[str] = Field(
        default=["student", "employee"],
        description="Público-alvo: lista com 'student' e/ou 'employee'",
    )

    @validator("audience")
    @classmethod
    def validate_audience(cls, v):
        if not isinstance(v, list) or not v:
            raise ValueError("audience deve ser uma lista não vazia")

        valid_values = {"student", "employee"}
        for item in v:
            if item not in valid_values:
                raise ValueError(
                    'audience deve conter apenas "student" e/ou "employee"'
                )

        # Remove duplicatas mantendo a ordem
        seen = set()
        unique_audience = []
        for item in v:
            if item not in seen:
                seen.add(item)
                unique_audience.append(item)

        return unique_audience

    class Config:
        orm_mode = True


class ValidationCode(BaseModel):
    """Modelo para códigos de validação."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    student_id: str
    partner_id: str
    code_hash: str
    expires: datetime
    used_at: datetime | None = None

    class Config:
        orm_mode = True


class Redemption(BaseModel):
    """Modelo para resgates."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    validation_code_id: str
    value: float
    used_at: datetime

    class Config:
        orm_mode = True


# Modelos para requisições
class ValidationCodeRequest(BaseModel):
    """Modelo para requisição de código de validação."""

    partner_id: str


class RedeemRequest(BaseModel):
    """Modelo para requisição de resgate de código."""

    code: str
    cnpj: str

    @validator("code")
    @classmethod
    def validate_code(cls, v):
        if not v.isdigit() or len(v) != 6:
            raise ValueError("Código deve conter 6 dígitos numéricos")
        return v

    @validator("cnpj")
    @classmethod
    def validate_cnpj(cls, v):
        if not v.isdigit() or len(v) != 14:
            raise ValueError("CNPJ deve conter 14 dígitos numéricos")
        return v


class PromotionRequest(BaseModel):
    """Modelo para requisição de criação/atualização de promoção."""

    title: str
    type: str
    valid_from: datetime
    valid_to: datetime
    active: bool = True
    audience: list[str] = Field(
        default=["student", "employee"],
        description="Público-alvo: lista com 'student' e/ou 'employee'",
    )

    @validator("audience")
    @classmethod
    def validate_audience(cls, v):
        if not isinstance(v, list) or not v:
            raise ValueError("audience deve ser uma lista não vazia")

        valid_values = {"student", "employee"}
        for item in v:
            if item not in valid_values:
                raise ValueError(
                    'audience deve conter apenas "student" e/ou "employee"'
                )

        # Remove duplicatas mantendo a ordem
        seen = set()
        unique_audience = []
        for item in v:
            if item not in seen:
                seen.add(item)
                unique_audience.append(item)

        return unique_audience


class NotificationRequest(BaseModel):
    """Modelo para requisição de envio de notificações."""

    target: str
    filter: dict = {}
    message: str
    type: str = "both"

    @validator("target")
    @classmethod
    def validate_target(cls, v):
        if v not in ["students", "partners"]:
            raise ValueError('Target deve ser "students" ou "partners"')
        return v

    @validator("type")
    @classmethod
    def validate_type(cls, v):
        if v not in ["email", "push", "both"]:
            raise ValueError('Type deve ser "email", "push" ou "both"')
        return v


# Modelos para respostas
class PartnerDetail(Partner):
    """Modelo para detalhes de parceiro com promoções."""

    promotions: list[Promotion] = []


class PartnerListResponse(BaseResponse):
    """Modelo para resposta de listagem de parceiros."""

    data: dict


class PartnerDetailResponse(BaseResponse):
    """Modelo para resposta de detalhes de parceiro."""

    data: PartnerDetail


class ValidationCodeResponse(BaseResponse):
    """Modelo para resposta de geração de código de validação."""

    data: dict


class RedeemResponse(BaseResponse):
    """Modelo para resposta de resgate de código."""

    data: dict


class PromotionResponse(BaseResponse):
    """Modelo para resposta de criação/atualização de promoção."""

    data: Promotion


class PromotionListResponse(BaseResponse):
    """Modelo para resposta de listagem de promoções."""

    data: dict


class ReportResponse(BaseResponse):
    """Modelo para resposta de relatório."""

    data: dict


class MetricsResponse(BaseResponse):
    """Modelo para resposta de métricas."""

    data: dict


class NotificationResponse(BaseResponse):
    """Modelo para resposta de envio de notificações."""

    data: dict


class HistoryResponse(BaseResponse):
    """Modelo para resposta de histórico de resgates."""

    data: dict


class FavoritesResponse(BaseResponse):
    """Modelo para resposta de favoritos."""

    data: list[Partner]


class EntityResponse(BaseModel):
    """Modelo para resposta de entidade."""

    data: dict


class EntityListResponse(BaseResponse):
    """Modelo para resposta de listagem de entidades."""

    data: dict
