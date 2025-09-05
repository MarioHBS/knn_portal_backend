#!/usr/bin/env python3
"""
Script para padronizar a estrutura dos dados de alunos no firestore_export.json
para corresponder ao formato do dados_alunos.json
"""

import json
from pathlib import Path


def transform_student_data(student_data):
    """
    Transforma a estrutura de dados de um aluno do formato atual
    para o formato padronizado
    """
    data = student_data.get("data", {})

    # Estrutura padronizada
    transformed = {
        "name": data.get("nome", ""),
        "book": data.get("livro", ""),
        "occupation": data.get("ocupacao", ""),
        "contact": {"email": data.get("e-mail", ""), "phone": data.get("telefone", "")},
        "address": {
            "zip": data.get("cep", ""),
            "neighborhood": data.get("bairro", ""),
            "complement": data.get("complemento_aluno", ""),
        },
        "guardian": {
            "name": data.get("nome_responsavel", "") or "",
            "email": data.get("e-mail_responsavel", "") or "",
        },
    }

    # Manter campos do sistema
    if "id" in data:
        transformed["id"] = data["id"]
    if "tenant_id" in data:
        transformed["tenant_id"] = data["tenant_id"]
    if "active_until" in data:
        transformed["active_until"] = data["active_until"]
    if "created_at" in data:
        transformed["created_at"] = data["created_at"]
    if "updated_at" in data:
        transformed["updated_at"] = data["updated_at"]

    return {"data": transformed}


def main():
    # Caminhos dos arquivos
    project_root = Path(__file__).parent.parent.parent
    firestore_export_path = project_root / "data" / "firestore_export.json"

    print(f"Carregando arquivo: {firestore_export_path}")

    # Carregar o arquivo JSON
    with open(firestore_export_path, encoding="utf-8") as f:
        data = json.load(f)

    # Contar alunos transformados
    students_transformed = 0

    # Transformar dados dos alunos
    for key, value in data.items():
        if key.startswith("__collection__/students/STD_"):
            print(f"Transformando: {key}")
            data[key] = transform_student_data(value)
            students_transformed += 1

    # Salvar o arquivo atualizado
    print("Salvando arquivo atualizado...")
    with open(firestore_export_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print("✅ Transformação concluída!")
    print(f"📊 Total de alunos transformados: {students_transformed}")
    print(f"📁 Arquivo atualizado: {firestore_export_path}")


if __name__ == "__main__":
    main()
