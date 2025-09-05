"""Endpoints utilitários da API."""

from fastapi import APIRouter

from src.db.firestore import db
from src.utils.id_generators import CURSO_CODES
from src.utils.logging import logger
from src.utils.rate_limit import limiter

router = APIRouter()


@router.get("/courses", response_model=list[str])
@limiter.limit("100/minute")
async def get_courses(request):
    """
    Retorna a lista de cursos disponíveis da base de dados.
    Se não houver cursos na base de dados, retorna do mapeamento hardcoded.

    Returns:
        list[str]: Lista com os nomes dos cursos disponíveis
    """
    try:
        # Tentar buscar cursos da base de dados
        courses_ref = db.collection("courses")
        courses_query = courses_ref.where("active", "==", True)
        courses_docs = courses_query.stream()

        courses_data = []
        for doc in courses_docs:
            course_dict = doc.to_dict()
            course_dict["id"] = doc.id
            courses_data.append(course_dict)

        if courses_data:
            courses = [course["name"] for course in courses_data]
            logger.info(
                f"Lista de cursos retornada da base de dados: {len(courses)} cursos"
            )
        else:
            # Fallback para mapeamento hardcoded
            courses = list(CURSO_CODES.keys())
            logger.warning(
                "Nenhum curso encontrado na base de dados, usando mapeamento hardcoded"
            )

        return courses

    except Exception as e:
        logger.error(f"Erro ao buscar cursos: {str(e)}")
        # Fallback para mapeamento hardcoded em caso de erro
        courses = list(CURSO_CODES.keys())
        logger.info(
            "Retornando cursos do mapeamento hardcoded devido a erro na base de dados"
        )
        return courses


@router.get("/course-codes", response_model=dict[str, str])
@limiter.limit("100/minute")
async def get_course_codes(request):
    """
    Retorna o mapeamento completo de cursos para códigos da base de dados.
    Se não houver cursos na base de dados, retorna do mapeamento hardcoded.

    Returns:
        dict[str, str]: Dicionário com curso como chave e código como valor
    """
    try:
        # Tentar buscar cursos da base de dados
        courses_ref = db.collection("courses")
        courses_query = courses_ref.where("active", "==", True)
        courses_docs = courses_query.stream()

        courses_data = []
        for doc in courses_docs:
            course_dict = doc.to_dict()
            course_dict["id"] = doc.id
            courses_data.append(course_dict)

        if courses_data:
            course_codes = {course["name"]: course["code"] for course in courses_data}
            logger.info("Mapeamento de códigos de cursos retornado da base de dados")
        else:
            # Fallback para mapeamento hardcoded
            course_codes = CURSO_CODES
            logger.warning(
                "Nenhum curso encontrado na base de dados, usando mapeamento hardcoded"
            )

        return course_codes

    except Exception as e:
        logger.error(f"Erro ao buscar códigos de cursos: {str(e)}")
        # Fallback para mapeamento hardcoded em caso de erro
        logger.info(
            "Retornando códigos do mapeamento hardcoded devido a erro na base de dados"
        )
        return CURSO_CODES
