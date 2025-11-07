"""Data models for Employee entity."""

from datetime import date, datetime
from typing import Self

from pydantic import BaseModel, EmailStr, Field


class EmployeeContactDTO(BaseModel):
    """Data Transfer Object for employee contact information."""

    email: EmailStr | None = None
    phone: str | None = None


class EmployeeFirestoreDTO(BaseModel):
    """
    Este Objeto de Transferência de Dados é utilizado para mapear os dados de funcionários armazenados no Firestore
    para o formato utilizado pela API.

    Attributes:
        created_at: Timestamp de criação do funcionário
        updated_at: Timestamp de última atualização do funcionário
        tenant_id: ID do tenant (empresa) ao qual o funcionário pertence
        email: Endereço de e-mail do funcionário
        phone: Número de telefone do funcionário
        active: Indica se o funcionário está ativo ou não
        role: Função ou cargo do funcionário
        name: Nome do funcionário
        zip: Código postal do funcionário
    """

    created_at: datetime
    updated_at: datetime
    tenant_id: str
    email: str
    phone: str | None = None
    active: bool = True
    role: str
    name: str
    zip: str | None = None

    def to_model(self, emp_id: str) -> "EmployeeModel":
        """Converts DTO to an EmployeeModel instance."""
        return EmployeeModel(
            id=emp_id,
            tenant_id=self.tenant_id,
            name=self.name,
            contact=EmployeeContactDTO(email=self.email, phone=self.phone),
            zip=self.zip,
            role=self.role,
            active=self.active,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    @classmethod
    def from_update(cls, update_data: "EmployeeUpdateDTO", updated_time: str) -> dict:
        """
        Cria um dicionário de atualização a partir de EmployeeUpdateDTO.

        Args:
            update_data: Dados de atualização do funcionário
            updated_at: Timestamp de atualização

        Returns:
            Dicionário com os campos a serem atualizados no Firestore
        """
        dto = EmployeeFirestoreDTO(
            tenant_id=update_data.tenant_id,
            name=update_data.name,
            email=update_data.email,
            phone=update_data.phone,
            zip=update_data.zip,
            role=update_data.role,
            active=update_data.active,
            updated_at=updated_time,
        )
        return dto.model_dump(exclude_none=True)

    @classmethod
    def from_create(cls, create_data: "EmployeeCreateDTO", tenant: str) -> Self:
        """
        Cria um dicionário a partir de EmployeeCreateDTO.

        Args:
            create_data: Dados de criação do funcionário

        Returns:
            Dicionário com os campos a serem criados no Firestore
        """
        now = datetime.now()
        dto = EmployeeFirestoreDTO(
            tenant_id=tenant,
            name=create_data.name,
            email=create_data.email,
            phone=create_data.phone,
            zip=create_data.zip,
            role=create_data.role,
            active=create_data.active,
            created_at=now,
            updated_at=now,
        )
        return dto


class EmployeeModel(BaseModel):
    """
    Este modelo é utilizado para representar os dados de um funcionário na aplicação.

    Attributes:
        id: ID único do funcionário
        tenant_id: ID do tenant (empresa) ao qual o funcionário pertence
        name: Nome do funcionário
        contact: Contato do funcionário (e-mail e telefone)
        zip: Código postal do funcionário
        role: Função ou cargo do funcionário
        active: Indica se o funcionário está ativo ou não
        created_at: Timestamp de criação do funcionário
        updated_at: Timestamp de última atualização do funcionário
        benefits: Lista de benefícios associados ao funcionário
        last_updated: Data da última atualização do funcionário
    """

    id: str
    tenant_id: str
    name: str
    contact: EmployeeContactDTO | None = None
    zip: str | None = None
    role: str
    active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None
    benefits: list[str] | None = Field(
        None, description="Lista de benefícios associados ao funcionário."
    )
    last_updated: datetime | None = Field(
        None, description="Data da última atualização do funcionário."
    )


class EmployeeUpdateDTO(BaseModel):
    """Data Transfer Object for updating an employee."""

    name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    zip: str | None = None
    street: str | None = None
    number: str | None = None
    complement: str | None = None
    city: str | None = None
    state: str | None = None
    role: str | None = None
    active: bool | None = None
    admission_date: date | None = None


class EmployeeCreateDTO(BaseModel):
    """Data Transfer Object for creating an employee."""

    name: str
    email: EmailStr
    phone: str | None = None
    zip: str | None = None
    role: str
    active: bool = True
