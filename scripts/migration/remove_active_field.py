"""Script para remover o campo 'active' dos cursos no Firestore.

Simplifica a estrutura dos cursos removendo campos desnecessários.
"""

import asyncio

from src.db.firestore import firestore_client
from src.utils.logging import logger


async def remove_active_field():
    """Remove o campo 'active' de todos os cursos."""
    try:
        logger.info("Removendo campo 'active' dos cursos...")

        # Buscar todos os cursos
        result = await firestore_client.query_documents(collection="courses", limit=100)

        courses = result.get("items", [])
        logger.info(f"Encontrados {len(courses)} cursos para atualizar")

        if not courses:
            logger.warning("Nenhum curso encontrado")
            return

        courses_updated = 0

        for course in courses:
            try:
                # Criar nova estrutura sem o campo 'active'
                new_course_data = {
                    "id": course["id"],
                    "code": course["code"],
                    "name": course["name"],
                }

                # Atualizar o documento
                await firestore_client.update_document(
                    collection="courses", doc_id=course["id"], data=new_course_data
                )

                courses_updated += 1
                logger.info(f"Curso atualizado: {course['name']} ({course['code']})")

            except Exception as e:
                logger.error(
                    f"Erro ao atualizar curso {course.get('name', 'N/A')}: {str(e)}"
                )

        logger.info(f"Atualização concluída: {courses_updated} cursos atualizados")

    except Exception as e:
        logger.error(f"Erro durante remoção do campo 'active': {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(remove_active_field())
