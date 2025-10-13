"""Data models for Employee entity."""

from datetime import date, datetime
from typing import Self

from pydantic import BaseModel, EmailStr, field_validator


class EmployeeContactDTO(BaseModel):
    """Data Transfer Object for employee contact information."""

    email: EmailStr | None = None
    phone: str | None = None


class EmployeeDTO(BaseModel):
    """
    Data Transfer Object for reading/writing Employee data in Firestore.
    This structure mirrors the documents exported in
    data/firestore_export/firestore_employees.json.
    """

    created_at: datetime | None = None
    updated_at: datetime | None = None
    tenant_id: str
    email: str
    phone: str
    active: bool = True
    role: str
    name: str
    zip: str | None = None

    def to_employee(self, emp_id: str) -> "EmployeeModel":
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


class EmployeeModel(BaseModel):
    """API data model for an Employee."""

    id: str
    tenant_id: str
    name: str
    contact: EmployeeContactDTO
    zip: str | None = None
    role: str
    active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @field_validator("id", "tenant_id", "name", "role")
    def field_not_empty(cls, v: str) -> str:  # noqa: N805
        """Ensures that specified string fields are not empty."""
        if not v or not v.strip():
            raise ValueError("Field cannot be empty")
        return v

    @classmethod
    def from_dto(cls, dto: EmployeeDTO) -> Self:
        """Creates an EmployeeModel instance from an EmployeeDTO."""
        return cls(
            id=dto.id,
            tenant_id=dto.tenant_id,
            name=dto.name,
            contact=EmployeeContactDTO(email=dto.email, phone=dto.phone),
            role=dto.role,
            active=dto.active,
            created_at=dto.created_at,
            updated_at=dto.updated_at,
        )

    def to_dto(self) -> "EmployeeDTO":
        """Converts EmployeeModel to an EmployeeDTO instance."""
        return EmployeeDTO(
            id=self.id,
            tenant_id=self.tenant_id,
            name=self.name,
            email=self.contact.email,
            phone=self.contact.phone,
            zip=self.zip,
            role=self.role,
            active=self.active,
            created_at=self.created_at,
            updated_at=self.updated_at,
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
