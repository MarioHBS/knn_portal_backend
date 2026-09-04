import unittest

from src.models.partner import PartnerCategory
from src.utils.id_generators import IDGenerators


class TestIDGenerators(unittest.TestCase):
    """Testes unitários para os algoritmos de criação de IDs."""

    def setUp(self):
        """Configuração inicial para os testes."""
        self.id_gen = IDGenerators()

    def test_extract_initials_simple_name(self):
        resultado = IDGenerators.extract_initials("João Silva")
        self.assertEqual(resultado, "JS")

    def test_extract_initials_multiple_names(self):
        resultado = IDGenerators.extract_initials("Maria Eduarda Costa")
        self.assertEqual(resultado, "MEC")

    def test_extract_initials_single_name(self):
        resultado = IDGenerators.extract_initials("João")
        self.assertEqual(resultado, "J")

    def test_extract_initials_name_with_spaces(self):
        resultado = IDGenerators.extract_initials("  Ana   Paula  ")
        self.assertEqual(resultado, "AP")

    def test_extract_initials_name_with_special_characters(self):
        resultado = IDGenerators.extract_initials("L'Oréal D. Souza")
        self.assertEqual(resultado, "LDS")

    def test_extract_initials_name_with_hyphen(self):
        resultado = IDGenerators.extract_initials("Maria Clara-Silva")
        self.assertEqual(resultado, "MCS")

    def test_interleave_initials_digits_valid(self):
        initials = "ABC"
        digits = "1234"
        resultado = IDGenerators.interleave_initials_digits(initials, digits, 7)
        self.assertEqual(resultado, "A1B2C34")

    def test_interleave_initials_digits_more_initials(self):
        initials = "ABCD"
        digits = "12"
        resultado = IDGenerators.interleave_initials_digits(initials, digits, 6)
        self.assertEqual(resultado, "A1B2CD")

    def test_interleave_initials_digits_more_digits(self):
        initials = "AB"
        digits = "12345"
        resultado = IDGenerators.interleave_initials_digits(initials, digits, 7)
        self.assertEqual(resultado, "A1B2345")

    def test_interleave_initials_digits_empty_digits(self):
        initials = "ABC"
        digits = ""
        resultado = IDGenerators.interleave_initials_digits(initials, digits, 3)
        self.assertEqual(resultado, "ABC")

    def test_generate_employee_id_valid(self):
        name = "João da Silva"
        resultado = IDGenerators.generate_employee_id(
            name=name, role="Analista", email="joao@teste.com"
        )
        self.assertTrue(resultado.startswith("EMP_"))
        self.assertEqual(len(resultado), 15)

    def test_generate_employee_id_short_name(self):
        name = "Ana"
        resultado = IDGenerators.generate_employee_id(
            name=name, role="Gerente", zip_code="12345-678"
        )
        self.assertTrue(resultado.startswith("EMP_"))
        self.assertEqual(len(resultado), 15)

    def test_generate_partner_id_full_scenario(self):
        trade_name = "Empresa Teste"
        tax_id = "12345678901234"
        category = PartnerCategory.TECNOLOGIA
        resultado = IDGenerators.generate_partner_id(
            trade_name=trade_name, tax_id=tax_id, category=category
        )
        self.assertTrue(resultado.startswith("PTN_"))
        self.assertTrue(resultado.endswith("_TEC"))
        self.assertEqual(len(resultado), 15)  # PTN_ + 8 caracteres + _TEC

    def test_generate_partner_id_expected_1(self):
        """Gera um ID de parceiro com um nome e CNPJ específicos."""
        trade_name = "Tecno Soluções"
        tax_id = "12345678901234"  # Base: 12345678
        category = PartnerCategory.TECNOLOGIA
        # Iniciais: TS, 5 dígitos do final da base (12345678): 45678
        # Intercalado: T4S5678
        expected = "PTN_T4S5678_TEC"
        resultado = IDGenerators.generate_partner_id(
            trade_name=trade_name, tax_id=tax_id, category=category
        )
        self.assertEqual(resultado, expected)

    def test_generate_partner_id_expected_2(self):
        trade_name = "Saúde e Bem Estar"
        tax_id = "11222333444455"
        category = PartnerCategory.SAUDE_BEM_ESTAR
        resultado = IDGenerators.generate_partner_id(
            trade_name=trade_name, tax_id=tax_id, category=category
        )
        self.assertEqual(resultado, "PTN_S2B3E33_SAU")

    def test_generate_partner_id_expected_3(self):
        trade_name = "Educação para Todos"
        tax_id = "88777666555544"
        category = PartnerCategory.EDUCACAO
        resultado = IDGenerators.generate_partner_id(
            trade_name=trade_name, tax_id=tax_id, category=category
        )
        self.assertEqual(resultado, "PTN_E7P6T66_EDU")

    def test_generate_partner_id_short_name(self):
        trade_name = "A"
        tax_id = "55566777888899"
        category = PartnerCategory.SAUDE_BEM_ESTAR
        resultado = IDGenerators.generate_partner_id(
            trade_name=trade_name, tax_id=tax_id, category=category
        )
        self.assertEqual(resultado, "PTN_A566777_SAU")

    def test_generate_partner_id_short_documento(self):
        trade_name = "Empresa Teste"
        tax_id = "123"
        category = PartnerCategory.TECNOLOGIA
        with self.assertRaises(ValueError):
            IDGenerators.generate_partner_id(
                trade_name=trade_name, tax_id=tax_id, category=category
            )

    def test_generate_partner_id_invalid_documento_chars(self):
        trade_name = "Empresa Teste"
        tax_id = "1234567890123A"
        category = PartnerCategory.TECNOLOGIA
        with self.assertRaises(ValueError):
            IDGenerators.generate_partner_id(
                trade_name=trade_name, tax_id=tax_id, category=category
            )

    def test_generate_partner_id_all_categories(self):
        trade_name = "Super Loja"
        tax_id = "12345678000195"
        for category_enum in PartnerCategory:
            with self.subTest(category=category_enum.name):
                partner_id = IDGenerators.generate_partner_id(
                    trade_name=trade_name, tax_id=tax_id, category=category_enum
                )
                expected_suffix = IDGenerators.CATEGORY_CODES[category_enum]
                self.assertTrue(partner_id.endswith(f"_{expected_suffix}"))


if __name__ == "__main__":
    unittest.main()
