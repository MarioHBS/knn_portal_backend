import unittest

from src.utils.id_generators import IDGenerators


class TestIDGenerators(unittest.TestCase):
    """Testes unitários para os algoritmos de criação de IDs."""

    def setUp(self):
        """Configuração inicial para os testes."""
        self.id_gen = IDGenerators()

    def test_extrair_iniciais_nome_simples(self):
        """Testa extração de iniciais de nome simples."""
        resultado = IDGenerators.extrair_iniciais("João Silva")
        self.assertEqual(resultado, ["J", "S"])

    def test_extrair_iniciais_nome_composto(self):
        """Testa extração de iniciais de nome composto."""
        resultado = IDGenerators.extrair_iniciais("Maria da Silva Santos")
        self.assertEqual(resultado, ["M", "S", "S"])

    def test_extrair_iniciais_nome_unico(self):
        """Testa extração de iniciais de nome único."""
        resultado = IDGenerators.extrair_iniciais("João")
        self.assertEqual(resultado, ["J"])

    def test_extrair_iniciais_nome_vazio(self):
        """Testa extração de iniciais de nome vazio."""
        resultado = IDGenerators.extrair_iniciais("")
        self.assertEqual(resultado, [])

    def test_extrair_digitos_cep(self):
        """Testa extração de dígitos do CEP."""
        resultado = IDGenerators.extrair_digitos_cep("12345-678")
        self.assertEqual(resultado, "678")

        resultado = IDGenerators.extrair_digitos_cep("12345678")
        self.assertEqual(resultado, "678")

    def test_extrair_digitos_telefone(self):
        """Testa extração de dígitos do telefone."""
        resultado = IDGenerators.extrair_digitos_telefone("(11) 99999-9999")
        self.assertEqual(resultado, "999")

        resultado = IDGenerators.extrair_digitos_telefone("11999999999")
        self.assertEqual(resultado, "999")

    def test_extrair_digitos_cnpj(self):
        """Testa extração de dígitos do CNPJ."""
        resultado = IDGenerators.extrair_digitos_cnpj("12.345.678/0001-90", 3)
        self.assertEqual(resultado, "678")

        resultado = IDGenerators.extrair_digitos_cnpj("12345678000190", 4)
        self.assertEqual(resultado, "0190")  # Últimos 4 dígitos do primeiro grupo

    def test_intercalar_iniciais_digitos(self):
        """Testa intercalação de iniciais com dígitos."""
        resultado = IDGenerators.intercalar_iniciais_digitos(["J", "S"], "123456", 4)
        self.assertEqual(resultado, "J1S2")

        resultado = IDGenerators.intercalar_iniciais_digitos(
            ["M", "S", "S"], "123456", 6
        )
        self.assertEqual(resultado, "M1S2S3")

    def test_gerar_id_aluno_completo(self):
        """Testa geração de ID completo para aluno."""
        resultado = IDGenerators.gerar_id_aluno(
            nome="João Silva Santos",
            curso="KIDS 1",
            cep="12345-678",
            celular="(11) 99999-9999",
            email="joao@email.com",
        )

        # Verifica estrutura: STD_[intercalação]_[sufixo]
        self.assertTrue(resultado.startswith("STD_"))
        self.assertTrue(resultado.endswith("_K1"))

        # Verifica se contém intercalação JSS com dígitos
        partes = resultado.split("_")
        self.assertEqual(len(partes), 3)
        intercalacao = partes[1]
        self.assertTrue("J" in intercalacao and "S" in intercalacao)

    def test_gerar_id_funcionario_completo(self):
        """Testa geração de ID completo para funcionário."""
        resultado = IDGenerators.gerar_id_funcionario(
            nome="Maria Oliveira",
            cargo="PROFESSORA",
            cep="54321-876",
            telefone="(21) 88888-8888",
        )

        # Verifica estrutura: EMP_[intercalação]_[sufixo]
        self.assertTrue(resultado.startswith("EMP_"))
        self.assertTrue(resultado.endswith("_PR"))

        # Verifica se contém intercalação MO com dígitos
        partes = resultado.split("_")
        self.assertEqual(len(partes), 3)
        intercalacao = partes[1]
        self.assertTrue("M" in intercalacao and "O" in intercalacao)

    def test_gerar_id_parceiro_completo(self):
        """Testa geração de ID completo para parceiro."""
        resultado = IDGenerators.gerar_id_parceiro(
            trade_name="Empresa ABC Ltda",
            category="TECNOLOGIA",
            cnpj="12.345.678/0001-90",
        )

        # Verifica estrutura: PTN_[intercalação]_[sufixo]
        self.assertTrue(resultado.startswith("PTN_"))
        self.assertTrue(resultado.endswith("_TEC"))

        # Verifica se contém intercalação EAL com dígitos
        partes = resultado.split("_")
        self.assertEqual(len(partes), 3)
        intercalacao = partes[1]
        self.assertTrue(
            "E" in intercalacao and "A" in intercalacao and "L" in intercalacao
        )

    def test_validar_id_formato_valido(self):
        """Testa validação de formato de ID válido."""
        # IDs válidos
        self.assertTrue(IDGenerators.validar_id_formato("STD_J1S23456_K1", "student"))
        self.assertTrue(IDGenerators.validar_id_formato("EMP_M1O23456_PR", "employee"))
        self.assertTrue(IDGenerators.validar_id_formato("PTN_E1A2L34_TEC", "partner"))

    def test_validar_id_formato_invalido(self):
        """Testa validação de formato de ID inválido."""
        # IDs inválidos
        self.assertFalse(IDGenerators.validar_id_formato("INVALID_FORMAT", "student"))
        self.assertFalse(IDGenerators.validar_id_formato("STD_ONLY_PREFIX", "student"))
        self.assertFalse(IDGenerators.validar_id_formato("_MISSING_PREFIX", "student"))
        self.assertFalse(IDGenerators.validar_id_formato("", "student"))

    def test_casos_extremos_nome_com_acentos(self):
        """Testa casos extremos com nomes acentuados."""
        resultado = IDGenerators.extrair_iniciais("José da Conceição")
        self.assertEqual(resultado, ["J", "C"])

    def test_casos_extremos_dados_incompletos(self):
        """Testa geração de ID com dados incompletos."""
        resultado = IDGenerators.gerar_id_aluno(
            nome="João Silva", curso="KIDS 1", cep="", celular="11999999999", email=""
        )
        self.assertTrue(resultado.startswith("STD_"))
        self.assertTrue(resultado.endswith("_K1"))

    def test_intercalacao_com_iniciais_maiores_que_digitos(self):
        """Testa intercalação quando há mais iniciais que dígitos disponíveis."""
        resultado = IDGenerators.intercalar_iniciais_digitos(
            ["A", "B", "C", "D", "E", "F"], "123", 8
        )
        # Deve intercalar até onde há dígitos e preencher com zeros
        self.assertEqual(resultado, "A1B2C3D0")

    def test_intercalacao_com_digitos_maiores_que_iniciais(self):
        """Testa intercalação quando há mais dígitos que iniciais."""
        resultado = IDGenerators.intercalar_iniciais_digitos(["A", "B"], "123456", 6)
        # Deve intercalar até onde há iniciais
        self.assertEqual(resultado, "A1B234")

    def test_id_aluno_esperado_1(self):
        """Testa geração de ID específico para aluno - Caso 1."""
        resultado = IDGenerators.gerar_id_aluno(
            nome="João Silva Santos",
            curso="KIDS 1",
            cep="12345-678",
            celular="(11) 99999-9999",
            email="joao@email.com",
        )
        # Esperado: STD_J6S7S899_K1 (JSS + 678 + 99)
        self.assertEqual(resultado, "STD_J6S7S899_K1")

    def test_id_aluno_esperado_2(self):
        """Testa geração de ID específico para aluno - Caso 2."""
        resultado = IDGenerators.gerar_id_aluno(
            nome="Maria da Silva",
            curso="TEENS 2",
            cep="54321-123",
            celular="(21) 88888-8888",
            email="maria123@escola.com",
        )
        # Esperado: STD_M1S23888_T2 (MS + 123 + 888)
        self.assertEqual(resultado, "STD_M1S23888_T2")

    def test_id_aluno_esperado_3(self):
        """Testa geração de ID específico para aluno - Caso 3."""
        resultado = IDGenerators.gerar_id_aluno(
            nome="Ana Paula",
            curso="ADVANCED 1",
            cep="98765-432",
            celular="(31) 77777-7777",
            email="",
        )
        # Esperado: STD_A4P32777_A1 (AP + 432 + 777)
        self.assertEqual(resultado, "STD_A4P32777_A1")

    def test_id_funcionario_esperado_1(self):
        """Testa geração de ID específico para funcionário - Caso 1."""
        resultado = IDGenerators.gerar_id_funcionario(
            nome="Carlos Eduardo",
            cargo="PROFESSORA",
            cep="11111-222",
            telefone="(11) 55555-5555",
        )
        # Esperado: EMP_C2E22555_PR (CE + 222 + 555)
        self.assertEqual(resultado, "EMP_C2E22555_PR")

    def test_id_funcionario_esperado_2(self):
        """Testa geração de ID específico para funcionário - Caso 2."""
        resultado = IDGenerators.gerar_id_funcionario(
            nome="Fernanda Santos",
            cargo="CDA",
            cep="33333-444",
            telefone="(21) 66666-6666",
        )
        # Esperado: EMP_F4S4466_CDA (FS + 444 + 66)
        self.assertEqual(resultado, "EMP_F4S4466_CDA")

    def test_id_funcionario_esperado_3(self):
        """Testa geração de ID específico para funcionário - Caso 3."""
        resultado = IDGenerators.gerar_id_funcionario(
            nome="Roberto Lima",
            cargo="ADM. FINANCEIRO",
            cep="77777-888",
            telefone="(31) 44444-4444",
        )
        # Esperado: EMP_R8L88444_AF (RL + 888 + 444)
        self.assertEqual(resultado, "EMP_R8L88444_AF")

    def test_id_parceiro_esperado_1(self):
        """Testa geração de ID específico para parceiro - Caso 1."""
        resultado = IDGenerators.gerar_id_parceiro(
            trade_name="Tech Solutions",
            category="TECNOLOGIA",
            cnpj="12.345.678/0001-90",
        )
        # Esperado: PTN_T4S5678_TEC (TS + 45678 do CNPJ)
        self.assertEqual(resultado, "PTN_T4S5678_TEC")

    def test_id_parceiro_esperado_2(self):
        """Testa geração de ID específico para parceiro - Caso 2."""
        resultado = IDGenerators.gerar_id_parceiro(
            trade_name="Saúde & Vida", category="SAÚDE", cnpj="98.765.432/0001-11"
        )
        # Esperado: PTN_S6V5432_SAU (SV + 65432 do CNPJ)
        self.assertEqual(resultado, "PTN_S6V5432_SAU")

    def test_id_parceiro_esperado_3(self):
        """Testa geração de ID específico para parceiro - Caso 3."""
        resultado = IDGenerators.gerar_id_parceiro(
            trade_name="Escola ABC", category="EDUCAÇÃO", cnpj="11.222.333/0001-44"
        )
        # Esperado: PTN_E2A2333_EDU (EA + 22333 do CNPJ)
        self.assertEqual(resultado, "PTN_E2A2333_EDU")


if __name__ == "__main__":
    unittest.main()
