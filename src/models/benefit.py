"""
Modelos Pydantic para Benefícios do sistema KNN Benefits.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator, model_validator
from pytz import UTC

from src.utils.id_generators import IDGenerators


class BenefitValueType(str, Enum):
    """Tipos de valor de benefício."""

    PERCENTAGE = "percentage"
    FIXED = "fixed"


class BenefitType(str, Enum):
    """Tipos de benefício."""

    DISCOUNT = "discount"
    GIFT = "gift"
    SERVICE = "service"


class BenefitAudience(str, Enum):
    """Público-alvo do benefício."""

    STUDENT = "student"
    EMPLOYEE = "employee"


class BenefitStatus(str, Enum):
    """Status do benefício."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    EXPIRED = "expired"


class BenefitConfigurationDTO(BaseModel):
    """Configuração do benefício para DTO."""

    value: int = Field(..., ge=0, description="Valor do benefício")
    value_type: BenefitValueType = Field(default=BenefitValueType.PERCENTAGE)


class BenefitModel(BaseModel):
    """Modelo principal do Benefício."""

    id: str
    tenant_id: str
    partner_id: str
    title: str
    description: str
    value: int
    value_type: BenefitValueType = BenefitValueType.PERCENTAGE
    tags: list[str] = Field(default_factory=list)
    type: BenefitType = BenefitType.DISCOUNT
    valid_from: datetime
    valid_to: datetime
    active: bool = True
    audience: list[BenefitAudience] = Field(
        default_factory=lambda: [BenefitAudience.STUDENT, BenefitAudience.EMPLOYEE]
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @model_validator(mode="after")
    def validate_dates(self) -> "BenefitModel":
        """Valida se a data de término é posterior à data de início."""
        if self.valid_from and self.valid_to and self.valid_to <= self.valid_from:
            raise ValueError("Data de término deve ser posterior à data de início")
        return self

    class Config:
        use_enum_values = True
        from_attributes = True


# DTOs para Firestore
class BenefitSystemDTO(BaseModel):
    """Subdocumento de sistema do benefício (Firestore)."""

    tenant_id: str
    type: BenefitType
    status: BenefitStatus
    audience: str  # No Firestore: 'students', 'employees', 'all'
    category: str = "Parceiro"


class BenefitMetadataDTO(BaseModel):
    """Subdocumento de metadados do benefício (Firestore)."""

    tags: list[str] = Field(default_factory=list)


class BenefitDatesDTO(BaseModel):
    """Subdocumento de datas do benefício (Firestore)."""

    created_at: datetime
    updated_at: datetime
    valid_from: datetime
    valid_until: datetime  # Corresponde a 'valid_to' no modelo de domínio


# DTO para API
class BenefitCreationDTO(BaseModel):
    """DTO para a criação de um novo benefício via API."""

    partner_id: str
    tenant_id: str
    title: str
    description: str
    value: int
    value_type: BenefitValueType = BenefitValueType.PERCENTAGE
    type: BenefitType = BenefitType.DISCOUNT
    valid_from: datetime
    valid_to: datetime
    active: bool = True
    audience: list[BenefitAudience] = Field(
        default_factory=lambda: [BenefitAudience.STUDENT, BenefitAudience.EMPLOYEE]
    )
    tags: list[str] = Field(default_factory=list)

    @field_validator("partner_id")
    def validate_partner_id_format(cls, v: str) -> str:  # noqa: N805
        """Valida o formato do partner_id: PTN_XXXXXXX_XXX."""

        if not IDGenerators.validate_id_format(v, "partner"):
            raise ValueError("partner_id deve seguir o formato PTN_XXXXXXX_XXX")
        return v

    @field_validator("value")
    def validate_value_range(cls, v: int) -> int:  # noqa: N805
        """Garante que o valor do benefício esteja entre 5 e 100 (inclusivo)."""
        if v < 5 or v > 100:
            raise ValueError("value deve estar entre 5 e 100")
        return v

    @model_validator(mode="after")
    def validate_dates(self) -> "BenefitCreationDTO":
        """Valida se a data de término é posterior à data de início."""
        if self.valid_from and self.valid_to and self.valid_to <= self.valid_from:
            raise ValueError("Data de término deve ser posterior à data de início")
        return self


# Modelos de Resposta da API
class BenefitResponse(BaseModel):
    """Modelo para respostas da API contendo dados de um benefício."""

    msg: str = "ok"
    data: BenefitModel


class BenefitListResponse(BaseModel):
    """Modelo para respostas da API contendo listas de benefícios."""

    msg: str = "ok"
    data: list[BenefitModel]


class BenefitFirestoreDTO(BaseModel):
    """DTO do Benefício para leitura/escrita no Firestore."""

    partner_id: str = Field(..., description="ID do parceiro associado ao benefício")
    tenant_id: str = Field(..., description="ID do tenant associado ao benefício")
    title: str = Field(..., min_length=1, description="Título do benefício")
    description: str = Field(..., min_length=1, description="Descrição do benefício")
    configuration: BenefitConfigurationDTO = Field(
        ..., description="Configuração do benefício"
    )
    tags: list[str] = Field(default_factory=list, description="Tags do benefício")
    valid_from: datetime
    valid_until: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    status: BenefitStatus = Field(default=BenefitStatus.ACTIVE)
    type: BenefitType = Field(default=BenefitType.DISCOUNT)
    audience: list[BenefitAudience] = Field(
        default_factory=lambda: [BenefitAudience.STUDENT, BenefitAudience.EMPLOYEE]
    )

    @model_validator(mode="after")
    def validate_dates(self) -> "BenefitFirestoreDTO":
        """Valida se a data de término é posterior à data de início."""
        if self.valid_from and self.valid_until and self.valid_until <= self.valid_from:
            raise ValueError("Data de término deve ser posterior à data de início")
        return self

    def to_benefit(self, id: str) -> "BenefitModel":
        """
        Converte o DTO do Firestore para o modelo de domínio Benefit.

        Args:
            id: O ID do documento no Firestore.
            tenant_id: O ID do tenant associado ao benefício.

        Returns:
            Uma instância do modelo Benefit.
        """
        return BenefitModel(
            id=id,
            tenant_id=self.tenant_id,
            partner_id=self.partner_id,
            title=self.title,
            description=self.description,
            value=self.configuration.value,
            value_type=self.configuration.value_type,
            tags=self.tags,
            type=self.type,
            valid_from=self.valid_from,
            valid_to=self.valid_until,
            active=self.status == BenefitStatus.ACTIVE,
            audience=self.audience,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )
