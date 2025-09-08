#!/usr/bin/env python3
"""
Script para preparar dados de alunos e funcionários no formato Firestore.

Este script:
1. Carrega dados dos arquivos JSON existentes
2. Transforma os dados para o formato Firestore
3. Gera arquivos de importação para ambos os bancos
4. Cria estrutura compatível com o Firebase Admin SDK
"""

import json
import os
import sys
import uuid
from datetime import datetime, timedelta
from typing import Any

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils import logger


class FirestoreDataPreparator:
    """Classe para preparar dados no formato Firestore."""

    def __init__(self):
        self.tenant_id = "knn-dev-tenant"

    def transform_student_data(self, student: dict[str, Any]) -> dict[str, Any]:
        """Transforma dados do aluno para o formato Firestore."""
        # Calcular data de expiração (2 anos a partir de hoje)
        active_until = (datetime.now() + timedelta(days=730)).strftime("%Y-%m-%d")

        transformed = {
            "id": student.get("id", ""),
            "tenant_id": self.tenant_id,
            "nome": student.get("nome", ""),
            "livro": student.get("livro", ""),
            "ocupacao": student.get("ocupacao", ""),
            "e-mail": student.get("e-mail", ""),
            "telefone": str(student.get("telefone", "")),
            "cep": student.get("cep", ""),
            "bairro": student.get("bairro", ""),
            "complemento_aluno": student.get("complemento_aluno", ""),
            "nome_responsavel": student.get("nome_responsavel", "") or None,
            "e-mail_responsavel": student.get("e-mail_responsavel", "") or None,
            "active_until": active_until,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

        return transformed

    def transform_employee_data(self, employee: dict[str, Any]) -> dict[str, Any]:
        """Transforma dados do funcionário para o formato Firestore."""
        transformed = {
            "id": employee.get("id", ""),
            "tenant_id": self.tenant_id,
            "nome": employee.get("nome", ""),
            "cargo": employee.get("cargo", ""),
            "e-mail": employee.get("e-mail", ""),
            "telefone": str(employee.get("telefone", "")),
            "cep": employee.get("cep", ""),
            "active": True,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

        return transformed

    def create_firestore_export_format(
        self, students_data: list[dict], employees_data: list[dict]
    ) -> dict[str, Any]:
        """Cria estrutura no formato de exportação do Firestore."""
        firestore_export = {}

        # Adicionar coleção de estudantes
        firestore_export["__collection__/students"] = {}
        for student in students_data:
            doc_id = student.get("id", str(uuid.uuid4()))
            transformed_data = self.transform_student_data(student)
            firestore_export[f"__collection__/students/{doc_id}"] = {
                "data": transformed_data
            }

        # Adicionar coleção de funcionários
        firestore_export["__collection__/employees"] = {}
        for employee in employees_data:
            doc_id = employee.get("id", str(uuid.uuid4()))
            transformed_data = self.transform_employee_data(employee)
            firestore_export[f"__collection__/employees/{doc_id}"] = {
                "data": transformed_data
            }

        return firestore_export

    def create_batch_import_format(
        self, students_data: list[dict], employees_data: list[dict]
    ) -> dict[str, Any]:
        """Cria estrutura para importação em lote."""
        batch_data = {"students": [], "employees": []}

        # Processar estudantes
        for student in students_data:
            doc_id = student.get("id", str(uuid.uuid4()))
            transformed_data = self.transform_student_data(student)
            batch_data["students"].append({"id": doc_id, "data": transformed_data})

        # Processar funcionários
        for employee in employees_data:
            doc_id = employee.get("id", str(uuid.uuid4()))
            transformed_data = self.transform_employee_data(employee)
            batch_data["employees"].append({"id": doc_id, "data": transformed_data})

        return batch_data

    def load_json_data(self, file_path: str) -> dict[str, Any]:
        """Carrega dados de um arquivo JSON."""
        try:
            with open(file_path, encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Erro ao carregar arquivo {file_path}: {str(e)}")
            raise

    def save_json_data(self, data: dict[str, Any], file_path: str):
        """Salva dados em um arquivo JSON."""
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"Dados salvos em: {file_path}")
        except Exception as e:
            logger.error(f"Erro ao salvar arquivo {file_path}: {str(e)}")
            raise

    def generate_import_script(self, output_dir: str):
        """Gera script Python para importação dos dados."""
        script_content = '''#!/usr/bin/env python3
"""
Script gerado automaticamente para importar dados no Firestore.

Uso:
1. Configure as credenciais do Firebase
2. Execute: python import_to_firestore.py
"""

import json
import os
import firebase_admin
from firebase_admin import credentials, firestore

def import_data_to_firestore(project_id: str, data_file: str):
    """Importa dados para o Firestore."""
    # Inicializar Firebase
    if not firebase_admin._apps:
        try:
            cred = credentials.ApplicationDefault()
            app = firebase_admin.initialize_app(cred, {"projectId": project_id})
        except:
            app = firebase_admin.initialize_app(options={"projectId": project_id})

    db = firestore.client()

    # Carregar dados
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Importar estudantes
    students = data.get('students', [])
    print(f"Importando {len(students)} estudantes...")

    batch = db.batch()
    batch_count = 0

    for student in students:
        doc_ref = db.collection('students').document(student['id'])
        batch.set(doc_ref, student['data'])
        batch_count += 1

        if batch_count >= 500:
            batch.commit()
            batch = db.batch()
            batch_count = 0

    if batch_count > 0:
        batch.commit()

    # Importar funcionários
    employees = data.get('employees', [])
    print(f"Importando {len(employees)} funcionários...")

    batch = db.batch()
    batch_count = 0

    for employee in employees:
        doc_ref = db.collection('employees').document(employee['id'])
        batch.set(doc_ref, employee['data'])
        batch_count += 1

        if batch_count >= 500:
            batch.commit()
            batch = db.batch()
            batch_count = 0

    if batch_count > 0:
        batch.commit()

    print(f"Importação concluída: {len(students)} estudantes, {len(employees)} funcionários")

if __name__ == "__main__":
    # Configurar os projetos
    projects = {
        "default": "knn-portal-dev",
        "production": "knn-benefits"
    }

    for env, project_id in projects.items():
        print(f"\\n=== Importando para {env} ({project_id}) ===")
        try:
            import_data_to_firestore(project_id, f"firestore_data_{env}.json")
        except Exception as e:
            print(f"Erro na importação para {env}: {str(e)}")
'''

        script_path = os.path.join(output_dir, "import_to_firestore.py")
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(script_content)

        logger.info(f"Script de importação gerado: {script_path}")

    def run_preparation(self):
        """Executa a preparação completa dos dados."""
        logger.info("=== Iniciando Preparação de Dados para Firestore ===")

        # Carregar dados dos arquivos JSON
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        students_file = os.path.join(base_dir, "sources", "dados_alunos.json")
        employees_file = os.path.join(base_dir, "sources", "dados_funcionarios.json")

        logger.info("Carregando dados dos arquivos JSON...")
        students_data = self.load_json_data(students_file)
        employees_data = self.load_json_data(employees_file)

        students_list = students_data.get("alunos", [])
        employees_list = employees_data.get("funcionarios", [])

        logger.info(
            f"Dados carregados: {len(students_list)} alunos, {len(employees_list)} funcionários"
        )

        # Criar diretório de saída
        output_dir = os.path.join(base_dir, "data", "firestore_import")
        os.makedirs(output_dir, exist_ok=True)

        # Gerar dados no formato de exportação do Firestore
        logger.info("Gerando dados no formato de exportação do Firestore...")
        firestore_export = self.create_firestore_export_format(
            students_list, employees_list
        )

        # Gerar dados no formato de importação em lote
        logger.info("Gerando dados no formato de importação em lote...")
        batch_data = self.create_batch_import_format(students_list, employees_list)

        # Salvar arquivos para ambos os bancos
        databases = ["default", "production"]

        for db_name in databases:
            # Formato de exportação
            export_file = os.path.join(output_dir, f"firestore_export_{db_name}.json")
            self.save_json_data(firestore_export, export_file)

            # Formato de importação em lote
            batch_file = os.path.join(output_dir, f"firestore_data_{db_name}.json")
            self.save_json_data(batch_data, batch_file)

        # Gerar script de importação
        self.generate_import_script(output_dir)

        # Gerar relatório
        report = {
            "timestamp": datetime.now().isoformat(),
            "students_count": len(students_list),
            "employees_count": len(employees_list),
            "databases": databases,
            "files_generated": [f"firestore_export_{db}.json" for db in databases]
            + [f"firestore_data_{db}.json" for db in databases]
            + ["import_to_firestore.py"],
            "next_steps": [
                "1. Configure as credenciais do Firebase para os projetos",
                "2. Execute o script import_to_firestore.py",
                "3. Ou importe manualmente os arquivos firestore_export_*.json no console do Firebase",
            ],
        }

        # Salvar relatório no diretório de relatórios
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        reports_dir = os.path.join(project_root, "reports")
        os.makedirs(reports_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = os.path.join(reports_dir, f"migration_report_{timestamp}.json")
        self.save_json_data(report, report_file)

        logger.info("\n=== Preparação Concluída ===")
        logger.info(f"Arquivos gerados em: {output_dir}")
        logger.info(f"Estudantes processados: {len(students_list)}")
        logger.info(f"Funcionários processados: {len(employees_list)}")
        logger.info("\nPróximos passos:")
        logger.info("1. Configure as credenciais do Firebase")
        logger.info("2. Execute: python data/firestore_import/import_to_firestore.py")
        logger.info("3. Ou importe manualmente no console do Firebase")


def main():
    """Função principal do script."""
    preparator = FirestoreDataPreparator()

    try:
        preparator.run_preparation()
    except Exception as e:
        logger.error(f"Erro durante a preparação: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
