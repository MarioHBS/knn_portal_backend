#!/usr/bin/env python3
"""
Script para comparar IDs de alunos entre firestore_export.json e dados_alunos.json
"""

import json
import re
from pathlib import Path


def extract_firestore_ids(firestore_path):
    """Extrai IDs de alunos do firestore_export.json"""
    with open(firestore_path, encoding="utf-8") as f:
        content = f.read()

    # Busca por padrão __collection__/students/STD_XXXXX
    pattern = r'"__collection__/students/(STD_[^"]+)"'
    matches = re.findall(pattern, content)
    return sorted(set(matches))


def extract_dados_alunos_ids(dados_path):
    """Extrai IDs de alunos do dados_alunos.json"""
    with open(dados_path, encoding="utf-8") as f:
        data = json.load(f)

    return sorted(data["students"].keys())


def compare_ids(firestore_ids, dados_ids):
    """Compara as duas listas de IDs"""
    firestore_set = set(firestore_ids)
    dados_set = set(dados_ids)

    # IDs que estão no firestore mas não nos dados_alunos
    only_in_firestore = firestore_set - dados_set

    # IDs que estão nos dados_alunos mas não no firestore
    only_in_dados = dados_set - firestore_set

    return only_in_firestore, only_in_dados


def main():
    # Caminhos dos arquivos
    firestore_path = Path(
        "P:/ProjectsWEB/PRODUCAO/KNN PROJECT/knn_portal_journey_club_backend/data/firestore_export.json"
    )
    dados_path = Path(
        "P:/ProjectsWEB/PRODUCAO/KNN PROJECT/knn_portal_journey_club_backend/sources/dados_alunos.json"
    )

    print("Extraindo IDs do firestore_export.json...")
    firestore_ids = extract_firestore_ids(firestore_path)
    print(f"Total de alunos no firestore_export.json: {len(firestore_ids)}")

    print("\nExtraindo IDs do dados_alunos.json...")
    dados_ids = extract_dados_alunos_ids(dados_path)
    print(f"Total de alunos no dados_alunos.json: {len(dados_ids)}")

    print("\nComparando listas...")
    only_in_firestore, only_in_dados = compare_ids(firestore_ids, dados_ids)

    print("\n=== RESULTADOS ===")
    print(f"Alunos apenas no firestore_export.json: {len(only_in_firestore)}")
    if only_in_firestore:
        print("IDs extras no firestore:")
        for student_id in sorted(only_in_firestore):
            print(f"  - {student_id}")

    print(f"\nAlunos apenas no dados_alunos.json: {len(only_in_dados)}")
    if only_in_dados:
        print("IDs faltando no firestore:")
        for student_id in sorted(only_in_dados):
            print(f"  - {student_id}")

    if not only_in_firestore and not only_in_dados:
        print("\n✅ Os arquivos estão sincronizados!")
    else:
        print("\n❌ Os arquivos NÃO estão sincronizados!")


if __name__ == "__main__":
    main()
