#!/usr/bin/env python3
"""
Script para dividir o arquivo firestore_export.json em arquivos menores
Separa alunos, funcionários/parceiros e outros dados
"""

import json
from pathlib import Path


def split_firestore_export():
    """Divide o arquivo firestore_export.json em arquivos menores"""

    # Caminhos dos arquivos
    source_file = Path("data/firestore_export.json")
    students_file = Path("data/firestore_students.json")
    employees_partners_file = Path("data/firestore_employees_partners.json")
    other_data_file = Path("data/firestore_other_data.json")

    # Verificar se o arquivo fonte existe
    if not source_file.exists():
        print(f"Erro: Arquivo {source_file} não encontrado")
        return

    print("Carregando arquivo firestore_export.json...")
    with open(source_file, encoding="utf-8") as f:
        data = json.load(f)

    # Dicionários para armazenar os dados separados
    students_data = {}
    employees_partners_data = {}
    other_data = {}

    # Contadores
    students_count = 0
    employees_count = 0
    partners_count = 0
    other_count = 0

    print("Separando dados por categoria...")

    for key, value in data.items():
        if key.startswith("__collection__/students"):
            students_data[key] = value
            students_count += 1
        elif key.startswith("__collection__/employees"):
            employees_partners_data[key] = value
            employees_count += 1
        elif key.startswith("__collection__/partners"):
            employees_partners_data[key] = value
            partners_count += 1
        else:
            other_data[key] = value
            other_count += 1

    # Salvar arquivo de alunos
    print(f"Salvando {students_count} registros de alunos em {students_file}...")
    with open(students_file, "w", encoding="utf-8") as f:
        json.dump(students_data, f, ensure_ascii=False, indent=2)

    # Salvar arquivo de funcionários e parceiros
    print(
        f"Salvando {employees_count} funcionários e {partners_count} parceiros em {employees_partners_file}..."
    )
    with open(employees_partners_file, "w", encoding="utf-8") as f:
        json.dump(employees_partners_data, f, ensure_ascii=False, indent=2)

    # Salvar outros dados
    print(f"Salvando {other_count} outros registros em {other_data_file}...")
    with open(other_data_file, "w", encoding="utf-8") as f:
        json.dump(other_data, f, ensure_ascii=False, indent=2)

    # Criar backup do arquivo original
    backup_file = Path("data/firestore_export_original_backup.json")
    print(f"Criando backup do arquivo original em {backup_file}...")
    with open(backup_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # Relatório final
    print("\n=== RELATÓRIO DE DIVISÃO ===")
    print(f"Arquivo original: {source_file} ({len(data)} registros)")
    print("\nArquivos criados:")
    print(f"  📚 Alunos: {students_file} ({students_count} registros)")
    print(
        f"  👥 Funcionários e Parceiros: {employees_partners_file} ({employees_count + partners_count} registros)"
    )
    print(f"     - Funcionários: {employees_count}")
    print(f"     - Parceiros: {partners_count}")
    print(f"  📋 Outros dados: {other_data_file} ({other_count} registros)")
    print(f"  💾 Backup original: {backup_file}")

    # Verificar tamanhos dos arquivos
    original_size = source_file.stat().st_size / (1024 * 1024)  # MB
    students_size = students_file.stat().st_size / (1024 * 1024)  # MB
    emp_part_size = employees_partners_file.stat().st_size / (1024 * 1024)  # MB
    other_size = other_data_file.stat().st_size / (1024 * 1024)  # MB

    print("\n=== TAMANHOS DOS ARQUIVOS ===")
    print(f"Original: {original_size:.2f} MB")
    print(f"Alunos: {students_size:.2f} MB")
    print(f"Funcionários/Parceiros: {emp_part_size:.2f} MB")
    print(f"Outros: {other_size:.2f} MB")

    return {
        "students_count": students_count,
        "employees_count": employees_count,
        "partners_count": partners_count,
        "other_count": other_count,
        "files_created": [
            str(students_file),
            str(employees_partners_file),
            str(other_data_file),
            str(backup_file),
        ],
    }


if __name__ == "__main__":
    split_firestore_export()
