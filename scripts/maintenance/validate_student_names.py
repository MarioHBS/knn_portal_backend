"""
Script para validar a existência do campo 'name' nos documentos de estudantes no Firestore.
"""

import asyncio
import sys
from pathlib import Path

# Adicionar o diretório raiz do projeto ao PYTHONPATH
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

# Carregar variáveis de ambiente antes de importar módulos do projeto
try:
    from dotenv import load_dotenv

    env_path = project_root / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print(f"Variáveis de ambiente carregadas de: {env_path}")
except ImportError:
    print("python-dotenv não encontrado, usando variáveis de ambiente do sistema")


from src.db.firestore import db  # noqa: E402
from src.utils.logging import logger  # noqa: E402


async def validate_student_names():
    """
    Valida os nomes dos estudantes no Firestore.
    """
    logger.info("Iniciando a validação de nomes de estudantes no Firestore...")

    if not db:
        logger.error("A conexão com o Firestore não foi inicializada.")
        return

    try:
        tenants_collection = db.collection("tenants")
        tenants = [tenant.id for tenant in tenants_collection.stream()]

        if not tenants:
            logger.warning("Nenhum tenant encontrado.")
            return

        logger.info(f"Tenants encontrados: {tenants}")

        for tenant_id in tenants:
            logger.info(f"Verificando estudantes para o tenant: {tenant_id}")
            # Query students for the current tenant
            students_ref = db.collection("students").where("tenant_id", "==", tenant_id)
            students = list(students_ref.stream())

            if not students:
                logger.info(f"Nenhum estudante encontrado para o tenant: {tenant_id}")
                continue

            invalid_students = []
            for student in students:
                student_data = student.to_dict()
                if "name" not in student_data or not student_data.get("name"):
                    invalid_students.append(student.id)

            if invalid_students:
                logger.warning(
                    f"Tenant '{tenant_id}': Encontrados {len(invalid_students)} estudantes com campo 'name' ausente ou vazio."
                )
                for student_id in invalid_students:
                    logger.warning(f"  - ID do estudante problemático: {student_id}")
            else:
                logger.info(
                    f"Tenant '{tenant_id}': Todos os estudantes têm o campo 'name' preenchido."
                )

    except Exception as e:
        logger.error(f"Ocorreu um erro durante a validação: {e}", exc_info=True)
    finally:
        logger.info("Validação de nomes de estudantes concluída.")


if __name__ == "__main__":
    asyncio.run(validate_student_names())
