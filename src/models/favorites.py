"""
Modelos para gerenciamento de favoritos no Firestore.

Este módulo define os modelos Pydantic para a coleção de favoritos
de alunos (students_fav).
"""

from datetime import UTC, datetime

from pydantic import BaseModel, Field, field_validator


class FavoriteRequest(BaseModel):
    """
    Modelo de requisição para adicionar um parceiro aos favoritos.
    """

    partner_id: str = Field(..., description="ID do parceiro a ser favoritado")

    @field_validator("partner_id")
    @classmethod
    def validate_partner_id_format(cls, v):
        if not v or not v.startswith("PTN"):
            raise ValueError('ID do parceiro deve começar com "PTN"')
        return v


class FavoriteResponse(BaseModel):
    """
    Modelo de resposta para operações de favoritos.
    """

    success: bool = Field(..., description="Indica se a operação foi bem-sucedida")
    message: str = Field(..., description="Mensagem descritiva do resultado")
    favorites_count: int = Field(
        default=0, description="Quantidade de favoritos do usuário após a operação"
    )


class StudentPartnerFavorite(BaseModel):
    """
    Modelo para um documento na coleção 'students_fav'.

    Cada documento representa um parceiro específico que foi favoritado
    por um aluno específico.
    """

    student_id: str = Field(..., description="ID do estudante que favoritou o parceiro")
    partner_id: str = Field(..., description="ID do parceiro que foi favoritado")
    favorited_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Timestamp de quando o parceiro foi favoritado (UTC)",
    )

    @field_validator("student_id")
    @classmethod
    def validate_student_id(cls, v):
        """Valida o formato do ID do estudante."""
        # IDs de alunos no sistema começam com "STD"
        if not v or not v.startswith("STD"):
            raise ValueError('ID do estudante deve começar com "STD"')
        return v

    @field_validator("partner_id")
    @classmethod
    def validate_partner_id_format(cls, v):
        """Valida o formato do ID do parceiro."""
        if not v or not v.startswith("PTN"):
            raise ValueError('ID do parceiro deve começar com "PTN"')
        return v

    class Config:
        """Configuração do modelo."""

        json_encoders = {datetime: lambda v: v.isoformat()}
        schema_extra = {
            "example": {
                "student_id": "STD_ABC123",
                "partner_id": "PTN789012",
                "favorited_at": "2024-01-15T10:30:00Z",
            }
        }
