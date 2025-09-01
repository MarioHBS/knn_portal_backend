#!/usr/bin/env python3
"""
Script para migrar dados de alunos e funcionários dos arquivos JSON para os bancos Firestore.

Este script:
1. Conecta aos bancos Firestore (default e knn-benefits)
2. Migra dados de alunos do arquivo dados_alunos.json
3. Migra dados de funcionários do arquivo dados_funcionarios.json
4. Mantém a estrutura multi-tenant do projeto
5. Aplica transformações necessárias nos dados
"""

import hashlib
import json
import os
import sys
import uuid
from datetime import datetime, timedelta
from typing import Any

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import firebase_admin
from firebase_admin import credentials, firestore

from src.config import FB_PROJECT_ID, FIRESTORE_PROJECT
from src.utils import logger


class FirestoreMigrator:
    """Classe para migração de dados para múltiplos bancos Firestore."""

    def __init__(self):
        self.databases = {}
        self.tenant_id = "knn-dev-tenant"

    def initialize_databases(self):
        """Inicializa conexões com os bancos Firestore."""
        try:
            # Banco padrão (default)
            if not firebase_admin._apps:
                try:
                    # Tentar credenciais padrão primeiro
                    cred = credentials.ApplicationDefault()
                    default_app = firebase_admin.initialize_app(
                        cred,
                        {
                            "projectId": FIRESTORE_PROJECT,
                        },
                        name="default",
                    )
                except Exception as cred_error:
                    logger.warning(
                        f"Credenciais padrão não encontradas: {str(cred_error)}"
                    )
                    logger.info("Tentando inicializar sem credenciais (modo emulador)")
                    # Inicializar sem credenciais para emulador
                    default_app = firebase_admin.initialize_app(
                        options={
                            "projectId": FIRESTORE_PROJECT,
                        },
                        name="default",
                    )
            else:
                default_app = firebase_admin.get_app("default")

            self.databases["default"] = firestore.client(app=default_app)
            logger.info(f"Conectado ao banco default: {FIRESTORE_PROJECT}")

            # Banco de produção (knn-benefits)
            if FB_PROJECT_ID != FIRESTORE_PROJECT:
                try:
                    prod_app = firebase_admin.initialize_app(
                        credentials.ApplicationDefault(),
                        {
                            "projectId": FB_PROJECT_ID,
                        },
                        name="production",
                    )
                except Exception as cred_error:
                    logger.warning(
                        f"Credenciais para produção não encontradas: {str(cred_error)}"
                    )
                    logger.info(
                        "Tentando inicializar produção sem credenciais (modo emulador)"
                    )
                    prod_app = firebase_admin.initialize_app(
                        options={
                            "projectId": FB_PROJECT_ID,
                        },
                        name="production",
                    )

                self.databases["production"] = firestore.client(app=prod_app)
                logger.info(f"Conectado ao banco production: {FB_PROJECT_ID}")
            else:
                logger.info("Usando o mesmo projeto para ambos os bancos")
                self.databases["production"] = self.databases["default"]

        except Exception as e:
            logger.error(f"Erro ao inicializar bancos Firestore: {str(e)}")
            raise

    def hash_cpf(self, cpf: str) -> str:
        """Gera hash do CPF para segurança."""
        if not cpf:
            return ""
        # Remove caracteres não numéricos
        cpf_clean = "".join(filter(str.isdigit, cpf))
        return hashlib.sha256(cpf_clean.encode()).hexdigest()

    def hash_cnpj(self, cnpj: str) -> str:
        """Gera hash do CNPJ para segurança."""
        if not cnpj:
            return ""
        # Remove caracteres não numéricos
        cnpj_clean = "".join(filter(str.isdigit, cnpj))
        return hashlib.sha256(cnpj_clean.encode()).hexdigest()

    def transform_student_data(self, student: dict[str, Any]) -> dict[str, Any]:
        """Transforma dados do aluno para o formato Firestore."""
        # Gerar CPF fictício baseado no ID para hash
        fake_cpf = f"000{hash(student['id']) % 100000000:08d}"[:11]

        # Calcular data de expiração (1 ano a partir de hoje)
        active_until = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d")

        transformed = {
            "tenant_id": self.tenant_id,
            "cpf_hash": self.hash_cpf(fake_cpf),
            "nome_aluno": student.get("nome", ""),
            "curso": student.get("livro", ""),
            "ocupacao_aluno": student.get("ocupacao", ""),
            "email_aluno": student.get("e-mail", ""),
            "celular_aluno": str(student.get("telefone", "")),
            "cep_aluno": student.get("cep", ""),
            "bairro": student.get("bairro", ""),
            "complemento_aluno": student.get("complemento_aluno", ""),
            "nome_responsavel": student.get("nome_responsavel", "") or None,
            "email_responsavel": student.get("e-mail_responsavel", "") or None,
            "active_until": active_until,
            "created_at": firestore.SERVER_TIMESTAMP,
            "updated_at": firestore.SERVER_TIMESTAMP,
        }

        return transformed

    def transform_employee_data(self, employee: dict[str, Any]) -> dict[str, Any]:
        """Transforma dados do funcionário para o formato Firestore."""
        # Gerar CPF fictício baseado no ID para hash
        fake_cpf = f"111{hash(employee['id']) % 100000000:08d}"[:11]

        transformed = {
            "tenant_id": self.tenant_id,
            "cpf_hash": self.hash_cpf(fake_cpf),
            "nome_funcionario": employee.get("nome", ""),
            "cargo": employee.get("cargo", ""),
            "email_funcionario": employee.get("e-mail", ""),
            "telefone_funcionario": str(employee.get("telefone", "")),
            "cep_funcionario": employee.get("cep", ""),
            "active": True,
            "created_at": firestore.SERVER_TIMESTAMP,
            "updated_at": firestore.SERVER_TIMESTAMP,
        }

        return transformed

    def migrate_students(
        self, database_name: str, students_data: list[dict[str, Any]]
    ) -> int:
        """Migra dados de alunos para o Firestore."""
        db = self.databases[database_name]
        migrated_count = 0

        logger.info(
            f"Iniciando migração de {len(students_data)} alunos para {database_name}"
        )

        batch = db.batch()
        batch_count = 0

        for student in students_data:
            try:
                # Usar o ID original ou gerar um novo UUID
                doc_id = student.get("id", str(uuid.uuid4()))

                # Transformar dados
                transformed_data = self.transform_student_data(student)

                # Adicionar ao batch
                doc_ref = db.collection("students").document(doc_id)
                batch.set(doc_ref, transformed_data)

                batch_count += 1
                migrated_count += 1

                # Executar batch a cada 500 documentos (limite do Firestore)
                if batch_count >= 500:
                    batch.commit()
                    batch = db.batch()
                    batch_count = 0
                    logger.info(f"Migrados {migrated_count} alunos...")

            except Exception as e:
                logger.error(
                    f"Erro ao migrar aluno {student.get('nome', 'N/A')}: {str(e)}"
                )
                continue

        # Executar batch final
        if batch_count > 0:
            batch.commit()

        logger.info(
            f"Migração de alunos concluída: {migrated_count} registros em {database_name}"
        )
        return migrated_count

    def migrate_employees(
        self, database_name: str, employees_data: list[dict[str, Any]]
    ) -> int:
        """Migra dados de funcionários para o Firestore."""
        db = self.databases[database_name]
        migrated_count = 0

        logger.info(
            f"Iniciando migração de {len(employees_data)} funcionários para {database_name}"
        )

        batch = db.batch()
        batch_count = 0

        for employee in employees_data:
            try:
                # Usar o ID original ou gerar um novo UUID
                doc_id = employee.get("id", str(uuid.uuid4()))

                # Transformar dados
                transformed_data = self.transform_employee_data(employee)

                # Adicionar ao batch
                doc_ref = db.collection("employees").document(doc_id)
                batch.set(doc_ref, transformed_data)

                batch_count += 1
                migrated_count += 1

                # Executar batch a cada 500 documentos
                if batch_count >= 500:
                    batch.commit()
                    batch = db.batch()
                    batch_count = 0
                    logger.info(f"Migrados {migrated_count} funcionários...")

            except Exception as e:
                logger.error(
                    f"Erro ao migrar funcionário {employee.get('nome', 'N/A')}: {str(e)}"
                )
                continue

        # Executar batch final
        if batch_count > 0:
            batch.commit()

        logger.info(
            f"Migração de funcionários concluída: {migrated_count} registros em {database_name}"
        )
        return migrated_count

    def load_json_data(self, file_path: str) -> dict[str, Any]:
        """Carrega dados de um arquivo JSON."""
        try:
            with open(file_path, encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Erro ao carregar arquivo {file_path}: {str(e)}")
            raise

    def run_migration(self, databases_to_migrate: list[str] = None):
        """Executa a migração completa."""
        if databases_to_migrate is None:
            databases_to_migrate = ["default", "production"]

        # Inicializar conexões
        self.initialize_databases()

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

        # Migrar para cada banco
        for db_name in databases_to_migrate:
            if db_name not in self.databases:
                logger.warning(f"Banco {db_name} não disponível, pulando...")
                continue

            logger.info(f"\n=== Migrando para {db_name} ===")

            # Migrar alunos
            students_migrated = self.migrate_students(db_name, students_list)

            # Migrar funcionários
            employees_migrated = self.migrate_employees(db_name, employees_list)

            logger.info(
                f"Migração para {db_name} concluída: {students_migrated} alunos, {employees_migrated} funcionários"
            )

    def validate_migration(self, database_name: str) -> dict[str, int]:
        """Valida se a migração foi bem-sucedida."""
        db = self.databases[database_name]

        try:
            # Contar documentos nas coleções
            students_count = len(list(db.collection("students").limit(1000).stream()))
            employees_count = len(list(db.collection("employees").limit(1000).stream()))

            logger.info(
                f"Validação {database_name}: {students_count} alunos, {employees_count} funcionários"
            )

            return {"students": students_count, "employees": employees_count}
        except Exception as e:
            logger.error(f"Erro na validação do banco {database_name}: {str(e)}")
            return {"students": 0, "employees": 0}


def main():
    """Função principal do script."""
    logger.info("=== Iniciando Migração de Dados para Firestore ===")

    migrator = FirestoreMigrator()

    try:
        # Executar migração
        migrator.run_migration()

        # Validar migração
        logger.info("\n=== Validando Migração ===")
        for db_name in migrator.databases.keys():
            migrator.validate_migration(db_name)

        logger.info("\n=== Migração Concluída com Sucesso ===")

    except Exception as e:
        logger.error(f"Erro durante a migração: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
