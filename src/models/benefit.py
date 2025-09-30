"""
Modelos Pydantic para Benefícios do sistema KNN Benefits.

Este módulo define os modelos de dados para benefícios, incluindo:
- Benefit: Modelo principal do benefício
- BenefitRequest: Modelo para requisições de criação/atualização
- BenefitResponse: Modelo para respostas da API

Os benefícios são oferecidos pelos parceiros,
com validações específicas para garantir a integridade dos dados.
"""

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


def generate_benefit_id() -> str:
    """
    Gera um ID temporário para benefício.

    O ID real deve ser gerado quando o benefício for criado,
    usando informações do parceiro e contador sequencial.
    Este é apenas um placeholder que será substituído.

    Returns:
        ID temporário no formato BNF_TEMP_XX_DC
    """
    return "BNF_TEMP_00_DC"


def _ensure_datetime(value: Any) -> datetime:
    """Converte vários formatos (str ISO, datetime, DatetimeWithNanoseconds) para datetime com timezone UTC."""
    if value is None:
        return datetime.now(UTC)
    if isinstance(value, datetime):
        # se for datetime sem tz, assume UTC
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value
    # Tratar DatetimeWithNanoseconds do Firestore
    if hasattr(value, "timestamp"):
        return datetime.fromtimestamp(value.timestamp(), tz=UTC)
    if isinstance(value, str):
        try:
            # tenta parse ISO
            dt = datetime.fromisoformat(value)
            if dt.tzinfo is None:
                return dt.replace(tzinfo=UTC)
            return dt
        except Exception:
            # fallback para agora se não conseguir parse
            return datetime.now(UTC)
    # fallback
    return datetime.now(UTC)


class Benefit(BaseModel):
    """
    Modelo principal do Benefício.
    """

    id: str = Field(default_factory=generate_benefit_id)
    tenant_id: str
    partner_id: str
    title: str
    value: int
    value_type: str = Field(default="percentage", description="percentage | fixed")
    tags: list[str] = Field(default_factory=list)
    type: str
    valid_from: datetime
    valid_to: datetime
    active: bool = True
    audience: list[str] = Field(
        default_factory=lambda: ["student", "employee"],
        description="Público-alvo: lista com 'student' e/ou 'employee'",
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("audience")
    @classmethod
    def validate_audience(cls, v):
        """Valida o público-alvo da promoção."""
        if not isinstance(v, list) or not v:
            raise ValueError("audience deve ser uma lista não vazia")

        valid_values = {"student", "employee"}
        seen = set()
        unique_audience = []
        for item in v:
            if item not in valid_values:
                raise ValueError(
                    'audience deve conter apenas "student" e/ou "employee"'
                )
            if item not in seen:
                seen.add(item)
                unique_audience.append(item)
        return unique_audience

    @field_validator("type")
    @classmethod
    def validate_type(cls, v):
        valid_types = ["discount", "cashback", "freebie", "upgrade"]
        if v not in valid_types:
            raise ValueError(f"Type deve ser um dos valores: {valid_types}")
        return v

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
            ) and v <= info.data.get("valid_from"):
                raise ValueError("Data de término deve ser posterior à data de início")
        except (TypeError, AttributeError):
            # Se info.data não for iterável ou não tiver get, pular a validação
            pass
        return v

    class Config:
        orm_mode = True


class BenefitDTO(BaseModel):
    """
    Modelo de conversão para gravar e ler os dados ao salvar no Firestore.
    """

    key: str
    benefit_data: dict[str, Any]
    partner_id: str

    def to_benefit(self) -> Benefit:
        """
        Converte o DTO em um modelo Benefit.
        """
        if not self.key.startswith("BNF_") or not isinstance(self.benefit_data, dict):
            raise ValueError("Chave inválida ou benefit_data não é dict")

        # Extrair campos do Firestore com defaults
        system = self.benefit_data.get("system", {}) or {}
        configuration = self.benefit_data.get("configuration", {}) or {}
        dates = self.benefit_data.get("dates", {}) or {}
        metadata = self.benefit_data.get("metadata", {}) or {}

        firestore_audience = system.get("audience", "students")
        valid_until = dates.get("valid_until")
        # REMOVA a vírgula — antes gerava uma tupla!
        benefit_status = system.get("status", "active")

        the_benefit = Benefit(
            id=self.key,
            title=self.benefit_data.get("title", "") or "",
            tenant_id=system.get("tenant_id", "not found"),
            partner_id=self.partner_id,
            type=self.convert_type(
                system.get("type", "discount")
            ),  # Usar convert_type para mapear valores
            audience=self.convert_audience(firestore_audience),
            active=self.convert_status(benefit_status),
            value=configuration.get("value", 0),
            value_type=configuration.get("value_type", "percentage"),
            created_at=_ensure_datetime(dates.get("created_at")),
            updated_at=_ensure_datetime(dates.get("updated_at")),
            valid_from=_ensure_datetime(dates.get("valid_from")),
            valid_to=self.handle_valid_to(valid_until),
            tags=metadata.get("tags", []) or [],
        )
        return the_benefit

    @staticmethod
    def convert_type(firestore_type: str) -> str:
        """Converte tipo do formato Firestore para o formato da API."""
        type_mapping = {
            "percentage": "discount",
            "fixed": "discount",
            "discount": "discount",
            "cashback": "cashback",
            "freebie": "freebie",
            "upgrade": "upgrade",
        }
        return type_mapping.get(firestore_type, "discount")

    @staticmethod
    def convert_status(benefit_status: str) -> bool:
        """Converte status do formato Firestore para o formato da API."""
        return benefit_status == "active"

    @staticmethod
    def convert_audience(firestore_audience) -> list[str]:
        """Converte audience do formato Firestore para o formato da API (singular)."""
        # Se já é uma lista, retorna diretamente
        if isinstance(firestore_audience, list):
            return firestore_audience

        # Se é uma string, usa o mapeamento
        mapping = {
            "students": ["student"],
            "employees": ["employee"],
            "all": ["student", "employee"],
        }
        return mapping.get(firestore_audience, ["student"])

    @staticmethod
    def handle_valid_to(valid_until):
        """Trata o campo valid_to quando é None no Firestore."""
        if valid_until is None:
            # Usar uma data padrão distante no futuro para benefícios sem data de expiração
            # Usando timezone UTC para compatibilidade
            return datetime(2099, 12, 31, 23, 59, 59, tzinfo=UTC)
        return _ensure_datetime(valid_until)

    @classmethod
    def from_benefit(cls, benefit: Benefit) -> dict:
        """
        Converte um modelo Benefit em um DTO compatível com o Firestore.

        Args:
            benefit: Objeto Benefit a ser convertido

        Returns:
            BenefitDTO com estrutura compatível com o Firestore
        """
        # Converter audience de volta para o formato Firestore
        audience_mapping = {
            frozenset(["student"]): "students",
            frozenset(["employee"]): "employees",
            frozenset(["student", "employee"]): "all",
        }
        firestore_audience = audience_mapping.get(
            frozenset(benefit.audience), "students"
        )

        # Converter status de volta para string
        firestore_status = "active" if benefit.active else "inactive"

        # Estrutura de dados compatível com o Firestore
        benefit_data = {
            "title": benefit.title,
            "description": f"Benefício {benefit.type} - {benefit.title}",
            "system": {
                "tenant_id": benefit.tenant_id,
                "type": benefit.type,
                "status": firestore_status,
                "audience": firestore_audience,
                "category": "Parceiro",
            },
            "configuration": {
                "value": benefit.value,
                "value_type": benefit.value_type,
                "calculation_method": "final_amount",
                "description": f"Benefício {benefit.type} - {benefit.title}",
                "terms_conditions": "Válido mediante apresentação de comprovante de vínculo com KNN",
                "requirements": ["comprovante_vinculo_knn"],
                "applicable_services": [],
                "excluded_services": [],
                "additional_benefits": [],
            },
            "metadata": {
                "tags": benefit.tags if benefit.tags else [benefit.type, "parceiro"]
            },
            "dates": {
                "created_at": benefit.created_at.isoformat()
                if benefit.created_at
                else None,
                "updated_at": benefit.updated_at.isoformat()
                if benefit.updated_at
                else None,
                "valid_from": benefit.valid_from.isoformat()
                if benefit.valid_from
                else None,
                "valid_until": benefit.valid_to.isoformat()
                if benefit.valid_to
                else None,
            },
        }

        return cls(
            key=benefit.id, benefit_data=benefit_data, partner_id=benefit.partner_id
        )


class BenefitRequest(BaseModel):
    """
    Modelo para requisições de criação/atualização de benefícios.

    Usado nos endpoints da API para receber dados de benefícios
    dos parceiros com validações apropriadas.
    """

    title: str
    type: str
    valid_from: datetime
    valid_to: datetime
    active: bool = True
    audience: list[str] = Field(
        default=["all", "employee", "student"],
        description="Público-alvo: lista com 'student' e/ou 'employee'",
    )

    @field_validator("audience")
    @classmethod
    def validate_audience(cls, v):
        """Valida o público-alvo da promoção."""
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


class BenefitResponse(BaseModel):
    """
    Modelo para respostas da API contendo dados de benefícios.

    Usado para retornar dados de benefícios nos endpoints da API
    com formatação apropriada para o frontend.
    """

    msg: str = "ok"
    data: Benefit


class BenefitListResponse(BaseModel):
    """
    Modelo para respostas da API contendo listas de benefícios.

    Usado para retornar listas de benefícios nos endpoints da API
    com formatação apropriada para o frontend.
    """

    msg: str = "ok"
    data: list[Benefit]
