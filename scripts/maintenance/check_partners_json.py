#!/usr/bin/env python3
"""
Script para verificar os parceiros no arquivo firestore_employees_partners.json
"""

import json
from pathlib import Path


def check_partners():
    """Verifica os parceiros no arquivo firestore_employees_partners.json"""

    firestore_file = Path("data/firestore_employees_partners.json")

    if not firestore_file.exists():
        print(f"Erro: Arquivo {firestore_file} não encontrado")
        return

    with open(firestore_file, encoding="utf-8") as f:
        data = json.load(f)

    # Encontrar parceiros
    partners = [
        k
        for k in data
        if k.startswith("__collection__/partners/") and k != "__collection__/partners"
    ]

    print(f"Total de parceiros: {len(partners)}")
    print("\nLista de parceiros:")

    for partner_key in partners:
        partner_data = data[partner_key]["data"]
        partner_id = partner_key.split("/")[-1]
        name = partner_data.get("name", "Nome não encontrado")
        category = partner_data.get("category", "Categoria não encontrada")
        print(f"- {name} ({partner_id}) - {category}")

    # Verificar funcionários também
    employees = [
        k
        for k in data
        if k.startswith("__collection__/employees/") and k != "__collection__/employees"
    ]
    print(f"\nTotal de funcionários: {len(employees)}")

    print("\nResumo:")
    print(f"- Funcionários: {len(employees)}")
    print(f"- Parceiros: {len(partners)}")
    print(f"- Total: {len(employees) + len(partners)}")


if __name__ == "__main__":
    check_partners()
