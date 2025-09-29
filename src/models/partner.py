"""
Modelos Pydantic para Parceiros do sistema KNN Benefits.

Este módulo define os modelos de dados para parceiros, incluindo:
- Partner: Modelo principal do parceiro
- PartnerAddress: Endereço do parceiro
- PartnerSocialNetworks: Redes sociais do parceiro
- PartnerGeolocation: Links de geolocalização
- PartnerContact: Informações de contato
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class PartnerCategory(str, Enum):
    """Categorias disponíveis para parceiros."""

    AUTOMOTIVO = "Automotivo"
    EDUCACAO = "Educação"
    TECNOLOGIA = "Tecnologia"
    ALIMENTACAO = "Alimentação"
    ENTRETENIMENTO = "Entretenimento"
    VAREJO = "Varejo"
    SERVICOS = "Serviços"
    PAPELARIA = "Papelaria"
    ESPORTE = "Esporte"
    SAUDE_BEM_ESTAR = "Saúde e Bem-estar"
    TURISMO_VIAGEM = "Turismo e Viagem"
    MODA = "Moda"
    OUTROS = "Outros"


class PartnerAddress(BaseModel):
    """Modelo para endereço do parceiro."""

    zip: str | None = Field(None, description="CEP no formato XXXXX-XXX")
    street: str | None = Field(
        None, max_length=255, description="Nome da rua/logradouro"
    )
    neighborhood: str | None = Field(None, max_length=100, description="Nome do bairro")
    city: str | None = Field(None, max_length=100, description="Nome da cidade")
    state: str | None = Field(None, description="Sigla do estado (UF)")

    @field_validator("zip")
    @classmethod
    def validate_zip(cls, v):
        """Valida formato do CEP."""
        import re
        if v and not re.match(r"^\d{5}-\d{3}$", v):
            raise ValueError("CEP deve estar no formato XXXXX-XXX")
        return v

    @field_validator("state")
    @classmethod
    def validate_state(cls, v):
        """Valida sigla do estado."""
        if v and (len(v) != 2 or not v.isupper()):
            raise ValueError("Estado deve ser uma sigla de 2 letras maiúsculas")
        return v


class PartnerSocialNetworks(BaseModel):
    """Modelo para redes sociais do parceiro."""

    instagram: str | None = Field(None, description="URL ou handle do Instagram")
    facebook: str | None = Field(None, description="URL da página do Facebook")
    website: str | None = Field(None, description="URL do site oficial")


class PartnerGeolocation(BaseModel):
    """Modelo para links de geolocalização."""

    google: str | None = Field(None, description="URL do Google Maps")
    waze: str | None = Field(None, description="URL do Waze")


class PartnerContact(BaseModel):
    """Modelo para informações de contato do parceiro."""

    phone: str | None = Field(None, description="Número de telefone")
    whatsapp: str | None = Field(None, description="Número do WhatsApp")
    email: str | None = Field(None, description="Endereço de email")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v):
        """Valida formato do email."""
        if v and "@" not in v:
            raise ValueError("Email deve ter formato válido")
        return v


class Partner(BaseModel):
    """
    Modelo principal do Parceiro.

    Representa um parceiro do sistema KNN Benefits com todas as suas
    informações de contato, endereço, categoria e configurações.
    """

    id: str = Field(..., description="ID único do parceiro no formato PTN_XXXXXXX_XXX")
    trade_name: str = Field(
        ..., min_length=1, max_length=50, description="Nome comercial do parceiro"
    )
    tenant_id: str = Field(
        ..., min_length=1, max_length=30, description="ID do tenant do parceiro"
    )
    benefits_count: int | None = Field(
        0, ge=0, description="Número total de benefícios oferecidos"
    )
    has_active_benefits: bool = Field(
        False, description="Indica se o parceiro possui benefícios ativos"
    )
    cnpj: str = Field(..., description="CNPJ do parceiro no formato XX.XXX.XXX/XXXX-XX")
    logo_url: str | None = Field(
        None, description="URL do logo do parceiro no Firebase Storage"
    )
    address: PartnerAddress = Field(..., description="Endereço do parceiro")
    social_networks: PartnerSocialNetworks = Field(
        ..., description="Redes sociais do parceiro"
    )
    geolocation: PartnerGeolocation = Field(..., description="Links de geolocalização")
    category: PartnerCategory = Field(..., description="Categoria do parceiro")
    contact: PartnerContact = Field(
        ..., description="Informações de contato do parceiro"
    )
    active: bool = Field(True, description="Status ativo/inativo do parceiro")
    created_at: datetime | None = Field(None, description="Data de criação")
    updated_at: datetime | None = Field(None, description="Data de última atualização")

    @field_validator("id")
    @classmethod
    def validate_partner_id(cls, v):
        """Valida formato do ID do parceiro."""
        import re

        if not re.match(r"^PTN_[A-Z0-9]{7}_[A-Z]{3}$", v):
            raise ValueError("ID do parceiro deve seguir o formato PTN_XXXXXXX_XXX")
        return v

    @field_validator("cnpj")
    @classmethod
    def validate_cnpj(cls, v):
        """Valida formato do CNPJ."""
        import re

        if not re.match(r"^\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}$", v):
            raise ValueError("CNPJ deve estar no formato XX.XXX.XXX/XXXX-XX")
        return v

    class Config:
        """Configuração do modelo."""

        json_encoders = {datetime: lambda v: v.isoformat() if v else None}
        schema_extra = {
            "example": {
                "id": "PTN_A1E8958_AUT",
                "trade_name": "Autoescola Escórcio",
                "tenant_id": "knn-dev-tenant",
                "benefits_count": 1,
                "has_active_benefits": True,
                "cnpj": "13.018.958/0001-51",
                "logo_url": "https://firebasestorage.googleapis.com/v0/b/knn-benefits.firebasestorage.app/o/partners%2Flogos%2FPTN_A1E8958_AUT.png",
                "address": {
                    "zip": "65040-003",
                    "street": "Rua das Flores, 123",
                    "neighborhood": "Outeiro da Cruz",
                    "city": "São Luís",
                    "state": "MA",
                },
                "social_networks": {
                    "instagram": "@autoescola_escorcio",
                    "facebook": "https://facebook.com/autoescola.escorcio",
                    "website": "https://www.autoescolaescorcio.com.br",
                },
                "geolocation": {
                    "google": "https://maps.google.com/?q=Autoescola+Escorcio",
                    "waze": "https://waze.com/ul/hsv8vtgq2k",
                },
                "category": "Automotivo",
                "contact": {
                    "phone": "98848-4642",
                    "whatsapp": "(98) 98848-4642",
                    "email": "contato@autoescolaescorcio.com.br",
                },
                "active": True,
            }
        }
