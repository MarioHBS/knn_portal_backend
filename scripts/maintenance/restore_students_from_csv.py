#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para restaurar dados_alunos.json a partir do arquivo CSV
"""

import csv
import json
from pathlib import Path
from datetime import datetime

def restore_students_from_csv():
    """Restaura o arquivo dados_alunos.json a partir do CSV"""
    
    # Caminhos dos arquivos
    csv_path = Path("sources/dados_alunos.csv")
    json_path = Path("sources/dados_alunos.json")
    
    # Verificar se o CSV existe
    if not csv_path.exists():
        print(f"Erro: Arquivo {csv_path} não encontrado")
        return False
    
    # Estrutura base do JSON
    json_data = {
        "metadata": {
            "count": 0,
            "generation_date": datetime.now().strftime("%Y-%m-%d"),
            "description": "Dados de alunos ativos formatados para alimentação de banco de dados",
            "version": 1
        },
        "students": {},
        "columns": [
            "name",
            "book",
            "occupation",
            {
                "contact": [
                    "email",
                    "phone"
                ]
            },
            {
                "address": [
                    "zip",
                    "neighborhood",
                    "complement"
                ]
            },
            {
                "guardian": [
                    "name",
                    "email"
                ]
            }
        ]
    }
    
    # Ler o CSV e converter para JSON
    with open(csv_path, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        
        for row in reader:
            student_id = row['id']
            
            # Estruturar os dados do aluno
            student_data = {
                "name": row['nome_aluno'],
                "book": row['livro'],
                "occupation": row['ocupacao_aluno'],
                "contact": {
                    "email": row['email_aluno'] or "",
                    "phone": row['celular_aluno'] or ""
                },
                "address": {
                    "zip": row['cep_aluno'] or "",
                    "neighborhood": row['bairro'] or "",
                    "complement": row['complemento_aluno'] or ""
                },
                "guardian": {
                    "name": row['nome_responsavel'] or "",
                    "email": row['email_responsavel'] or ""
                }
            }
            
            json_data["students"][student_id] = student_data
    
    # Atualizar o count
    json_data["metadata"]["count"] = len(json_data["students"])
    
    # Fazer backup do arquivo atual se existir
    if json_path.exists():
        backup_path = json_path.with_suffix('.json.backup')
        json_path.rename(backup_path)
        print(f"Backup criado: {backup_path}")
    
    # Salvar o novo JSON
    with open(json_path, 'w', encoding='utf-8') as jsonfile:
        json.dump(json_data, jsonfile, indent=2, ensure_ascii=False)
    
    print(f"Arquivo {json_path} restaurado com sucesso!")
    print(f"Total de alunos restaurados: {json_data['metadata']['count']}")
    
    return True

if __name__ == "__main__":
    restore_students_from_csv()