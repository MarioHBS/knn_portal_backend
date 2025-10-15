"""Script para modificar os campos 'name' e 'sequence_order' nos cursos existentes.

Este script percorre todos os documentos na coleção 'courses', renomeia 'sequence_order'
para 'sequential_order', usa 'name' para criar o campo 'book' e, em seguida,
exclui os campos 'name' e 'sequence_order' originais.
"""

import asyncio
import os
import sys

# Adicionar o diretório raiz do projeto ao sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from google.cloud import firestore

from src.db.firestore import FirestoreClient
from src.utils.logging import logger


async def modify_course_fields():
    """Modifica os campos dos cursos no Firestore."""
    try:
        logger.info("Iniciando a modificação de campos dos cursos...")

        # Buscar todos os cursos existentes
        courses = await FirestoreClient.query_documents(collection="courses", limit=100)

        if not courses:
            logger.warning("Nenhum curso encontrado para atualizar.")
            return

        logger.info(f"Encontrados {len(courses)} cursos para atualizar.")

        updated_count = 0
        for index, course in enumerate(courses):
            try:
                doc_id = course["id"]
                book_name = course.get("name")

                if not book_name:
                    logger.warning(
                        f"Curso '{doc_id}' não tem o campo 'name'. Pulando a criação do campo 'book'."
                    )
                    book_name = f"Unknown Book {index + 1}"

                update_data = {
                    "book": book_name,
                    "sequential_order": (index + 1) * 10,
                    "name": firestore.DELETE_FIELD,
                    "sequence_order": firestore.DELETE_FIELD,
                }

                # Atualizar o documento no Firestore
                FirestoreClient.update_document(
                    collection="courses", doc_id=doc_id, data=update_data
                )

                updated_count += 1
                logger.info(
                    f"Curso '{doc_id}' atualizado. Campos 'name' e 'sequence_order' removidos."
                )

            except Exception as e:
                logger.error(f"Erro ao atualizar o curso '{course.get('id', 'N/A')}': {e}")

        logger.info(f"Migração concluída: {updated_count} cursos foram atualizados.")

    except Exception as e:
        logger.error(f"Erro geral durante a migração dos cursos: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(modify_course_fields())