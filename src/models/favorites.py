"""
Modelos para gerenciamento de favoritos no Firestore.

Este módulo define os modelos Pydantic para as coleções de favoritos
separadas por tipo de usuário (students_fav e employees_fav).
"""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class StudentFavorites(BaseModel):
    """
    Modelo para favoritos de estudantes.

    Representa um documento na coleção 'students_fav' onde cada documento
    contém a lista de parceiros favoritados por um estudante específico.
    """

    id: str = Field(..., description="ID do estudante")
    favorites: list[str] = Field(
        default_factory=list, description="Lista de IDs dos parceiros favoritos"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Data da última atualização"
    )

    @field_validator("id")
    @classmethod
    def validate_student_id(cls, v):
        """Valida o formato do ID do estudante."""
        if not v or not v.startswith("STU"):
            raise ValueError('ID do estudante deve começar com "STU"')
        return v

    @field_validator("favorites")
    @classmethod
    def validate_favorites_list(cls, v):
        """Valida a lista de favoritos."""
        if len(v) > 1000:  # Limite prático para evitar documentos muito grandes
            raise ValueError("Máximo de 1000 favoritos permitidos por estudante")

        # Verifica se todos os IDs são de parceiros válidos
        for partner_id in v:
            if not partner_id or not partner_id.startswith("PTN"):
                raise ValueError(f"ID de parceiro inválido: {partner_id}")

        # Remove duplicatas mantendo a ordem
        seen = set()
        unique_favorites = []
        for item in v:
            if item not in seen:
                seen.add(item)
                unique_favorites.append(item)

        return unique_favorites

    class Config:
        """Configuração do modelo."""

        json_encoders = {datetime: lambda v: v.isoformat()}
        schema_extra = {
            "example": {
                "id": "STU123456",
                "favorites": ["PTN789012", "PTN345678"],
                "updated_at": "2024-01-15T10:30:00Z",
            }
        }


class EmployeeFavorites(BaseModel):
    """
    Modelo para favoritos de funcionários.

    Representa um documento na coleção 'employees_fav' onde cada documento
    contém a lista de parceiros favoritados por um funcionário específico.
    """

    id: str = Field(..., description="ID do funcionário")
    favorites: list[str] = Field(
        default_factory=list, description="Lista de IDs dos parceiros favoritos"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Data da última atualização"
    )

    @field_validator("id")
    @classmethod
    def validate_employee_id(cls, v):
        """Valida o formato do ID do funcionário."""
        if not v or not v.startswith("EMP"):
            raise ValueError('ID do funcionário deve começar com "EMP"')
        return v

    @field_validator("favorites")
    @classmethod
    def validate_favorites_list(cls, v):
        """Valida a lista de favoritos."""
        if len(v) > 1000:  # Limite prático para evitar documentos muito grandes
            raise ValueError("Máximo de 1000 favoritos permitidos por funcionário")

        # Verifica se todos os IDs são de parceiros válidos
        for partner_id in v:
            if not partner_id or not partner_id.startswith("PTN"):
                raise ValueError(f"ID de parceiro inválido: {partner_id}")

        # Remove duplicatas mantendo a ordem
        seen = set()
        unique_favorites = []
        for item in v:
            if item not in seen:
                seen.add(item)
                unique_favorites.append(item)

        return unique_favorites

    class Config:
        """Configuração do modelo."""

        json_encoders = {datetime: lambda v: v.isoformat()}
        schema_extra = {
            "example": {
                "id": "EMP789012",
                "favorites": ["PTN123456", "PTN987654"],
                "updated_at": "2024-01-15T10:30:00Z",
            }
        }


class FavoriteRequest(BaseModel):
    """
    Modelo para requisições de adição/remoção de favoritos.
    """

    partner_id: str = Field(
        ..., description="ID do parceiro a ser adicionado/removido dos favoritos"
    )

    @field_validator("partner_id")
    @classmethod
    def validate_partner_id(cls, v):
        """Valida o formato do ID do parceiro."""
        if not v or not v.startswith("PTN"):
            raise ValueError('ID do parceiro deve começar com "PTN"')
        return v

    class Config:
        """Configuração do modelo."""

        schema_extra = {"example": {"partner_id": "PTN123456"}}


class FavoriteResponse(BaseModel):
    """
    Modelo para respostas de operações de favoritos.
    """

    success: bool = Field(..., description="Indica se a operação foi bem-sucedida")
    message: str = Field(..., description="Mensagem descritiva da operação")
    favorites_count: int = Field(
        default=0, description="Número total de favoritos após a operação"
    )

    class Config:
        """Configuração do modelo."""

        schema_extra = {
            "example": {
                "success": True,
                "message": "Parceiro adicionado aos favoritos com sucesso",
                "favorites_count": 5,
            }
        }
