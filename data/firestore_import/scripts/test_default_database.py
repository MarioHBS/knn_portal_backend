#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de teste para validar dados no banco Firestore (default)
Testa regras de negócio, integridade dos dados e funcionalidades básicas
"""

import os
import re
from datetime import datetime
from google.cloud import firestore
from google.oauth2 import service_account

# Configurações
PROJECT_ID = "knn-benefits"
DATABASE_ID = "(default)"
SERVICE_ACCOUNT_KEY = "default-service-account-key.json"

def get_firestore_client():
    """Inicializa cliente Firestore para o banco (default)"""
    try:
        # Carrega credenciais da conta de serviço
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_KEY
        )
        
        # Inicializa cliente Firestore
        client = firestore.Client(
            project=PROJECT_ID,
            database=DATABASE_ID,
            credentials=credentials
        )
        
        print(f"✅ Conectado ao Firestore - Projeto: {PROJECT_ID}, Banco: {DATABASE_ID}")
        return client
        
    except Exception as e:
        print(f"❌ Erro ao conectar ao Firestore: {e}")
        return None

def validate_email(email):
    """Valida formato de email"""
    if not email:
        return True  # Email vazio é permitido
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_cep(cep):
    """Valida formato de CEP brasileiro (XXXXX-XXX)"""
    if not cep:
        return True  # CEP vazio é permitido
    
    pattern = r'^\d{5}-\d{3}$'
    return re.match(pattern, cep) is not None

def validate_phone(phone):
    """Valida formato de telefone brasileiro"""
    if not phone:
        return True  # Telefone vazio é permitido
    
    # Remove espaços e caracteres especiais
    clean_phone = re.sub(r'[^\d]', '', phone)
    
    # Telefone deve ter 10 ou 11 dígitos
    return len(clean_phone) in [10, 11]

def calculate_age(birth_date):
    """Calcula idade a partir da data de nascimento"""
    try:
        if isinstance(birth_date, str):
            # Tenta diferentes formatos de data
            for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y']:
                try:
                    birth = datetime.strptime(birth_date, fmt)
                    break
                except ValueError:
                    continue
            else:
                return None
        else:
            birth = birth_date
        
        today = datetime.now()
        age = today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
        return age
    except:
        return None

def test_students_data(client):
    """Testa dados dos estudantes"""
    print("\n🔍 Testando dados dos estudantes...")
    
    students_ref = client.collection('students')
    students = students_ref.stream()
    
    total_students = 0
    minors_without_guardian = []
    invalid_emails = []
    invalid_ceps = []
    invalid_phones = []
    missing_courses = []
    
    for student in students:
        total_students += 1
        data = student.to_dict()
        student_id = student.id
        
        # Verifica se menor de idade tem responsável
        age = calculate_age(data.get('data_nascimento'))
        if age and age < 18:
            if not data.get('nome_responsavel'):
                minors_without_guardian.append({
                    'id': student_id,
                    'nome': data.get('nome', 'N/A'),
                    'idade': age
                })
        
        # Valida email
        email = data.get('email')
        if email and not validate_email(email):
            invalid_emails.append({
                'id': student_id,
                'nome': data.get('nome', 'N/A'),
                'email': email
            })
        
        # Valida CEP
        cep = data.get('cep')
        if cep and not validate_cep(cep):
            invalid_ceps.append({
                'id': student_id,
                'nome': data.get('nome', 'N/A'),
                'cep': cep
            })
        
        # Valida telefone
        telefone = data.get('telefone')
        if telefone and not validate_phone(telefone):
            invalid_phones.append({
                'id': student_id,
                'nome': data.get('nome', 'N/A'),
                'telefone': telefone
            })
        
        # Verifica se livro está preenchido
        livro = data.get('livro')
        if not livro:
            missing_courses.append({
                'id': student_id,
                'nome': data.get('nome', 'N/A')
            })
    
    # Relatório dos estudantes
    print(f"📊 Total de estudantes: {total_students}")
    
    if minors_without_guardian:
        print(f"⚠️  Menores sem responsável: {len(minors_without_guardian)}")
        for minor in minors_without_guardian[:5]:  # Mostra apenas os primeiros 5
            print(f"   - {minor['nome']} (ID: {minor['id']}, Idade: {minor['idade']})")
    else:
        print("✅ Todos os menores têm responsável definido")
    
    if invalid_emails:
        print(f"⚠️  Emails inválidos: {len(invalid_emails)}")
        for email in invalid_emails[:5]:
            print(f"   - {email['nome']}: {email['email']}")
    else:
        print("✅ Todos os emails estão em formato válido")
    
    if invalid_ceps:
        print(f"⚠️  CEPs inválidos: {len(invalid_ceps)}")
        for cep in invalid_ceps[:5]:
            print(f"   - {cep['nome']}: {cep['cep']}")
    else:
        print("✅ Todos os CEPs estão em formato válido")
    
    if invalid_phones:
        print(f"⚠️  Telefones inválidos: {len(invalid_phones)}")
        for phone in invalid_phones[:5]:
            print(f"   - {phone['nome']}: {phone['telefone']}")
    else:
        print("✅ Todos os telefones estão em formato válido")
    
    if missing_courses:
        print(f"⚠️  Estudantes sem livro: {len(missing_courses)}")
        for student in missing_courses[:5]:
            print(f"   - {student['nome']} (ID: {student['id']})")
    else:
        print("✅ Todos os estudantes têm livro definido")
    
    return {
        'total': total_students,
        'minors_without_guardian': len(minors_without_guardian),
        'invalid_emails': len(invalid_emails),
        'invalid_ceps': len(invalid_ceps),
        'invalid_phones': len(invalid_phones),
        'missing_courses': len(missing_courses)
    }

def test_employees_data(client):
    """Testa dados dos funcionários"""
    print("\n🔍 Testando dados dos funcionários...")
    
    employees_ref = client.collection('employees')
    employees = employees_ref.stream()
    
    total_employees = 0
    invalid_emails = []
    invalid_ceps = []
    invalid_phones = []
    missing_departments = []
    
    for employee in employees:
        total_employees += 1
        data = employee.to_dict()
        employee_id = employee.id
        
        # Valida email
        email = data.get('email')
        if email and not validate_email(email):
            invalid_emails.append({
                'id': employee_id,
                'nome': data.get('nome', 'N/A'),
                'email': email
            })
        
        # Valida CEP
        cep = data.get('cep')
        if cep and not validate_cep(cep):
            invalid_ceps.append({
                'id': employee_id,
                'nome': data.get('nome', 'N/A'),
                'cep': cep
            })
        
        # Valida telefone
        telefone = data.get('telefone')
        if telefone and not validate_phone(telefone):
            invalid_phones.append({
                'id': employee_id,
                'nome': data.get('nome', 'N/A'),
                'telefone': telefone
            })
        
        # Verifica se cargo está preenchido
        cargo = data.get('cargo')
        if not cargo:
            missing_departments.append({
                'id': employee_id,
                'nome': data.get('nome', 'N/A')
            })
    
    # Relatório dos funcionários
    print(f"📊 Total de funcionários: {total_employees}")
    
    if invalid_emails:
        print(f"⚠️  Emails inválidos: {len(invalid_emails)}")
        for email in invalid_emails[:5]:
            print(f"   - {email['nome']}: {email['email']}")
    else:
        print("✅ Todos os emails estão em formato válido")
    
    if invalid_ceps:
        print(f"⚠️  CEPs inválidos: {len(invalid_ceps)}")
        for cep in invalid_ceps[:5]:
            print(f"   - {cep['nome']}: {cep['cep']}")
    else:
        print("✅ Todos os CEPs estão em formato válido")
    
    if invalid_phones:
        print(f"⚠️  Telefones inválidos: {len(invalid_phones)}")
        for phone in invalid_phones[:5]:
            print(f"   - {phone['nome']}: {phone['telefone']}")
    else:
        print("✅ Todos os telefones estão em formato válido")
    
    if missing_departments:
        print(f"⚠️  Funcionários sem cargo: {len(missing_departments)}")
        for emp in missing_departments[:5]:
            print(f"   - {emp['nome']} (ID: {emp['id']})")
    else:
        print("✅ Todos os funcionários têm cargo definido")
    
    return {
        'total': total_employees,
        'invalid_emails': len(invalid_emails),
        'invalid_ceps': len(invalid_ceps),
        'invalid_phones': len(invalid_phones),
        'missing_departments': len(missing_departments)
    }

def test_database_operations(client):
    """Testa operações básicas do banco"""
    print("\n🔍 Testando operações do banco...")
    
    try:
        # Teste de leitura
        collections = client.collections()
        collection_names = [col.id for col in collections]
        print(f"✅ Coleções encontradas: {collection_names}")
        
        # Teste de contagem
        students_count = len(list(client.collection('students').stream()))
        employees_count = len(list(client.collection('employees').stream()))
        
        print(f"✅ Contagem - Estudantes: {students_count}, Funcionários: {employees_count}")
        
        # Teste de consulta simples
        first_student = next(client.collection('students').limit(1).stream(), None)
        if first_student:
            print(f"✅ Consulta de exemplo - Primeiro estudante: {first_student.to_dict().get('nome', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro nas operações do banco: {e}")
        return False

def main():
    """Função principal de teste"""
    print("🚀 Iniciando testes do banco Firestore (default)")
    print("=" * 50)
    
    # Conecta ao Firestore
    client = get_firestore_client()
    if not client:
        return
    
    # Executa testes
    try:
        # Testa operações básicas
        if not test_database_operations(client):
            return
        
        # Testa dados dos estudantes
        students_results = test_students_data(client)
        
        # Testa dados dos funcionários
        employees_results = test_employees_data(client)
        
        # Resumo final
        print("\n" + "=" * 50)
        print("📋 RESUMO DOS TESTES")
        print("=" * 50)
        
        print(f"📊 Estudantes: {students_results['total']} registros")
        print(f"📊 Funcionários: {employees_results['total']} registros")
        
        total_issues = (
            students_results['minors_without_guardian'] +
            students_results['invalid_emails'] +
            students_results['invalid_ceps'] +
            students_results['invalid_phones'] +
            students_results['missing_courses'] +
            employees_results['invalid_emails'] +
            employees_results['invalid_ceps'] +
            employees_results['invalid_phones'] +
            employees_results['missing_departments']
        )
        
        if total_issues == 0:
            print("\n🎉 TODOS OS TESTES PASSARAM! Dados estão íntegros e seguem as regras de negócio.")
        else:
            print(f"\n⚠️  ENCONTRADOS {total_issues} PROBLEMAS nos dados. Verifique os detalhes acima.")
        
        print("\n✅ Testes concluídos com sucesso!")
        
    except Exception as e:
        print(f"\n❌ Erro durante os testes: {e}")

if __name__ == "__main__":
    main()