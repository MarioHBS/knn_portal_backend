"""
Script para simular o ambiente de dados para testes locais.
"""

import hashlib
import json
import os
import uuid
from datetime import datetime, timedelta

# Diretório para armazenar dados simulados
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_data")

# Criar diretório se não existir
os.makedirs(DATA_DIR, exist_ok=True)


# Função para gerar hash de CPF
def hash_cpf(cpf, salt="knn-dev-salt"):
    return hashlib.sha256(f"{cpf}{salt}".encode()).hexdigest()


# Função para gerar dados de teste
def generate_test_data():
    # Dados de alunos
    students = [
        {
            "id": str(uuid.uuid4()),
            "cpf_hash": hash_cpf("12345678901"),
            "name": "Ana Silva",
            "email": "ana.silva@exemplo.com",
            "course": "Inglês Avançado",
            "active_until": (datetime.now() + timedelta(days=30)).date().isoformat(),
            "active": True,
        },
        {
            "id": str(uuid.uuid4()),
            "cpf_hash": hash_cpf("23456789012"),
            "name": "Bruno Santos",
            "email": "bruno.santos@exemplo.com",
            "course": "Espanhol Intermediário",
            "active_until": (datetime.now() + timedelta(days=60)).date().isoformat(),
            "active": True,
        },
        {
            "id": str(uuid.uuid4()),
            "cpf_hash": hash_cpf("34567890123"),
            "name": "Carla Oliveira",
            "email": "carla.oliveira@exemplo.com",
            "course": "Francês Básico",
            "active_until": (datetime.now() - timedelta(days=10)).date().isoformat(),
            "active": True,
        },
    ]

    # Dados de parceiros
    partners = [
        {
            "id": str(uuid.uuid4()),
            "trade_name": "Livraria Cultura",
            "category": "Livraria",
            "address": "Av. Paulista, 2073 - São Paulo/SP",
            "active": True,
        },
        {
            "id": str(uuid.uuid4()),
            "trade_name": "Restaurante Sabor & Arte",
            "category": "Alimentação",
            "address": "Rua Augusta, 1200 - São Paulo/SP",
            "active": True,
        },
        {
            "id": str(uuid.uuid4()),
            "trade_name": "Cinema Lumière",
            "category": "Entretenimento",
            "address": "Shopping Cidade, Loja 42 - São Paulo/SP",
            "active": False,
        },
    ]

    # Dados de promoções
    promotions = [
        {
            "id": str(uuid.uuid4()),
            "partner_id": partners[0]["id"],
            "title": "20% de desconto em livros de idiomas",
            "type": "discount",
            "valid_from": (datetime.now() - timedelta(days=10)).isoformat(),
            "valid_to": (datetime.now() + timedelta(days=20)).isoformat(),
            "active": True,
        },
        {
            "id": str(uuid.uuid4()),
            "partner_id": partners[0]["id"],
            "title": "Brinde exclusivo na compra acima de R$ 100",
            "type": "gift",
            "valid_from": (datetime.now() - timedelta(days=5)).isoformat(),
            "valid_to": (datetime.now() + timedelta(days=25)).isoformat(),
            "active": True,
        },
        {
            "id": str(uuid.uuid4()),
            "partner_id": partners[1]["id"],
            "title": "15% de desconto no almoço executivo",
            "type": "discount",
            "valid_from": (datetime.now() - timedelta(days=15)).isoformat(),
            "valid_to": (datetime.now() + timedelta(days=15)).isoformat(),
            "active": True,
        },
        {
            "id": str(uuid.uuid4()),
            "partner_id": partners[2]["id"],
            "title": "Ingresso com 30% de desconto nas segundas e terças",
            "type": "discount",
            "valid_from": (datetime.now() - timedelta(days=30)).isoformat(),
            "valid_to": (datetime.now() - timedelta(days=1)).isoformat(),
            "active": True,
        },
    ]

    # Dados de códigos de validação
    validation_codes = [
        {
            "id": str(uuid.uuid4()),
            "student_id": students[0]["id"],
            "partner_id": partners[0]["id"],
            "code_hash": "123456",
            "expires": (datetime.now() + timedelta(minutes=3)).isoformat(),
            "used_at": None,
        },
        {
            "id": str(uuid.uuid4()),
            "student_id": students[1]["id"],
            "partner_id": partners[1]["id"],
            "code_hash": "654321",
            "expires": (datetime.now() - timedelta(minutes=5)).isoformat(),
            "used_at": None,
        },
        {
            "id": str(uuid.uuid4()),
            "student_id": students[0]["id"],
            "partner_id": partners[0]["id"],
            "code_hash": "111222",
            "expires": (datetime.now() - timedelta(minutes=10)).isoformat(),
            "used_at": (datetime.now() - timedelta(minutes=12)).isoformat(),
        },
    ]

    # Dados de resgates
    redemptions = [
        {
            "id": str(uuid.uuid4()),
            "validation_code_id": validation_codes[2]["id"],
            "value": 50.0,
            "used_at": validation_codes[2]["used_at"],
        }
    ]

    # Dados de favoritos
    favorites = [
        {
            "id": str(uuid.uuid4()),
            "student_id": students[0]["id"],
            "partner_id": partners[0]["id"],
            "created_at": (datetime.now() - timedelta(days=5)).isoformat(),
        },
        {
            "id": str(uuid.uuid4()),
            "student_id": students[1]["id"],
            "partner_id": partners[1]["id"],
            "created_at": (datetime.now() - timedelta(days=3)).isoformat(),
        },
    ]

    # Salvar dados em arquivos JSON
    data = {
        "students": students,
        "partners": partners,
        "promotions": promotions,
        "validation_codes": validation_codes,
        "redemptions": redemptions,
        "favorites": favorites,
    }

    for entity, items in data.items():
        with open(os.path.join(DATA_DIR, f"{entity}.json"), "w") as f:
            json.dump(items, f, indent=2)

    # Criar arquivo de mapeamento de IDs para facilitar testes
    id_mapping = {
        "students": {student["name"]: student["id"] for student in students},
        "partners": {partner["trade_name"]: partner["id"] for partner in partners},
        "promotions": {promotion["title"]: promotion["id"] for promotion in promotions},
        "validation_codes": {
            code["code_hash"]: code["id"] for code in validation_codes
        },
        "cpf_mapping": {
            "12345678901": "Ana Silva (ativo)",
            "23456789012": "Bruno Santos (ativo)",
            "34567890123": "Carla Oliveira (inativo)",
        },
    }

    with open(os.path.join(DATA_DIR, "id_mapping.json"), "w") as f:
        json.dump(id_mapping, f, indent=2)

    print(f"Dados de teste gerados com sucesso em {DATA_DIR}")
    print("Mapeamento de IDs salvo em id_mapping.json")


if __name__ == "__main__":
    generate_test_data()
