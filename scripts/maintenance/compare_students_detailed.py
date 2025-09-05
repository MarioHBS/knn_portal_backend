#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para comparar alunos entre dados_alunos.json e firestore_export.json
Gera listagem detalhada para identificar diferenças
"""

import json
from pathlib import Path
from typing import Set, Dict, Any

def load_students_from_dados_alunos(file_path: Path) -> Dict[str, Dict[str, Any]]:
    """Carrega alunos do arquivo dados_alunos.json"""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('students', {})

def load_students_from_firestore_export(file_path: Path) -> Dict[str, Dict[str, Any]]:
    """Carrega alunos do arquivo firestore_export.json"""
    students = {}
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    for key, value in data.items():
        if key.startswith('__collection__/students/STD_'):
            student_id = key.replace('__collection__/students/', '')
            if 'data' in value:
                students[student_id] = value['data']
    
    return students

def compare_students():
    """Compara alunos entre os dois arquivos"""
    
    # Caminhos dos arquivos
    dados_alunos_path = Path("sources/dados_alunos.json")
    firestore_export_path = Path("data/firestore_export.json")
    
    # Verificar se os arquivos existem
    if not dados_alunos_path.exists():
        print(f"Erro: Arquivo {dados_alunos_path} não encontrado")
        return
    
    if not firestore_export_path.exists():
        print(f"Erro: Arquivo {firestore_export_path} não encontrado")
        return
    
    # Carregar dados dos alunos
    print("Carregando dados dos alunos...")
    dados_alunos_students = load_students_from_dados_alunos(dados_alunos_path)
    firestore_students = load_students_from_firestore_export(firestore_export_path)
    
    # Obter conjuntos de IDs
    dados_alunos_ids = set(dados_alunos_students.keys())
    firestore_ids = set(firestore_students.keys())
    
    print(f"\n=== RESUMO GERAL ===")
    print(f"Total de alunos em dados_alunos.json: {len(dados_alunos_ids)}")
    print(f"Total de alunos em firestore_export.json: {len(firestore_ids)}")
    
    # Alunos apenas em dados_alunos.json
    only_in_dados_alunos = dados_alunos_ids - firestore_ids
    print(f"\n=== ALUNOS APENAS EM dados_alunos.json ({len(only_in_dados_alunos)}) ===")
    if only_in_dados_alunos:
        for student_id in sorted(only_in_dados_alunos):
            student_data = dados_alunos_students[student_id]
            print(f"ID: {student_id}")
            print(f"  Nome: {student_data.get('name', 'N/A')}")
            print(f"  Livro: {student_data.get('book', 'N/A')}")
            print(f"  Ocupação: {student_data.get('occupation', 'N/A')}")
            print()
    else:
        print("Nenhum aluno encontrado apenas em dados_alunos.json")
    
    # Alunos apenas em firestore_export.json
    only_in_firestore = firestore_ids - dados_alunos_ids
    print(f"\n=== ALUNOS APENAS EM firestore_export.json ({len(only_in_firestore)}) ===")
    if only_in_firestore:
        for student_id in sorted(only_in_firestore):
            student_data = firestore_students[student_id]
            print(f"ID: {student_id}")
            print(f"  Nome: {student_data.get('name', 'N/A')}")
            print(f"  Livro: {student_data.get('book', 'N/A')}")
            print(f"  Ocupação: {student_data.get('occupation', 'N/A')}")
            print()
    else:
        print("Nenhum aluno encontrado apenas em firestore_export.json")
    
    # Alunos em ambos os arquivos
    common_students = dados_alunos_ids & firestore_ids
    print(f"\n=== ALUNOS EM AMBOS OS ARQUIVOS ({len(common_students)}) ===")
    if common_students:
        print("Lista de IDs dos alunos presentes em ambos os arquivos:")
        for student_id in sorted(common_students):
            student_data = dados_alunos_students[student_id]
            print(f"  {student_id} - {student_data.get('name', 'N/A')}")
    else:
        print("Nenhum aluno comum encontrado")
    
    # Salvar relatório em arquivo
    report_path = Path("docs/relatorio_comparacao_alunos.txt")
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("RELATÓRIO DE COMPARAÇÃO DE ALUNOS\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Data da análise: {Path().cwd()}\n")
        f.write(f"Total de alunos em dados_alunos.json: {len(dados_alunos_ids)}\n")
        f.write(f"Total de alunos em firestore_export.json: {len(firestore_ids)}\n\n")
        
        f.write(f"ALUNOS APENAS EM dados_alunos.json ({len(only_in_dados_alunos)}):\n")
        f.write("-" * 40 + "\n")
        for student_id in sorted(only_in_dados_alunos):
            student_data = dados_alunos_students[student_id]
            f.write(f"{student_id} - {student_data.get('name', 'N/A')}\n")
        
        f.write(f"\nALUNOS APENAS EM firestore_export.json ({len(only_in_firestore)}):\n")
        f.write("-" * 40 + "\n")
        for student_id in sorted(only_in_firestore):
            student_data = firestore_students[student_id]
            f.write(f"{student_id} - {student_data.get('name', 'N/A')}\n")
        
        f.write(f"\nALUNOS EM AMBOS OS ARQUIVOS ({len(common_students)}):\n")
        f.write("-" * 40 + "\n")
        for student_id in sorted(common_students):
            student_data = dados_alunos_students[student_id]
            f.write(f"{student_id} - {student_data.get('name', 'N/A')}\n")
    
    print(f"\nRelatório salvo em: {report_path}")
    
    return {
        'dados_alunos_count': len(dados_alunos_ids),
        'firestore_count': len(firestore_ids),
        'only_in_dados_alunos': len(only_in_dados_alunos),
        'only_in_firestore': len(only_in_firestore),
        'common_students': len(common_students)
    }

if __name__ == "__main__":
    compare_students()