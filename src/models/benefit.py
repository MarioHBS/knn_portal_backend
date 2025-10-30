"""
Modelos Pydantic para Benefícios do sistema KNN Benefits.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator, model_validator
from pytz import UTC


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


class BenefitMetadataDTO(BaseModel):
    """Subdocumento de metadados do benefício (Firestore)."""

    tags: list[str] = Field(default_factory=list)


# DTO para API
class BenefitCreateDTO(BaseModel):
    """
    DTO para a criação de um novo benefício via API.
    Os campos são todos opcionais para permitir a atualização parcial do benefício.
    """

    title: str | None = None
    description: str | None = None
    value: int | None = None
    value_type: BenefitValueType | None = None
    type: BenefitType | None = None
    valid_from: datetime | None = None
    valid_to: datetime | None = None
    active: bool | None = None
    audience: list[BenefitAudience] | None = None
    tags: list[str] | None = None

    @field_validator("value")
    def validate_value_range(cls, v: int) -> int:  # noqa: N805
        """Garante que o valor do benefício esteja entre 5 e 100 (inclusivo)."""
        if v < 5 or v > 100:
            raise ValueError("value deve estar entre 5 e 100")
        return v

    @model_validator(mode="after")
    def validate_dates(self) -> "BenefitCreateDTO":
        """Valida se a data de término é posterior à data de início."""
        if self.valid_from and self.valid_to and self.valid_to <= self.valid_from:
            raise ValueError("Data de término deve ser posterior à data de início")
        return self

    def prepare_to_update(self, updated_at: datetime) -> dict:
        update_data = {}
        if self.title is not None:
            update_data["title"] = self.title
        if self.description is not None:
            update_data["description"] = self.description
        if self.value is not None:
            update_data["configuration.value"] = self.value
        if self.value_type is not None:
            update_data["configuration.value_type"] = self.value_type
        if self.type is not None:
            update_data["type"] = self.type
        if self.valid_from is not None:
            update_data["valid_from"] = self.valid_from
        if self.valid_to is not None:
            update_data["valid_until"] = self.valid_to
        if self.active is not None:
            update_data["status"] = "active" if self.active else "inactive"
        if self.audience is not None:
            update_data["audience"] = self.audience
        if self.tags is not None:
            update_data["tags"] = self.tags
        update_data["updated_at"] = updated_at
        return update_data


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

    @classmethod
    def from_create(
        cls, create_data: "BenefitCreateDTO", partner: str, tenant: str
    ) -> "BenefitFirestoreDTO":
        """
        Cria um BenefitFirestoreDTO a partir de BenefitCreateDTO.

        Args:
            create_data: DTO com os dados de criação do benefício.
            tenant: O ID do tenant associado ao benefício.

        Returns:
            Uma instância de BenefitFirestoreDTO.
        """
        now = datetime.now(UTC)
        return cls(
            created_at=now,
            updated_at=now,
            partner_id=partner,
            tenant_id=tenant,
            title=create_data.title,
            description=create_data.description,
            configuration=BenefitConfigurationDTO(
                value=create_data.value,
                value_type=create_data.value_type,
            ),
            tags=create_data.tags,
            valid_from=create_data.valid_from,
            valid_until=create_data.valid_to,
            type=create_data.type,
            audience=create_data.audience,
        )


class BenefitSystemDTO(BaseModel):
    """Subdocumento de sistema do benefício (Firestore)."""

    tenant_id: str
    type: BenefitType
    status: BenefitStatus
    audience: str  # No Firestore: 'students', 'employees', 'all'
    category: str = "Parceiro"
