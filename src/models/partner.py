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
from typing import Any, Self

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


class PartnerModel(BaseModel):
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
    address: PartnerAddress | None = Field(None, description="Endereço do parceiro")
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


class PartnerCreateDTO(BaseModel):
    """
    Data Transfer Object para criação de um novo parceiro.

    Este DTO é utilizado para validar e transformar dados de entrada ao
    criar um novo parceiro no sistema.
    """

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
    add_zip: str = Field(..., description="CEP do parceiro no formato XXXXX-XXX")
    add_street: str = Field(..., description="Rua do parceiro")
    add_number: str = Field(..., description="Número do endereço")
    add_complement: str | None = Field(None, description="Complemento do endereço")
    add_neighborhood: str = Field(..., description="Bairro do endereço")
    add_city: str = Field(..., description="Cidade do endereço")
    add_state: str = Field(..., description="Estado do endereço")
    social_networks: PartnerSocialNetworks = Field(
        ..., description="Redes sociais do parceiro"
    )
    geolocation: PartnerGeolocation = Field(..., description="Links de geolocalização")
    category: PartnerCategory = Field(..., description="Categoria do parceiro")
    phone: str = Field(..., description="Número de telefone do parceiro")
    whatsapp: str = Field(..., description="Número de WhatsApp do parceiro")
    email: str = Field(..., description="Email do parceiro")
    active: bool = Field(True, description="Status ativo/inativo do parceiro")

    @field_validator("cnpj")
    @classmethod
    def validate_cnpj(cls, v):
        """Valida formato do CNPJ."""
        import re

        if not re.match(r"^\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}$", v):
            raise ValueError("CNPJ deve estar no formato XX.XXX.XXX/XXXX-XX")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "trade_name": "Nome Fantasia do Parceiro",
                "tenant_id": "tenant_exemplo",
                "benefits_count": 0,
                "has_active_benefits": True,
                "cnpj": "11.222.333/0001-44",
                "logo_url": "https://example.com/logo.png",
                "address": {
                    "street": "Rua Exemplo",
                    "number": "123",
                    "complement": "Apto 101",
                    "neighborhood": "Bairro Exemplo",
                    "city": "Cidade Exemplo",
                    "state": "UF",
                    "zip_code": "12345-678",
                },
                "social_networks": {
                    "instagram": "https://instagram.com/parceiro",
                    "facebook": "https://facebook.com/parceiro",
                    "website": "https://parceiro.com.br",
                },
                "geolocation": {
                    "latitude": -23.55052,
                    "longitude": -46.633307,
                    "plus_code": "ABCD+EFG",
                },
                "category": "TECNOLOGIA",
                "contact": {
                    "email": "contato@parceiro.com.br",
                    "phone": "+5511987654321",
                    "responsible_name": "Nome do Responsável",
                },
                "active": True,
            }
        }


class PartnerUpdateDTO(BaseModel):
    """
    Data Transfer Object para atualização de um parceiro existente.

    Todos os campos são opcionais, permitindo atualizações parciais.
    """

    trade_name: str | None = Field(
        None, min_length=1, max_length=50, description="Nome comercial do parceiro"
    )
    tenant_id: str | None = Field(
        None, min_length=1, max_length=30, description="ID do tenant do parceiro"
    )
    benefits_count: int | None = Field(
        None, ge=0, description="Número total de benefícios oferecidos"
    )
    has_active_benefits: bool | None = Field(
        None, description="Indica se o parceiro possui benefícios ativos"
    )
    cnpj: str | None = Field(
        None, description="CNPJ do parceiro no formato XX.XXX.XXX/XXXX-XX"
    )
    logo_url: str | None = Field(
        None, description="URL do logo do parceiro no Firebase Storage"
    )
    address: PartnerAddress | None = Field(None, description="Endereço do parceiro")
    social_networks: PartnerSocialNetworks | None = Field(
        None, description="Redes sociais do parceiro"
    )
    geolocation: PartnerGeolocation | None = Field(
        None, description="Links de geolocalização"
    )
    category: PartnerCategory | None = Field(None, description="Categoria do parceiro")
    contact: PartnerContact | None = Field(
        None, description="Informações de contato do parceiro"
    )
    active: bool | None = Field(None, description="Status ativo/inativo do parceiro")

    @field_validator("cnpj")
    @classmethod
    def validate_cnpj(cls, v):
        """Valida formato do CNPJ."""
        import re

        if v is not None and not re.match(r"^\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}$", v):
            raise ValueError("CNPJ deve estar no formato XX.XXX.XXX/XXXX-XX")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "trade_name": "Nome Fantasia Atualizado",
                "cnpj": "99.888.777/0001-66",
                "active": False,
            }
        }


class PartnerFirestoreDTO(BaseModel):
    """
    Data Transfer Object para conversão de dados entre Firestore e modelo Partner.

    Responsável por padronizar a conversão de dados, lidar com campos opcionais
    e facilitar futuras migrações de dados.
    """

    active: bool = True
    trade_name: str = Field(
        ..., min_length=1, max_length=50, description="Nome comercial do parceiro"
    )
    tenant_id: str = Field(
        ..., min_length=1, max_length=20, description="ID do tenant do parceiro"
    )
    benefits_count: int | None = Field(
        0, ge=0, description="Número total de benefícios oferecidos"
    )
    has_active_benefits: bool = Field(
        False, description="Indica se o parceiro possui benefícios ativos"
    )
    cnpj: str
    logo_url: str | None = Field(
        None, description="URL do logo do parceiro no Firebase Storage"
    )
    category: PartnerCategory = Field(..., description="Categoria do parceiro")
    address: PartnerAddress
    contact: PartnerContact
    geolocation: PartnerGeolocation
    social_networks: PartnerSocialNetworks
    created_at: datetime | None = Field(None, description="Data de criação")
    updated_at: datetime | None = Field(None, description="Data de última atualização")

    @staticmethod
    def from_firestore(doc_data: dict[str, Any], doc_id: str = None) -> dict[str, Any]:
        """
        Converte dados do Firestore para formato compatível com modelo Partner.

        Args:
            doc_data: Dados brutos do documento Firestore
            doc_id: ID do documento (opcional, pode estar em doc_data['id'])

        Returns:
            dict: Dados formatados para criação do modelo Partner

        Raises:
            ValueError: Se campos obrigatórios estiverem ausentes
        """
        # Campos obrigatórios com mapeamento (exceto id que vem separado)
        required_mappings = {
            "trade_name": "trade_name",
            "tenant_id": "tenant_id",
            "cnpj": "cnpj",
            "category": "category",
            "active": "active",
        }

        # Verificar campos obrigatórios
        missing_fields = []
        for firestore_field, _model_field in required_mappings.items():
            if firestore_field not in doc_data:
                missing_fields.append(firestore_field)

        if missing_fields:
            raise ValueError(f"Campos obrigatórios ausentes: {missing_fields}")

        # Construir dados base
        partner_data = {}

        # ID pode vir do parâmetro doc_id ou do campo 'id' nos dados
        partner_data["id"] = doc_id or doc_data.get("id")
        if not partner_data["id"]:
            raise ValueError("ID do documento é obrigatório")

        # Mapear outros campos obrigatórios
        for firestore_field, model_field in required_mappings.items():
            partner_data[model_field] = doc_data[firestore_field]

        # Campos opcionais com valores padrão
        partner_data.update(
            {
                "benefits_count": doc_data.get("benefits_count", 0),
                "has_active_benefits": doc_data.get("has_active_benefits", False),
                "logo_url": doc_data.get("logo_url"),
                "created_at": doc_data.get("created_at"),
                "updated_at": doc_data.get("updated_at"),
            }
        )

        # Campos complexos com estruturas padrão
        partner_data["address"] = PartnerFirestoreDTO._extract_address(doc_data)
        partner_data["social_networks"] = PartnerFirestoreDTO._extract_social_networks(
            doc_data
        )
        partner_data["geolocation"] = PartnerFirestoreDTO._extract_geolocation(doc_data)
        partner_data["contact"] = PartnerFirestoreDTO._extract_contact(doc_data)

        return partner_data

    @staticmethod
    def _extract_address(doc_data: dict[str, Any]) -> dict[str, str | None] | None:
        """Extrai dados de endereço com valores padrão."""
        address_data = doc_data.get("address")

        # Se address for None, retorna None para permitir campo opcional
        if address_data is None:
            return None

        # Se address for um dicionário vazio ou com dados, processa normalmente
        if isinstance(address_data, dict):
            return {
                "zip": address_data.get("zip"),
                "street": address_data.get("street"),
                "neighborhood": address_data.get("neighborhood"),
                "city": address_data.get("city"),
                "state": address_data.get("state"),
            }

        # Fallback para casos inesperados
        return None

    @staticmethod
    def _extract_social_networks(doc_data: dict[str, Any]) -> dict[str, str | None]:
        """Extrai dados de redes sociais com valores padrão."""
        social_data = doc_data.get("social_networks") or {}
        return {
            "instagram": social_data.get("instagram"),
            "facebook": social_data.get("facebook"),
            "website": social_data.get("website"),
        }

    @staticmethod
    def _extract_geolocation(doc_data: dict[str, Any]) -> dict[str, str | None]:
        """Extrai dados de geolocalização com valores padrão."""
        geo_data = doc_data.get("geolocation") or {}
        # Compatibilidade com campo 'maps' antigo
        maps_data = doc_data.get("maps") or {}
        return {
            "google": geo_data.get("google") or maps_data.get("google"),
            "waze": geo_data.get("waze") or maps_data.get("waze"),
        }

    @staticmethod
    def _extract_contact(doc_data: dict[str, Any]) -> dict[str, str | None]:
        """Extrai dados de contato com valores padrão."""
        contact_data = doc_data.get("contact") or {}
        return {
            "phone": contact_data.get("phone"),
            "whatsapp": contact_data.get("whatsapp"),
            "email": contact_data.get("email"),
        }

    @staticmethod
    def to_firestore(
        partner: PartnerModel, created_at: datetime, updated_at: datetime
    ) -> Self:
        """
        Converte modelo Partner para formato Firestore.

        Args:
            partner: Instância do modelo Partner

        Returns:
            PartnerDTO: Dados formatados para armazenamento no Firestore
        """
        return PartnerFirestoreDTO(
            trade_name=partner.trade_name,
            tenant_id=partner.tenant_id,
            benefits_count=partner.benefits_count,
            has_active_benefits=partner.has_active_benefits,
            cnpj=partner.cnpj,
            logo_url=partner.logo_url,
            address=partner.address,
            social_networks=partner.social_networks,
            geolocation=partner.geolocation,
            contact=partner.contact,
            category=partner.category,
            active=partner.active,
            created_at=created_at,
            updated_at=updated_at,
        )

    @classmethod
    def from_create(cls, create_data: PartnerCreateDTO, tenant: str) -> Self:
        """
        Cria instância de PartnerFirestoreDTO a partir de PartnerCreateDTO.

        Args:
            create_data: Dados de criação do parceiro
            tenant: ID do tenant associado

        Returns:
            PartnerFirestoreDTO: Instância pronta para Firestore
        """

        now = datetime.now()
        return cls(
            created_at=now,
            updated_at=now,
            trade_name=create_data.trade_name,
            tenant_id=tenant,
            benefits_count=create_data.benefits_count,
            has_active_benefits=create_data.has_active_benefits,
            cnpj=create_data.cnpj,
            logo_url=create_data.logo_url,
            address=PartnerAddress(
                zip=create_data.add_zip,
                street=create_data.add_street,
                neighborhood=create_data.add_neighborhood,
                city=create_data.add_city,
                state=create_data.add_state,
            ),
            social_networks=create_data.social_networks,
            geolocation=create_data.geolocation,
            category=create_data.category,
            contact=PartnerContact(
                phone=create_data.phone,
                whatsapp=create_data.whatsapp,
                email=create_data.email,
            ),
            active=create_data.active,
        )

    def to_model(self, partner_id: str) -> PartnerModel:
        """
        Converte a instância atual de PartnerFirestoreDTO para PartnerModel.
        """
        return PartnerModel(
            id=partner_id,
            trade_name=self.trade_name,
            tenant_id=self.tenant_id,
            benefits_count=self.benefits_count,
            has_active_benefits=self.has_active_benefits,
            cnpj=self.cnpj,
            logo_url=self.logo_url,
            address=self.address,
            social_networks=self.social_networks,
            geolocation=self.geolocation,
            category=self.category,
            contact=self.contact,
            active=self.active,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )
