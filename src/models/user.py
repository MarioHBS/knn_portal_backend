"""
Modelos de dados para usuários.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class UserModel(BaseModel):
    """
    Representa um usuário no sistema, armazenado na coleção 'users' do Firestore.
    """

    email: str = Field(..., description="Endereço de e-mail do usuário.")
    entity_id: str = Field(
        ..., description="ID da entidade associada (ex: funcionário, aluno)."
    )
    first_access: bool = Field(
        True, description="Indica se é o primeiro acesso do usuário."
    )
    name: str = Field(..., description="Nome completo do usuário.")
    role: str = Field(
        ..., description="Papel do usuário (ex: employee, student, admin)."
    )
    tenant_id: str = Field(..., description="ID do tenant ao qual o usuário pertence.")
    updated_at: datetime = Field(
        ..., description="Timestamp da última atualização do registro do usuário."
    )
