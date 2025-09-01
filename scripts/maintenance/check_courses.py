"""Script para verificar se os cursos foram adicionados ao Firestore."""

import asyncio

from src.db.firestore import firestore_client
from src.utils.logging import logger


async def check_courses():
    """Verifica se os cursos estão presentes no Firestore."""
    try:
        logger.info("Verificando cursos na base de dados Firestore...")

        # Buscar todos os cursos
        courses_result = await firestore_client.query_documents(
            collection="courses", limit=100
        )

        courses_data = courses_result.get("items", [])

        if courses_data:
            logger.info(f"✅ Encontrados {len(courses_data)} cursos na base de dados:")
            for course in courses_data:
                logger.info(f"   - {course['name']} ({course['code']})")
        else:
            logger.warning("❌ Nenhum curso encontrado na base de dados")

        return len(courses_data) if courses_data else 0

    except Exception as e:
        logger.error(f"Erro ao verificar cursos: {str(e)}")
        return -1


if __name__ == "__main__":
    result = asyncio.run(check_courses())
    if result > 0:
        print(f"\n✅ Verificação concluída: {result} cursos ativos encontrados")
    elif result == 0:
        print("\n⚠️  Nenhum curso ativo encontrado na base de dados")
    else:
        print("\n❌ Erro durante a verificação")
