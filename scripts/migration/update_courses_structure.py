"""Script para atualizar a estrutura dos cursos no Firestore.

Modifica os cursos existentes para:
1. Manter apenas os campos 'code' e 'name'
2. Alterar IDs para ordenação por nível conforme id_generators.py
"""

import asyncio

from src.db.firestore import firestore_client
from src.utils.id_generators import IDGenerators
from src.utils.logging import logger


async def update_courses_structure():
    """Atualiza a estrutura dos cursos no Firestore."""
    try:
        logger.info("Iniciando atualização da estrutura de cursos")

        # Buscar todos os cursos existentes
        existing_result = await firestore_client.query_documents(
            collection="courses", filters=[], limit=100
        )

        existing_courses = existing_result.get("items", [])
        logger.info(f"Encontrados {len(existing_courses)} cursos para atualizar")

        if not existing_courses:
            logger.warning("Nenhum curso encontrado para atualizar")
            return

        # Criar mapeamento de ordem dos cursos baseado no id_generators.py
        course_order = list(IDGenerators.CURSO_CODES.keys())

        courses_updated = 0
        courses_deleted = 0

        # Deletar todos os cursos existentes primeiro
        for course in existing_courses:
            try:
                await firestore_client.delete_document(
                    collection="courses", doc_id=course["id"]
                )
                courses_deleted += 1
                logger.info(f"Curso deletado: {course.get('name', 'N/A')}")
            except Exception as e:
                logger.error(
                    f"Erro ao deletar curso {course.get('name', 'N/A')}: {str(e)}"
                )

        # Criar novos cursos com IDs ordenados
        for index, course_name in enumerate(course_order):
            try:
                course_code = IDGenerators.CURSO_CODES[course_name]

                # Gerar ID com padding para ordenação (001, 002, etc.)
                new_course_id = f"course_{str(index + 1).zfill(3)}"

                # Dados do curso com apenas os campos necessários
                course_data = {
                    "id": new_course_id,
                    "code": course_code,
                    "name": course_name,
                    "active": True,
                }

                await firestore_client.create_document(
                    collection="courses", doc_id=new_course_id, data=course_data
                )

                courses_updated += 1
                logger.info(
                    f"Curso atualizado: {course_name} ({course_code}) - ID: {new_course_id}"
                )

            except Exception as e:
                logger.error(f"Erro ao atualizar curso {course_name}: {str(e)}")

        logger.info(
            f"Atualização concluída: {courses_deleted} deletados, {courses_updated} criados"
        )

    except Exception as e:
        logger.error(f"Erro durante atualização da estrutura de cursos: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(update_courses_structure())
