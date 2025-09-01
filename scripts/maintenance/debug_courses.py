"""Script para debugar e listar todos os cursos no Firestore."""

import asyncio

from src.db.firestore import firestore_client
from src.utils.logging import logger


async def debug_courses():
    """Lista todos os documentos da coleção courses para debug."""
    try:
        logger.info("Debugando coleção de cursos...")

        # Buscar TODOS os documentos sem filtros
        result = await firestore_client.query_documents(collection="courses", limit=100)

        courses = result.get("items", [])

        logger.info(f"Total de documentos encontrados: {len(courses)}")

        if courses:
            for i, course in enumerate(courses, 1):
                logger.info(f"Curso {i}:")
                for key, value in course.items():
                    logger.info(f"  {key}: {value}")
                logger.info("---")
        else:
            logger.warning("Nenhum documento encontrado na coleção 'courses'")

        # Verificar campos específicos
        if courses:
            first_course = courses[0]
            logger.info(f"Campos do primeiro curso: {list(first_course.keys())}")
            logger.info(f"Tem campo 'active'? {'active' in first_course}")

    except Exception as e:
        logger.error(f"Erro durante debug: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(debug_courses())
