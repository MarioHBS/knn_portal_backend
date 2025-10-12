"""
Script para importar dados de benefícios de um arquivo JSON para a coleção 'benefits' no Firestore.
"""

import json
import os
import sys
from typing import Any

# Adiciona o diretório raiz do projeto ao sys.path para permitir importações de módulos internos
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.db.firestore import db  # type: ignore


def import_benefits_to_firestore(json_file_path: str) -> None:
    """
    Importa dados de benefícios de um arquivo JSON para a coleção 'benefits' no Firestore.

    Args:
        json_file_path (str): O caminho para o arquivo JSON contendo os dados dos benefícios.
    """
    if not os.path.exists(json_file_path):
        print(f"Erro: Arquivo não encontrado em {json_file_path}")
        return

    try:
        with open(json_file_path, encoding='utf-8') as f:
            data: dict[str, Any] = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Erro ao decodificar JSON: {e}")
        return
    except OSError as e:
        print(f"Erro de E/S ao ler o arquivo: {e}")
        return

    benefits_collection = db.collection('benefits')
    imported_count = 0

    print("Iniciando importação de benefícios para o Firestore...")

    for key, value in data.items():
        if key.startswith('__collection__/benefits/'):
            # Extrai o ID do benefício da chave
            # Ex: '__collection__/benefits/PTN_A7E6314_EDU' -> 'PTN_A7E6314_EDU'
            # Em seguida, acessa o objeto 'data' dentro do valor
            benefit_container = value.get('data')
            if benefit_container:
                for benefit_id, benefit_data in benefit_container.items():
                    if benefit_id and benefit_data:
                        try:
                            benefits_collection.document(benefit_id).set(benefit_data)
                            print(f"Benefício {benefit_id} importado com sucesso.")
                            imported_count += 1
                        except Exception as e:
                            print(f"Erro ao importar benefício {benefit_id}: {e}")
                    else:
                        print(f"Aviso: Dados inválidos para o benefício {benefit_id}. Ignorando.")

    print(f"Importação concluída. Total de benefícios importados: {imported_count}")


if __name__ == "__main__":
    # Define o caminho para o arquivo JSON de benefícios
    benefits_json_path = (
        "p:/ProjectsWEB/PRODUCAO/KNN PROJECT/knn_portal_journey_club_backend/"
        "data/firestore_export/firestore_benefits.json"
    )
    import_benefits_to_firestore(benefits_json_path)
