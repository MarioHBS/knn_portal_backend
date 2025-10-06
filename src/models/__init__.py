"""Modelos de dados para o Portal de Benefícios KNN."""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator

from src.models.favorites import (
    FavoriteRequest,
    FavoriteResponse,
    StudentPartnerFavorite,
)
from src.utils.id_generators import IDGenerators

from .benefit import (
    Benefit,
    BenefitListResponse,
    BenefitRequest,
    BenefitResponse,
)
from .partner import (
    Partner,
    PartnerAddress,
    PartnerCategory,
    PartnerContact,
    PartnerGeolocation,
    PartnerSocialNetworks,
)
from .validation_code import (
    ValidationCode,
    ValidationCodeCreationRequest,
    ValidationCodeRedeemRequest,
)

__all__ = [
    "Benefit",
    "BenefitListResponse",
    "BenefitRequest",
    "BenefitResponse",
    "Partner",
    "PartnerAddress",
    "PartnerCategory",
    "PartnerContact",
    "PartnerGeolocation",
    "PartnerSocialNetworks",
    "FavoriteRequest",
    "FavoriteResponse",
    "StudentPartnerFavorite",
    "ValidationCode",
    "ValidationCodeCreationRequest",
    "ValidationCodeRedeemRequest",
    "BaseResponse",
    "ErrorResponse",
    "COURSES_MAP",
    "get_course_by_name",
    "get_course_by_code",
]


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


class Student(BaseModel):
    """Modelo para alunos."""

    id: str = Field(default="")
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

    def __init__(self, **data):
        super().__init__(**data)
        if not self.id:
            self.id = IDGenerators.gerar_id_aluno(
                nome=self.nome_aluno,
                curso=self.curso,
                cep=self.cep_aluno or "",
                celular=self.celular_aluno or "",
                email=self.email_aluno or "",
            )

    class Config:
        orm_mode = True


# DTOs de Aluno para Firestore
class StudentContactDTO(BaseModel):
    """Subdocumento de contato do aluno (Firestore)."""

    email: str | None = None
    phone: str | None = None


class StudentAddressDTO(BaseModel):
    """Subdocumento de endereço do aluno (Firestore)."""

    zip: str | None = None
    complement: str | None = None
    neighborhood: str | None = None


class StudentGuardianDTO(BaseModel):
    """Subdocumento de responsável do aluno (Firestore)."""

    email: str | None = None
    name: str | None = None


class StudentDTO(BaseModel):
    """
    DTO do Aluno para leitura/escrita no Firestore.

    Esta estrutura espelha os documentos exportados em
    data/firestore_export/firestore_students.json.
    O ID do documento (ex.: "STD_I0L0M0O9_S1") é gerenciado externamente
    como doc_id no Firestore.
    """

    created_at: datetime | None = None
    updated_at: datetime | None = None
    occupation: str | None = None
    tenant_id: str
    contact: StudentContactDTO | None = None
    address: StudentAddressDTO | None = None
    guardian: StudentGuardianDTO | None = None
    active_until: date
    book: str | None = None
    name: str

    class Config:
        orm_mode = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat(),
        }


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

    @field_validator("code")
    @classmethod
    def validate_code(cls, v):
        if not v.isdigit() or len(v) != 6:
            raise ValueError("Código deve conter 6 dígitos numéricos")
        return v

    @field_validator("cnpj")
    @classmethod
    def validate_cnpj(cls, v):
        if not v.isdigit() or len(v) != 14:
            raise ValueError("CNPJ deve conter 14 dígitos numéricos")
        return v


# Modelo legado - manter para compatibilidade temporária
class Promotion(BaseModel):
    """Modelo legado - usar Benefit ao invés desta classe."""

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
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    def __init__(self, **data):
        import warnings

        warnings.warn(
            "Promotion está depreciado. Use Benefit ao invés desta classe.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(**data)

    @field_validator("audience")
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

    @field_validator("valid_to")
    @classmethod
    def validate_dates(cls, v, info):
        """Valida se a data de término é posterior à data de início."""
        try:
            if (
                hasattr(info, "data")
                and info.data
                and hasattr(info.data, "get")
                and info.data.get("valid_from")
                and v <= info.data.get("valid_from")
            ):
                raise ValueError("Data de término deve ser posterior à data de início")
        except (TypeError, AttributeError):
            # Se info.data não for iterável ou não tiver get, pular a validação
            pass
        return v

    class Config:
        orm_mode = True


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

    @field_validator("audience")
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

    @field_validator("valid_to")
    @classmethod
    def validate_dates(cls, v, info):
        """Valida se a data de término é posterior à data de início."""
        try:
            if (
                hasattr(info, "data")
                and info.data
                and hasattr(info.data, "get")
                and info.data.get("valid_from")
                and v <= info.data.get("valid_from")
            ):
                raise ValueError("Data de término deve ser posterior à data de início")
        except (TypeError, AttributeError):
            # Se info.data não for iterável ou não tiver get, pular a validação
            pass
        return v


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
    "BenefitConfiguration",
    "BenefitDates",
    "BenefitSystem",
    "BenefitMetadata",
    "BenefitRestrictions",
    "BenefitCooldownPeriod",
    "BenefitValidHours",
    "FirestoreTimestamp",
    "BenefitValueType",
    "BenefitCalculationMethod",
    "BenefitRequirement",
    "BenefitStatus",
    "BenefitType",
    "BenefitAudience",
    "BenefitCategory",
    "WeekDay",
    "FavoriteRequest",
    "FavoriteResponse",
    "StudentPartnerFavorite",
    "Student",
    "StudentDTO",
    "StudentContactDTO",
    "StudentAddressDTO",
    "StudentGuardianDTO",
    "Employee",
    "ValidationCode",
    "ValidationCodeRedeemRequest",
    "Redemption",
    "Promotion",
    "PromotionRequest",
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
