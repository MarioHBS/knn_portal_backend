import unittest
from datetime import date

from src.models import Employee, Partner
from src.models.student import Student


class TestModelsIntegration(unittest.TestCase):
    """Testes de integração dos modelos com os algoritmos de criação de IDs."""

    def test_student_id_generation(self):
        """Testa geração automática de ID para aluno."""
        student = Student(
            tenant_id="tenant_123",
            cpf_hash="hash_123",
            student_name="João Silva Santos",
            book="KIDS 1",
            student_occupation="Estudante",
            student_email="joao@email.com",
            student_phone="(11) 99999-9999",
            zip="12345-678",
            add_neighbor="Centro",
            active_until=date(2024, 12, 31),
        )

        # Verifica se o ID foi gerado automaticamente
        self.assertIsNotNone(student.id)
        self.assertTrue(student.id.startswith("STD_"))
        self.assertTrue(student.id.endswith("_K1"))
        self.assertEqual(len(student.id), 15)

    def test_student_with_existing_id(self):
        """Testa que ID existente não é sobrescrito."""
        existing_id = "STD_CUSTOM123_K1"
        student = Student(
            id=existing_id,
            tenant_id="tenant_123",
            cpf_hash="hash_123",
            student_name="João Silva Santos",
            book="KIDS 1",
            active_until=date(2024, 12, 31),
        )

        # Verifica se o ID existente foi mantido
        self.assertEqual(student.id, existing_id)

    def test_employee_id_generation(self):
        """Testa geração automática de ID para funcionário."""
        employee = Employee(
            tenant_id="tenant_123",
            cpf_hash="hash_456",
            name="Maria Oliveira",
            email="maria@empresa.com",
            department="PROFESSORA",
            cep="54321-876",
            telefone="(21) 88888-8888",
            active=True,
        )

        # Verifica se o ID foi gerado automaticamente
        self.assertIsNotNone(employee.id)
        self.assertTrue(employee.id.startswith("EMP_"))
        self.assertTrue(employee.id.endswith("_PR"))
        self.assertEqual(len(employee.id), 15)

    def test_employee_with_existing_id(self):
        """Testa que ID existente não é sobrescrito para funcionário."""
        existing_id = "EMP_CUSTOM123_PR"
        employee = Employee(
            id=existing_id,
            tenant_id="tenant_123",
            cpf_hash="hash_456",
            name="Maria Oliveira",
            email="maria@empresa.com",
            department="PROFESSORA",
        )

        # Verifica se o ID existente foi mantido
        self.assertEqual(employee.id, existing_id)

    def test_partner_id_generation(self):
        """Testa geração automática de ID para parceiro."""
        partner = Partner(
            tenant_id="tenant_123",
            cnpj_hash="hash_789",
            cnpj="12.345.678/0001-90",
            trade_name="Empresa ABC Ltda",
            category="TECNOLOGIA",
            address="Rua das Flores, 123",
            active=True,
        )

        # Verifica se o ID foi gerado automaticamente
        self.assertIsNotNone(partner.id)
        self.assertTrue(partner.id.startswith("PTN_"))
        self.assertTrue(partner.id.endswith("_TEC"))
        self.assertEqual(len(partner.id), 15)

    def test_partner_without_cnpj_fallback(self):
        """Testa fallback para UUID quando não há CNPJ."""
        partner = Partner(
            tenant_id="tenant_123",
            cnpj_hash="hash_789",
            trade_name="Empresa ABC Ltda",
            category="TECNOLOGIA",
            address="Rua das Flores, 123",
            active=True,
        )

        # Verifica se foi usado UUID como fallback
        self.assertIsNotNone(partner.id)
        # UUID tem 36 caracteres com hífens
        self.assertEqual(len(partner.id), 36)
        self.assertIn("-", partner.id)

    def test_partner_with_existing_id(self):
        """Testa que ID existente não é sobrescrito para parceiro."""
        existing_id = "PTN_CUSTOM1_TEC"
        partner = Partner(
            id=existing_id,
            tenant_id="tenant_123",
            cnpj_hash="hash_789",
            cnpj="12.345.678/0001-90",
            trade_name="Empresa ABC Ltda",
            category="TECNOLOGIA",
            address="Rua das Flores, 123",
        )

        # Verifica se o ID existente foi mantido
        self.assertEqual(partner.id, existing_id)

    def test_student_different_courses(self):
        """Testa geração de IDs para diferentes cursos."""
        courses = ["KIDS 1", "TEENS 2", "ADVANCED 1"]
        expected_suffixes = ["_K1", "_T2", "_A1"]

        for curso, suffix in zip(courses, expected_suffixes, strict=False):
            student = Student(
                tenant_id="tenant_123",
                cpf_hash="hash_123",
                student_name="Aluno Teste",
                book=curso,
                active_until=date(2024, 12, 31),
            )

            self.assertTrue(student.id.endswith(suffix))

    def test_employee_different_departments(self):
        """Testa geração de IDs para diferentes cargos."""
        departments = ["PROFESSORA", "CDA", "ADM. FINANCEIRO"]
        expected_suffixes = ["_PR", "_CDA", "_AF"]

        for dept, suffix in zip(departments, expected_suffixes, strict=False):
            employee = Employee(
                tenant_id="tenant_123",
                cpf_hash="hash_456",
                name="Funcionario Teste",
                email="teste@empresa.com",
                department=dept,
            )

            self.assertTrue(employee.id.endswith(suffix))

    def test_partner_different_categories(self):
        """Testa geração de IDs para diferentes categorias."""
        categories = ["TECNOLOGIA", "SAÚDE", "EDUCAÇÃO"]
        expected_suffixes = ["_TEC", "_SAU", "_EDU"]

        for category, suffix in zip(categories, expected_suffixes, strict=False):
            partner = Partner(
                tenant_id="tenant_123",
                cnpj_hash="hash_789",
                cnpj="12.345.678/0001-90",
                trade_name="Empresa Teste",
                category=category,
                address="Endereço Teste",
            )

            self.assertTrue(partner.id.endswith(suffix))


if __name__ == "__main__":
    unittest.main()
