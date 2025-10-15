"""
Script para corrigir o nome de um estudante específico no Firestore.
"""

import argparse
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

from src.db.firestore import db
from src.utils.logging import logger


async def fix_student_name(tenant_id: str, student_id: str, new_name: str):
    """
    Atualiza o nome de um estudante no Firestore.
    """
    logger.info(
        f"Iniciando a correção do nome para o estudante {student_id} no tenant {tenant_id}..."
    )

    if not db:
        logger.error("A conexão com o Firestore não foi inicializada.")
        return

    try:
        student_ref = db.collection("students").document(student_id)
        student_doc = await student_ref.get()

        if not student_doc.exists:
            logger.error(f"Estudante com ID {student_id} não encontrado.")
            return

        # Verificar se o estudante pertence ao tenant correto
        student_data = student_doc.to_dict()
        if student_data.get("tenant_id") != tenant_id:
            logger.error(
                f"O estudante {student_id} não pertence ao tenant {tenant_id}."
            )
            return

        # Atualizar o nome
        await student_ref.update({"name": new_name})
        logger.info(
            f"Nome do estudante {student_id} atualizado para '{new_name}' com sucesso."
        )

    except Exception as e:
        logger.error(f"Ocorreu um erro durante a correção: {e}", exc_info=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Corrige o nome de um estudante no Firestore."
    )
    parser.add_argument(
        "--tenant-id", required=True, help="O ID do tenant do estudante."
    )
    parser.add_argument(
        "--student-id", required=True, help="O ID do estudante a ser corrigido."
    )
    parser.add_argument(
        "--new-name", required=True, help="O novo nome para o estudante."
    )

    args = parser.parse_args()

    asyncio.run(fix_student_name(args.tenant_id, args.student_id, args.new_name))
