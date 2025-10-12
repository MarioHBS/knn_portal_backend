"""
Modelos de dados para respostas paginadas.

Este módulo define um modelo Pydantic genérico para padronizar
respostas de API que retornam listas de dados com paginação.
"""

from typing import Generic, TypeVar

from pydantic import Field

from src.models import BaseResponse

# Define um tipo genérico para ser usado no modelo de paginação
T = TypeVar("T")


class PaginatedResponse(BaseResponse, Generic[T]):
    """
    Modelo genérico para respostas paginadas.

    Atributos:
        items (List[T]): A lista de itens para a página atual.
        total (int): O número total de itens disponíveis.
        page (int): O número da página atual.
        per_page (int): O número de itens por página.
        pages (int): O número total de páginas.
    """

    items: list[T] = Field(..., description="Lista de itens na página atual")
    total: int = Field(..., description="Número total de itens")
    page: int = Field(..., description="Número da página atual")
    per_page: int = Field(..., description="Número de itens por página")
    pages: int = Field(..., description="Número total de páginas")
