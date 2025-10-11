"""Modelos de dados para o Portal de Benefícios KNN."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator, model_validator

from src.models.favorites import (
    FavoriteRequest,
    FavoriteResponse,
    StudentPartnerFavorite,
)
from src.utils.id_generators import IDGenerators

from .benefit import (
    Benefit,
    BenefitAudience,
    BenefitCreationDTO,
    BenefitFirestoreDTO,
    BenefitListResponse,
    BenefitResponse,
    BenefitStatus,
    BenefitType,
    BenefitValueType,
)
from .partner import (
    Partner,
    PartnerAddress,
    PartnerCategory,
    PartnerContact,
    PartnerGeolocation,
    PartnerSocialNetworks,
)
from .student import (
    Student,
    StudentAddressDTO,
    StudentContactDTO,
    StudentCreationDTO,
    StudentDTO,
    StudentGuardian,
)
from .validation_code import (
    ValidationCode,
    ValidationCodeCreationRequest,
    ValidationCodeRedeemRequest,
)


class Promotion(BaseModel):
    pass


# Modelos base
class BaseResponse(BaseModel):
    """Modelo base para respostas da API."""

    msg: str = "ok"


class ErrorResponse(BaseModel):
    """Modelo para respostas de erro."""

    error: dict


# Modelos de entidades
# Cursos disponíveis - Map simples baseado no IDGenerators
# Não precisa de classe própria pois não haverá modificações administrativas
COURSES_MAP = {
    course_name: {"code": course_code, "name": course_name}
    for course_name, course_code in IDGenerators.CURSO_CODES.items()
}


def get_course_by_name(course_name: str) -> dict | None:
    """Retorna os dados do curso pelo nome."""
    return COURSES_MAP.get(course_name)


def get_course_by_code(course_code: str) -> dict | None:
    """Retorna os dados do curso pelo código."""
    for _course_name, course_data in COURSES_MAP.items():
        if course_data["code"] == course_code:
            return course_data
    return None


def get_all_courses() -> list[dict]:
    """Retorna todos os cursos disponíveis."""
    return list(COURSES_MAP.values())


class Employee(BaseModel):
    """Modelo para funcionários."""

    id: str = Field(default="")
    tenant_id: str
    cpf_hash: str
    name: str
    email: str
    department: str
    cep: str | None = None
    telefone: str | None = None
    active: bool = True
    favorite_partners: list[str] = Field(default_factory=list)

    def __init__(self, **data):
        super().__init__(**data)
        if not self.id:
            self.id = IDGenerators.gerar_id_funcionario(
                nome=self.name,
                cargo=self.department,
                cep=self.cep or "",
                telefone=self.telefone or "",
            )

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


class RedeemRequest(BaseModel):
    """Modelo para requisição de resgate de código."""

    code: str
    cnpj: str

    @model_validator(mode="after")
    def validate_fields(self) -> "RedeemRequest":
        if not self.code.isdigit() or len(self.code) != 6:
            raise ValueError("Código deve conter 6 dígitos numéricos")
        if not self.cnpj.isdigit() or len(self.cnpj) != 14:
            raise ValueError("CNPJ deve conter 14 dígitos numéricos")
        return self


class NotificationRequest(BaseModel):
    """Modelo para requisição de envio de notificações."""

    target: str
    filter: dict = {}
    message: str
    type: str = "both"

    @field_validator("target")
    @classmethod
    def validate_target(cls, v):
        if v not in ["students", "partners"]:
            raise ValueError('Target deve ser "students" ou "partners"')
        return v

    @field_validator("type")
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

    data: list[Partner]


class PartnerDetailResponse(BaseResponse):
    """Modelo para resposta de detalhes de parceiro."""

    data: PartnerDetail


class ValidationCodeResponse(BaseResponse):
    """Modelo para resposta de geração de código de validação."""

    data: dict


class RedeemResponse(BaseResponse):
    """Modelo para resposta de resgate de código."""

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


# Exportações explícitas do módulo
__all__ = [
    # Modelos base
    "BaseResponse",
    "ErrorResponse",
    # Modelos de entidades
    "Partner",
    "PartnerAddress",
    "PartnerSocialNetworks",
    "PartnerGeolocation",
    "PartnerContact",
    "PartnerCategory",
    "Benefit",
    "BenefitCreationDTO",
    "BenefitFirestoreDTO",
    "BenefitType",
    "BenefitValueType",
    "BenefitAudience",
    "BenefitStatus",
    "FavoriteRequest",
    "FavoriteResponse",
    "StudentPartnerFavorite",
    "Student",
    "StudentDTO",
    "StudentContactDTO",
    "StudentAddressDTO",
    "StudentGuardian",
    "StudentCreationDTO",
    "Employee",
    "ValidationCode",
    "ValidationCodeCreationRequest",
    "ValidationCodeRedeemRequest",
    "Redemption",
    # Modelos de resposta
    "PartnerDetail",
    "PartnerListResponse",
    "PartnerDetailResponse",
    "ValidationCodeResponse",
    "RedeemResponse",
    "ValidationCodeRedeemRequest",
    "BenefitResponse",
    "BenefitListResponse",
    "ReportResponse",
    "MetricsResponse",
    "NotificationResponse",
    "HistoryResponse",
    "FavoritesResponse",
    "EntityResponse",
    "EntityListResponse",
    # Funções utilitárias
    "get_course_by_name",
    "get_course_by_code",
    "get_all_courses",
]
