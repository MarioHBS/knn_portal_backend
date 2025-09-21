#!/usr/bin/env python3
"""
Script para geração de dados de desenvolvimento/QA para o Portal de Benefícios KNN.
Cria 5 alunos, 3 parceiros e 4 promoções conforme solicitado.
"""

import hashlib
import json
import random
import uuid
from datetime import datetime, timedelta

# Configurações
FIRESTORE_EMULATOR_HOST = "localhost:8080"
CPF_HASH_SALT = "knn-dev-salt-2025"
DEFAULT_TENANT_ID = "knn-dev-tenant"


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
        "tenant_id": DEFAULT_TENANT_ID,
        "cpf_hash": hash_cpf("12345678901", CPF_HASH_SALT),
        "nome_aluno": "Ana Silva",
        "curso": "ADVANCED 1",
        "ocupacao_aluno": "Estudante",
        "email_aluno": "ana.silva@exemplo.com",
        "celular_aluno": "(11) 99999-1234",
        "cep_aluno": "01310-100",
        "bairro": "Bela Vista",
        "complemento_aluno": "Apto 101",
        "nome_responsavel": None,
        "email_responsavel": None,
        "active_until": iso_date_only(365),
    },
    {
        "id": generate_uuid(),
        "tenant_id": DEFAULT_TENANT_ID,
        "cpf_hash": hash_cpf("23456789012", CPF_HASH_SALT),
        "nome_aluno": "Bruno Santos",
        "curso": "TEENS 3",
        "ocupacao_aluno": "Estudante",
        "email_aluno": "bruno.santos@exemplo.com",
        "celular_aluno": "(11) 98888-5678",
        "cep_aluno": "04038-001",
        "bairro": "Vila Olímpia",
        "complemento_aluno": "Casa 15",
        "nome_responsavel": "Maria Santos",
        "email_responsavel": "maria.santos@exemplo.com",
        "active_until": iso_date_only(180),
    },
    {
        "id": generate_uuid(),
        "tenant_id": DEFAULT_TENANT_ID,
        "cpf_hash": hash_cpf("34567890123", CPF_HASH_SALT),
        "nome_aluno": "Carla Oliveira",
        "curso": "SEEDS 1",
        "ocupacao_aluno": "Professora",
        "email_aluno": "carla.oliveira@exemplo.com",
        "celular_aluno": "(11) 97777-9012",
        "cep_aluno": "05407-002",
        "bairro": "Pinheiros",
        "complemento_aluno": None,
        "nome_responsavel": None,
        "email_responsavel": None,
        "active_until": iso_date_only(90),
    },
    {
        "id": generate_uuid(),
        "tenant_id": DEFAULT_TENANT_ID,
        "cpf_hash": hash_cpf("45678901234", CPF_HASH_SALT),
        "nome_aluno": "Daniel Pereira",
        "curso": "TWEENS 4",
        "ocupacao_aluno": "Engenheiro",
        "email_aluno": "daniel.pereira@exemplo.com",
        "celular_aluno": "(11) 96666-3456",
        "cep_aluno": "01452-000",
        "bairro": "Jardins",
        "complemento_aluno": "Bloco B, Apto 502",
        "nome_responsavel": None,
        "email_responsavel": None,
        "active_until": iso_date_only(270),
    },
    {
        "id": generate_uuid(),
        "tenant_id": DEFAULT_TENANT_ID,
        "cpf_hash": hash_cpf("56789012345", CPF_HASH_SALT),
        "nome_aluno": "Eduarda Costa",
        "curso": "KINDER 6A",
        "ocupacao_aluno": "Estudante",
        "email_aluno": None,
        "celular_aluno": "(11) 95555-7890",
        "cep_aluno": "02011-000",
        "bairro": "Santana",
        "complemento_aluno": "Casa 22",
        "nome_responsavel": "Roberto Costa",
        "email_responsavel": "roberto.costa@exemplo.com",
        "active_until": iso_date_only(-30),  # Aluno com matrícula expirada
    },
]

partners = [
    {
        "id": generate_uuid(),
        "tenant_id": DEFAULT_TENANT_ID,
        "cnpj_hash": hashlib.sha256(f"12345678000195{CPF_HASH_SALT}".encode()).hexdigest(),
        "trade_name": "Livraria Cultura",
        "category": "Livraria",
        "address": "Av. Paulista, 2073 - São Paulo/SP",
        "active": True,
    },
    {
        "id": generate_uuid(),
        "tenant_id": DEFAULT_TENANT_ID,
        "cnpj_hash": hashlib.sha256(f"23456789000186{CPF_HASH_SALT}".encode()).hexdigest(),
        "trade_name": "Restaurante Sabor & Arte",
        "category": "Alimentação",
        "address": "Rua Augusta, 1200 - São Paulo/SP",
        "active": True,
    },
    {
        "id": generate_uuid(),
        "tenant_id": DEFAULT_TENANT_ID,
        "cnpj_hash": hashlib.sha256(f"34567890000177{CPF_HASH_SALT}".encode()).hexdigest(),
        "trade_name": "Cinema Lumière",
        "category": "Entretenimento",
        "address": "Shopping Cidade, Loja 42 - São Paulo/SP",
        "active": True,
    },
]

# Gerar promoções (uma para cada parceiro + uma extra para o primeiro parceiro)
promotions = [
    {
        "id": generate_uuid(),
        "tenant_id": DEFAULT_TENANT_ID,
        "partner_id": partners[0]["id"],
        "title": "20% de desconto em livros de idiomas",
        "type": "discount",
        "valid_from": iso_date(-30),
        "valid_to": iso_date(60),
        "active": True,
        "target_profile": "both",
    },
    {
        "id": generate_uuid(),
        "tenant_id": DEFAULT_TENANT_ID,
        "partner_id": partners[0]["id"],
        "title": "Brinde exclusivo na compra acima de R$ 100",
        "type": "gift",
        "valid_from": iso_date(-15),
        "valid_to": iso_date(45),
        "active": True,
        "target_profile": "student",
    },
    {
        "id": generate_uuid(),
        "tenant_id": DEFAULT_TENANT_ID,
        "partner_id": partners[1]["id"],
        "title": "15% de desconto no almoço executivo",
        "type": "discount",
        "valid_from": iso_date(-10),
        "valid_to": iso_date(80),
        "active": True,
        "target_profile": "employee",
    },
    {
        "id": generate_uuid(),
        "tenant_id": DEFAULT_TENANT_ID,
        "partner_id": partners[2]["id"],
        "title": "Ingresso com 30% de desconto nas segundas e terças",
        "type": "discount",
        "valid_from": iso_date(-5),
        "valid_to": iso_date(90),
        "active": True,
        "target_profile": "both",
    },
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
        "tenant_id": DEFAULT_TENANT_ID,
        "student_id": student["id"],
        "partner_id": partner["id"],
        "code_hash": hashlib.sha256(f"{100000 + i}".encode()).hexdigest(),
        "expires": iso_date(0 if i < 3 else 1),  # O último código ainda está válido
        "used_at": iso_date(-1) if i < 2 else None,  # Primeiros 2 códigos já usados
    }
    validation_codes.append(code)

    # Criar resgates para os códigos usados
    if i < 2 and promotion:
        redemption = {
            "id": generate_uuid(),
            "validation_code_id": code_id,
            "value": float(random.randint(10, 100)),
            "used_at": code["used_at"],
        }
        redemptions.append(redemption)


# Função para salvar dados em formato Firestore
def save_firestore_data():
    """Salva dados no formato de exportação do Firestore"""
    import copy

    collections = {
        "students": copy.deepcopy(students),
        "partners": copy.deepcopy(partners),
        "promotions": copy.deepcopy(promotions),
        "validation_codes": copy.deepcopy(validation_codes),
        "redemptions": copy.deepcopy(redemptions),
    }

    # Criar estrutura de exportação do Firestore
    firestore_export = {}
    for collection_name, items in collections.items():
        firestore_export[f"__collection__/{collection_name}"] = {}
        for item in items:
            doc_id = item.pop("id")  # Remover ID do item e usar como chave do documento
            firestore_export[f"__collection__/{collection_name}/{doc_id}"] = {
                "data": item
            }

    # Salvar arquivo de exportação
    with open("firestore_export.json", "w", encoding="utf-8") as f:
        json.dump(firestore_export, f, indent=2, ensure_ascii=False)

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
    tenant_id TEXT NOT NULL,
    cpf_hash TEXT NOT NULL,
    nome_aluno TEXT NOT NULL,
    curso TEXT NOT NULL,
    ocupacao_aluno TEXT,
    email_aluno TEXT,
    celular_aluno TEXT,
    cep_aluno TEXT,
    bairro TEXT,
    complemento_aluno TEXT,
    nome_responsavel TEXT,
    email_responsavel TEXT,
    active_until DATE NOT NULL
);

CREATE TABLE IF NOT EXISTS partners (
    id UUID PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    cnpj_hash TEXT NOT NULL,
    trade_name TEXT NOT NULL,
    category TEXT NOT NULL,
    address TEXT NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS promotions (
    id UUID PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    partner_id UUID NOT NULL REFERENCES partners(id),
    title TEXT NOT NULL,
    type TEXT NOT NULL,
    valid_from TIMESTAMP NOT NULL,
    valid_to TIMESTAMP NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    target_profile TEXT NOT NULL DEFAULT 'both'
);

CREATE TABLE IF NOT EXISTS validation_codes (
    id UUID PRIMARY KEY,
    tenant_id TEXT NOT NULL,
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
        ocupacao = f"'{student['ocupacao_aluno']}'" if student['ocupacao_aluno'] else 'NULL'
        email_aluno = f"'{student['email_aluno']}'" if student['email_aluno'] else 'NULL'
        celular = f"'{student['celular_aluno']}'" if student['celular_aluno'] else 'NULL'
        cep = f"'{student['cep_aluno']}'" if student['cep_aluno'] else 'NULL'
        bairro = f"'{student['bairro']}'" if student['bairro'] else 'NULL'
        complemento = f"'{student['complemento_aluno']}'" if student['complemento_aluno'] else 'NULL'
        nome_resp = f"'{student['nome_responsavel']}'" if student['nome_responsavel'] else 'NULL'
        email_resp = f"'{student['email_responsavel']}'" if student['email_responsavel'] else 'NULL'

        sql.append(f"""
INSERT INTO students (id, tenant_id, cpf_hash, nome_aluno, curso, ocupacao_aluno, email_aluno, celular_aluno, cep_aluno, bairro, complemento_aluno, nome_responsavel, email_responsavel, active_until)
VALUES (
    '{student["id"]}',
    '{student["tenant_id"]}',
    '{student["cpf_hash"]}',
    '{student["nome_aluno"]}',
    '{student["curso"]}',
    {ocupacao},
    {email_aluno},
    {celular},
    {cep},
    {bairro},
    {complemento},
    {nome_resp},
    {email_resp},
    '{student["active_until"]}'
);""")

    # Inserir parceiros
    for partner in partners:
        sql.append(f"""
INSERT INTO partners (id, tenant_id, cnpj_hash, trade_name, category, address, active)
VALUES (
    '{partner["id"]}',
    '{partner["tenant_id"]}',
    '{partner["cnpj_hash"]}',
    '{partner["trade_name"]}',
    '{partner["category"]}',
    '{partner["address"]}',
    {partner["active"]}
);""")

    # Inserir promoções
    for promotion in promotions:
        sql.append(f"""
INSERT INTO promotions (id, tenant_id, partner_id, title, type, valid_from, valid_to, active, target_profile)
VALUES (
    '{promotion["id"]}',
    '{promotion["tenant_id"]}',
    '{promotion["partner_id"]}',
    '{promotion["title"]}',
    '{promotion["type"]}',
    '{promotion["valid_from"]}',
    '{promotion["valid_to"]}',
    {promotion["active"]},
    '{promotion["target_profile"]}'
);""")

    # Inserir códigos de validação
    for code in validation_codes:
        used_at = f"'{code['used_at']}'" if code["used_at"] else "NULL"
        sql.append(f"""
INSERT INTO validation_codes (id, tenant_id, student_id, partner_id, code_hash, expires, used_at)
VALUES (
    '{code["id"]}',
    '{code["tenant_id"]}',
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
    with open("seed_postgres.sql", "w", encoding="utf-8") as f:
        f.write("\n".join(sql))

    print("Script SQL salvo em seed_postgres.sql")


# Função principal para executar o seed
def main():
    """Função principal para executar o seed de dados"""
    print("Iniciando seed de dados para o Portal de Benefícios KNN...")
    print(
        f"Gerando {len(students)} alunos, {len(partners)} parceiros e {len(promotions)} promoções..."
    )

    # Salvar dados para Firestore
    save_firestore_data()

    # Salvar dados para PostgreSQL
    save_sql_data()

    # Salvar mapeamento de CPFs para facilitar testes
    cpf_mapping = {
        "12345678901": "Ana Silva (ADVANCED 1)",
        "23456789012": "Bruno Santos (TEENS 3)",
        "34567890123": "Carla Oliveira (SEEDS 1)",
        "45678901234": "Daniel Pereira (TWEENS 4)",
        "56789012345": "Eduarda Costa (KINDER 6A - expirado)",
    }

    # Salvar mapeamento de CNPJs para facilitar testes
    cnpj_mapping = {
        "12345678000195": "Livraria Cultura",
        "23456789000186": "Restaurante Sabor & Arte",
        "34567890000177": "Cinema Lumière",
    }

    with open("cpf_mapping.txt", "w", encoding="utf-8") as f:
        f.write("CPF -> Nome e Curso (para testes)\n")
        f.write("----------------------------------\n")
        for cpf, name in cpf_mapping.items():
            f.write(f"{cpf} -> {name}\n")

    with open("cnpj_mapping.txt", "w", encoding="utf-8") as f:
        f.write("CNPJ -> Nome Fantasia (para testes)\n")
        f.write("------------------------------------\n")
        for cnpj, name in cnpj_mapping.items():
            f.write(f"{cnpj} -> {name}\n")

    print("Mapeamento de CPFs salvo em cpf_mapping.txt")
    print("Mapeamento de CNPJs salvo em cnpj_mapping.txt")

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
            "promotion_ids": [p["id"] for p in promotions],
        }
        json.dump(summary, f, indent=2)

    print("Resumo do seed salvo em seed_summary.json")
    print("Seed de dados concluído com sucesso!")


if __name__ == "__main__":
    main()
