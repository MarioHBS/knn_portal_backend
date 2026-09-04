"""
Script para migrar os campos dos cursos no Firestore para o novo formato.
"""

import asyncio
import sys
from pathlib import Path

# Adicionar o diretório raiz do projeto ao PYTHONPATH
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

# Carregar variáveis de ambiente
try:
    from dotenv import load_dotenv

    env_path = project_root / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass

from src.db.firestore import db  # noqa: E402
from src.utils.logging import logger  # noqa: E402


async def modify_course_fields():
    """
    Migra os campos dos cursos no Firestore para o novo formato.
    """
    logger.info("Iniciando a migração dos campos dos cursos no Firestore...")

    if not db:
        logger.error("A conexão com o Firestore não foi inicializada.")
        return

    try:
        courses_collection = db.collection("courses")
        courses = list(courses_collection.stream())

        if not courses:
            logger.info("Nenhum curso encontrado para migração.")
            return

        logger.info(f"Total de cursos encontrados: {len(courses)}")

        for course_doc in courses:
            course_data = course_doc.to_dict()
            course_id = course_doc.id

            updates = {}

            # Exemplo de migração: Renomear campo 'name' para 'title' se necessário
            # (Ajuste conforme a lógica real de migração necessária)
            if "name" in course_data and "title" not in course_data:
                updates["title"] = course_data["name"]

            if updates:
                await courses_collection.document(course_id).update(updates)
                logger.info(f"Curso {course_id} atualizado com sucesso.")

        logger.info("Migração dos campos dos cursos concluída.")

    except Exception as e:
        logger.error(f"Erro geral durante a migração dos cursos: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(modify_course_fields())
