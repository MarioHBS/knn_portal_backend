"""
Módulo que define os endpoints da API para gerenciamento de cursos.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from src.db.firestore import FirestoreClient
from src.models.course import CourseDTO, CourseList

router = APIRouter()


@router.get(
    "/",
    response_model=CourseList,
    summary="Recupera uma lista de cursos",
    description="Recupera uma lista de todos os cursos disponíveis, com a opção de filtrar por idioma.",
    tags=["Courses"],
)
async def get_all_courses(
    db: Annotated[FirestoreClient, Depends(FirestoreClient)],
    idiom: Annotated[
        str | None,
        Query(
            description="Filtra os cursos pelo idioma (ex: 'english', 'spanish').",
            example="english",
        ),
    ] = None,
) -> CourseList:
    """
    Endpoint para buscar todos os cursos, com filtro opcional por idioma.

    Args:
        db: Instância do cliente Firestore.
        idiom: Idioma para filtrar os cursos.

    Returns:
        Uma lista de cursos.
    """
    filters = {}
    if idiom:
        filters["idiom"] = idiom

    courses_data = await db.query_documents(
        collection="courses", filters=filters, order_by="sequential_order"
    )

    courses_models = []
    for course_doc in courses_data:
        course_dto = CourseDTO(**course_doc)
        courses_models.append(course_dto.to_model(course_doc["id"]))

    return CourseList(courses=courses_models)
