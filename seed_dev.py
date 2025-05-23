#!/usr/bin/env python3
"""
Script para geração de dados de desenvolvimento/QA para o Portal de Benefícios KNN.
Cria 5 alunos, 3 parceiros e 4 promoções conforme solicitado.
"""

import uuid
import hashlib
import json
import random
from datetime import datetime, timedelta

# Configurações
FIRESTORE_EMULATOR_HOST = "localhost:8080"
CPF_HASH_SALT = "knn-dev-salt-2025"

# Função para gerar hash de CPF
def hash_cpf(cpf, salt):
    """Gera hash SHA-256 do CPF com salt"""
    return hashlib.sha256(f"{cpf}{salt}".encode()).hexdigest()

# Função para gerar UUID
def generate_uuid():
    """Gera UUID v4 como string"""
    return str(uuid.uuid4())

# Função para gerar data ISO
def iso_date(days_offset=0):
    """Gera data ISO com offset em dias"""
    return (datetime.now() + timedelta(days=days_offset)).isoformat()

# Função para gerar data ISO (apenas data)
def iso_date_only(days_offset=0):
    """Gera data ISO (apenas data) com offset em dias"""
    return (datetime.now() + timedelta(days=days_offset)).date().isoformat()

# Dados para seed
students = [
    {
        "id": generate_uuid(),
        "cpf_hash": hash_cpf("12345678901", CPF_HASH_SALT),
        "name": "Ana Silva",
        "email": "ana.silva@exemplo.com",
        "course": "Inglês Avançado",
        "active_until": iso_date_only(365)
    },
    {
        "id": generate_uuid(),
        "cpf_hash": hash_cpf("23456789012", CPF_HASH_SALT),
        "name": "Bruno Santos",
        "email": "bruno.santos@exemplo.com",
        "course": "Espanhol Intermediário",
        "active_until": iso_date_only(180)
    },
    {
        "id": generate_uuid(),
        "cpf_hash": hash_cpf("34567890123", CPF_HASH_SALT),
        "name": "Carla Oliveira",
        "email": "carla.oliveira@exemplo.com",
        "course": "Francês Básico",
        "active_until": iso_date_only(90)
    },
    {
        "id": generate_uuid(),
        "cpf_hash": hash_cpf("45678901234", CPF_HASH_SALT),
        "name": "Daniel Pereira",
        "email": "daniel.pereira@exemplo.com",
        "course": "Alemão Intermediário",
        "active_until": iso_date_only(270)
    },
    {
        "id": generate_uuid(),
        "cpf_hash": hash_cpf("56789012345", CPF_HASH_SALT),
        "name": "Eduarda Costa",
        "email": "eduarda.costa@exemplo.com",
        "course": "Italiano Básico",
        "active_until": iso_date_only(-30)  # Aluno com matrícula expirada
    }
]

partners = [
    {
        "id": generate_uuid(),
        "trade_name": "Livraria Cultura",
        "category": "Livraria",
        "address": "Av. Paulista, 2073 - São Paulo/SP",
        "active": True
    },
    {
        "id": generate_uuid(),
        "trade_name": "Restaurante Sabor & Arte",
        "category": "Alimentação",
        "address": "Rua Augusta, 1200 - São Paulo/SP",
        "active": True
    },
    {
        "id": generate_uuid(),
        "trade_name": "Cinema Lumière",
        "category": "Entretenimento",
        "address": "Shopping Cidade, Loja 42 - São Paulo/SP",
        "active": True
    }
]

# Gerar promoções (uma para cada parceiro + uma extra para o primeiro parceiro)
promotions = [
    {
        "id": generate_uuid(),
        "partner_id": partners[0]["id"],
        "title": "20% de desconto em livros de idiomas",
        "type": "discount",
        "valid_from": iso_date(-30),
        "valid_to": iso_date(60),
        "active": True
    },
    {
        "id": generate_uuid(),
        "partner_id": partners[0]["id"],
        "title": "Brinde exclusivo na compra acima de R$ 100",
        "type": "gift",
        "valid_from": iso_date(-15),
        "valid_to": iso_date(45),
        "active": True
    },
    {
        "id": generate_uuid(),
        "partner_id": partners[1]["id"],
        "title": "15% de desconto no almoço executivo",
        "type": "discount",
        "valid_from": iso_date(-10),
        "valid_to": iso_date(80),
        "active": True
    },
    {
        "id": generate_uuid(),
        "partner_id": partners[2]["id"],
        "title": "Ingresso com 30% de desconto nas segundas e terças",
        "type": "discount",
        "valid_from": iso_date(-5),
        "valid_to": iso_date(90),
        "active": True
    }
]

# Gerar alguns códigos de validação e resgates para demonstração
validation_codes = []
redemptions = []

# Criar alguns códigos para demonstração (2 usados, 1 expirado, 1 ativo)
for i in range(4):
    code_id = generate_uuid()
    student = random.choice(students[:4])  # Apenas alunos ativos
    partner = random.choice(partners)
    promotion = next((p for p in promotions if p["partner_id"] == partner["id"]), None)
    
    code = {
        "id": code_id,
        "student_id": student["id"],
        "partner_id": partner["id"],
        "code_hash": hashlib.sha256(f"{100000 + i}".encode()).hexdigest(),
        "expires": iso_date(0 if i < 3 else 1),  # O último código ainda está válido
        "used_at": iso_date(-1) if i < 2 else None  # Primeiros 2 códigos já usados
    }
    validation_codes.append(code)
    
    # Criar resgates para os códigos usados
    if i < 2 and promotion:
        redemption = {
            "id": generate_uuid(),
            "validation_code_id": code_id,
            "value": float(random.randint(10, 100)),
            "used_at": code["used_at"]
        }
        redemptions.append(redemption)

# Função para salvar dados em formato Firestore
def save_firestore_data():
    """Salva dados no formato de exportação do Firestore"""
    collections = {
        "students": students,
        "partners": partners,
        "promotions": promotions,
        "validation_codes": validation_codes,
        "redemptions": redemptions
    }
    
    # Criar estrutura de exportação do Firestore
    firestore_export = {}
    for collection_name, items in collections.items():
        firestore_export[f"__collection__/{collection_name}"] = {}
        for item in items:
            doc_id = item.pop("id")  # Remover ID do item e usar como chave do documento
            firestore_export[f"__collection__/{collection_name}/{doc_id}"] = {"data": item}
    
    # Salvar arquivo de exportação
    with open("firestore_export.json", "w") as f:
        json.dump(firestore_export, f, indent=2)
    
    print("Dados do Firestore salvos em firestore_export.json")

# Função para salvar dados em formato SQL
def save_sql_data():
    """Gera script SQL para PostgreSQL"""
    sql = []
    
    # Criar tabelas
    sql.append("""
-- Criar tabelas
CREATE TABLE IF NOT EXISTS students (
    id UUID PRIMARY KEY,
    cpf_hash TEXT NOT NULL,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    course TEXT NOT NULL,
    active_until DATE NOT NULL
);

CREATE TABLE IF NOT EXISTS partners (
    id UUID PRIMARY KEY,
    trade_name TEXT NOT NULL,
    category TEXT NOT NULL,
    address TEXT NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS promotions (
    id UUID PRIMARY KEY,
    partner_id UUID NOT NULL REFERENCES partners(id),
    title TEXT NOT NULL,
    type TEXT NOT NULL,
    valid_from TIMESTAMP NOT NULL,
    valid_to TIMESTAMP NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS validation_codes (
    id UUID PRIMARY KEY,
    student_id UUID NOT NULL REFERENCES students(id),
    partner_id UUID NOT NULL REFERENCES partners(id),
    code_hash TEXT NOT NULL,
    expires TIMESTAMP NOT NULL,
    used_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS redemptions (
    id UUID PRIMARY KEY,
    validation_code_id UUID NOT NULL REFERENCES validation_codes(id),
    value NUMERIC(10,2) NOT NULL,
    used_at TIMESTAMP NOT NULL
);

-- Limpar dados existentes
TRUNCATE TABLE redemptions CASCADE;
TRUNCATE TABLE validation_codes CASCADE;
TRUNCATE TABLE promotions CASCADE;
TRUNCATE TABLE partners CASCADE;
TRUNCATE TABLE students CASCADE;
    """)
    
    # Inserir estudantes
    for student in students:
        sql.append(f"""
INSERT INTO students (id, cpf_hash, name, email, course, active_until)
VALUES (
    '{student["id"]}',
    '{student["cpf_hash"]}',
    '{student["name"]}',
    '{student["email"]}',
    '{student["course"]}',
    '{student["active_until"]}'
);""")
    
    # Inserir parceiros
    for partner in partners:
        sql.append(f"""
INSERT INTO partners (id, trade_name, category, address, active)
VALUES (
    '{partner["id"]}',
    '{partner["trade_name"]}',
    '{partner["category"]}',
    '{partner["address"]}',
    {partner["active"]}
);""")
    
    # Inserir promoções
    for promotion in promotions:
        sql.append(f"""
INSERT INTO promotions (id, partner_id, title, type, valid_from, valid_to, active)
VALUES (
    '{promotion["id"]}',
    '{promotion["partner_id"]}',
    '{promotion["title"]}',
    '{promotion["type"]}',
    '{promotion["valid_from"]}',
    '{promotion["valid_to"]}',
    {promotion["active"]}
);""")
    
    # Inserir códigos de validação
    for code in validation_codes:
        used_at = f"'{code['used_at']}'" if code["used_at"] else "NULL"
        sql.append(f"""
INSERT INTO validation_codes (id, student_id, partner_id, code_hash, expires, used_at)
VALUES (
    '{code["id"]}',
    '{code["student_id"]}',
    '{code["partner_id"]}',
    '{code["code_hash"]}',
    '{code["expires"]}',
    {used_at}
);""")
    
    # Inserir resgates
    for redemption in redemptions:
        sql.append(f"""
INSERT INTO redemptions (id, validation_code_id, value, used_at)
VALUES (
    '{redemption["id"]}',
    '{redemption["validation_code_id"]}',
    {redemption["value"]},
    '{redemption["used_at"]}'
);""")
    
    # Salvar script SQL
    with open("seed_postgres.sql", "w") as f:
        f.write("\n".join(sql))
    
    print("Script SQL salvo em seed_postgres.sql")

# Função principal para executar o seed
def main():
    """Função principal para executar o seed de dados"""
    print("Iniciando seed de dados para o Portal de Benefícios KNN...")
    print(f"Gerando {len(students)} alunos, {len(partners)} parceiros e {len(promotions)} promoções...")
    
    # Salvar dados para Firestore
    save_firestore_data()
    
    # Salvar dados para PostgreSQL
    save_sql_data()
    
    # Salvar mapeamento de CPFs para facilitar testes
    cpf_mapping = {
        "12345678901": "Ana Silva",
        "23456789012": "Bruno Santos",
        "34567890123": "Carla Oliveira",
        "45678901234": "Daniel Pereira",
        "56789012345": "Eduarda Costa (expirado)"
    }
    
    with open("cpf_mapping.txt", "w") as f:
        f.write("CPF -> Nome (para testes)\n")
        f.write("----------------------\n")
        for cpf, name in cpf_mapping.items():
            f.write(f"{cpf} -> {name}\n")
    
    print("Mapeamento de CPFs salvo em cpf_mapping.txt")
    
    # Gerar arquivo de resumo
    with open("seed_summary.json", "w") as f:
        summary = {
            "students": len(students),
            "partners": len(partners),
            "promotions": len(promotions),
            "validation_codes": len(validation_codes),
            "redemptions": len(redemptions),
            "student_ids": [s["id"] for s in students],
            "partner_ids": [p["id"] for p in partners],
            "promotion_ids": [p["id"] for p in promotions]
        }
        json.dump(summary, f, indent=2)
    
    print("Resumo do seed salvo em seed_summary.json")
    print("Seed de dados concluído com sucesso!")

if __name__ == "__main__":
    main()
