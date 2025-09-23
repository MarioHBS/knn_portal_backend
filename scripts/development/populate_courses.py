"""Script para popular a base de dados com os cursos disponíveis."""

import asyncio
from datetime import datetime

from src.db.firestore import firestore_client
from src.models import Course
from src.utils.id_generators import IDGenerators
from src.utils.logging import logger


async def populate_courses():
    """Popula a coleção de cursos no Firestore com os cursos disponíveis."""
    try:
        # Usar cliente Firestore

        logger.info("Iniciando população de cursos na base de dados")

        # Criar cursos baseados no mapeamento CURSO_CODES
        courses_created = 0
        courses_updated = 0

        for course_name, course_code in IDGenerators.CURSO_CODES.items():
            try:
                # Verificar se o curso já existe
                existing_result = await firestore_client.query_documents(
                    collection="courses",
                    filters=[("name", "==", course_name)],
                    limit=1
                )

                existing_courses = existing_result.get("items", [])

                if existing_courses:
                    # Atualizar curso existente
                    course_data = existing_courses[0]
                    course_data["code"] = course_code
                    course_data["updated_at"] = datetime.now()
                    course_data["active"] = True

                    await firestore_client.update_document(
                        collection="courses",
                        doc_id=course_data["id"],
                        data=course_data
                    )
                    courses_updated += 1
                    logger.info(f"Curso atualizado: {course_name} ({course_code})")
                else:
                    # Criar novo curso
                    course = Course(
                        name=course_name,
                        code=course_code,
                        active=True
                    )

                    await firestore_client.create_document(
                        collection="courses",
                        doc_id=course.id,
                        data=course.model_dump()
                    )
                    courses_created += 1
                    logger.info(f"Curso criado: {course_name} ({course_code})")

            except Exception as e:
                logger.error(f"Erro ao processar curso {course_name}: {str(e)}")
                continue

        logger.info(
            f"População de cursos concluída: {courses_created} criados, "
            f"{courses_updated} atualizados"
        )

    except Exception as e:
        logger.error(f"Erro durante população de cursos: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(populate_courses())