"""Script consolidado para operações de manutenção de cursos.

Combina funcionalidades de verificação, depuração e população de cursos
para facilitar a manutenção e reduzir duplicação de código.
"""

import asyncio
import sys
from pathlib import Path

from src.db.firestore import firestore_client
from src.utils.id_generators import IDGenerators
from src.utils.logging import logger

# Adicionar o diretório raiz ao path para imports
root_dir = Path(__file__).parent.parent.parent
sys.path.append(str(root_dir))


class CoursesOperations:
    """Classe para operações consolidadas de cursos."""

    @staticmethod
    async def check_courses():
        """Verifica a presença de cursos no Firestore."""
        try:
            logger.info("Verificando cursos no Firestore...")

            result = await firestore_client.query_documents(
                collection="courses",
                filters=[],
                limit=100
            )

            courses = result.get("items", [])

            if courses:
                logger.info(f"✓ Encontrados {len(courses)} cursos no Firestore")
                return True
            else:
                logger.warning("✗ Nenhum curso encontrado no Firestore")
                return False

        except Exception as e:
            logger.error(f"Erro ao verificar cursos: {str(e)}")
            return False

    @staticmethod
    async def debug_courses():
        """Lista todos os cursos para depuração."""
        try:
            logger.info("Listando cursos para depuração...")

            result = await firestore_client.query_documents(
                collection="courses",
                filters=[],
                limit=100
            )

            courses = result.get("items", [])

            if not courses:
                logger.info("Nenhum curso encontrado")
                return

            logger.info(f"Encontrados {len(courses)} cursos:")
            for course in courses:
                logger.info(f"- ID: {course.get('id', 'N/A')}, Nome: {course.get('name', 'N/A')}")

        except Exception as e:
            logger.error(f"Erro ao listar cursos: {str(e)}")

    @staticmethod
    async def populate_courses():
        """Popula a base de dados com cursos disponíveis."""
        try:
            logger.info("Iniciando população de cursos...")

            # Verificar se já existem cursos
            existing_result = await firestore_client.query_documents(
                collection="courses",
                filters=[],
                limit=1
            )

            if existing_result.get("items"):
                logger.info("Cursos já existem. Use --force para sobrescrever")
                return

            # Criar cursos baseados no IDGenerators
            courses_created = 0

            for course_code, course_name in IDGenerators.CURSO_CODES.items():
                course_data = {
                    "code": course_code,
                    "name": course_name
                }

                # Gerar ID baseado na ordem
                course_order = list(IDGenerators.CURSO_CODES.keys())
                course_index = course_order.index(course_code)
                course_id = f"course_{course_index + 1:02d}"

                await firestore_client.create_document(
                    collection="courses",
                    doc_id=course_id,
                    data=course_data
                )

                courses_created += 1
                logger.info(f"Curso criado: {course_name} (ID: {course_id})")

            logger.info(f"População concluída. {courses_created} cursos criados.")

        except Exception as e:
            logger.error(f"Erro ao popular cursos: {str(e)}")


async def main():
    """Função principal com menu de operações."""
    operations = CoursesOperations()

    if len(sys.argv) < 2:
        print("Uso: python courses_operations.py [check|debug|populate]")
        print("  check    - Verifica presença de cursos")
        print("  debug    - Lista todos os cursos")
        print("  populate - Popula cursos na base de dados")
        return

    operation = sys.argv[1].lower()

    if operation == "check":
        await operations.check_courses()
    elif operation == "debug":
        await operations.debug_courses()
    elif operation == "populate":
        await operations.populate_courses()
    else:
        print(f"Operação '{operation}' não reconhecida")
        print("Operações disponíveis: check, debug, populate")


if __name__ == "__main__":
    asyncio.run(main())
