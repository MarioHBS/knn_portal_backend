"""
Módulo de modelos Pydantic para códigos de validação.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, model_validator, validator

from src.utils.business_rules import BusinessRules


class ValidationCode(BaseModel):
    """
    Representa um código de validação no sistema.
    """

    student_id: str | None = Field(
        None, description="ID do estudante que gerou o código."
    )
    employee_id: str | None = Field(
        None, description="ID do funcionário que gerou o código."
    )
    partner_id: str = Field(
        ..., description="ID do parceiro para o qual o código é válido."
    )

    expires: datetime = Field(..., description="Data e hora de expiração do código.")
    used_at: datetime | None = Field(
        None, description="Data e hora em que o código foi utilizado."
    )
    tenant_id: str = Field(..., description="ID do tenant ao qual o código pertence.")
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Data e hora de criação do código."
    )

    @model_validator(mode='after')
    def check_user_id_exclusive(self) -> 'ValidationCode':
        """
        Garante que ou 'student_id' ou 'employee_id' seja fornecido, mas não ambos.
        """
        if self.student_id and self.employee_id:
            raise ValueError(
                "Apenas 'student_id' ou 'employee_id' deve ser fornecido, não ambos."
            )
        if not self.student_id and not self.employee_id:
            raise ValueError(
                "Um entre 'student_id' ou 'employee_id' deve ser fornecido."
            )
        return self

    class Config:
        """
        Configurações do modelo Pydantic.
        """

        from_attributes = True
        json_encoders = {UUID: str, datetime: lambda dt: dt.isoformat()}


class ValidationCodeCreationRequest(BaseModel):
    """
    DTO for creating a validation code.
    """
    partner_id: str = Field(..., description="ID of the partner for which the code is being generated.")


class ValidationCodeRedeemRequest(BaseModel):
    """
    DTO para a requisição de resgate de um código de validação.
    """

    code: str = Field(..., description="Código de validação de 6 dígitos.")
    cnpj: str = Field(..., description="CNPJ do parceiro que está resgatando o código.")

    @validator("cnpj")
    @classmethod
    def validate_cnpj(cls, v):
        """
        Valida o formato do CNPJ.
        """
        if not BusinessRules.validate_cnpj(v):
            raise ValueError("Formato de CNPJ inválido.")
        return v
