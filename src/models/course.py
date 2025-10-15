"""
Módulo que define o modelo de dados para os cursos.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class CourseDTO(BaseModel):
    """ """

    code: str
    book: str
    idiom: str
    sequential_order: int
    updated_at: datetime

    def to_model(self, course_id: str) -> "CourseModel":
        """
        Converte o DTO para o modelo de curso.

        Args:
            course_id: O ID do curso.

        Returns:
            Uma instância de CourseModel.
        """
        return CourseModel(id=course_id, **self.model_dump())


class CourseModel(BaseModel):
    """
    Representa um curso oferecido pela escola.
    """

    id: str = Field(..., description="O ID único do curso.")
    code: str = Field(..., description="O código de abreviação do curso.")
    book: str = Field(..., description="O nome do livro ou material do curso.")
    idiom: str = Field(..., description="O idioma do curso (ex: 'english', 'spanish').")
    sequential_order: int = Field(
        ...,
        description="A ordem de sequência para a progressão do curso.",
        alias="sequential_order",
    )
    updated_at: datetime = Field(
        ...,
        description="A data e hora da última atualização do curso.",
    )

    class Config:
        """
        Configurações do modelo Pydantic.
        """

        populate_by_name = True
        from_attributes = True


class CourseList(BaseModel):
    """
    Representa uma lista de cursos.
    """

    courses: list[CourseModel]
