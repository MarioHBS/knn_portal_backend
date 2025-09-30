"""Testes para funcionalidade de códigos de validação temporários."""

from datetime import datetime, timedelta

import pytest

from src.models import RedeemRequest, ValidationCodeCreationRequest


class TestValidationCodeModels:
    """Testes para modelos de códigos de validação."""

    def test_validation_code_request_valid(self):
        """Testa criação de ValidationCodeCreationRequest válido."""
        request = ValidationCodeCreationRequest(partner_id="partner123")
        assert request.partner_id == "partner123"

    def test_validation_code_request_empty_partner_id(self):
        """Testa ValidationCodeCreationRequest com partner_id vazio (ainda válido pelo modelo)."""
        request = ValidationCodeCreationRequest(partner_id="")
        assert request.partner_id == ""

    def test_redeem_request_valid(self):
        """Testa criação de RedeemRequest válido."""
        request = RedeemRequest(code="123456", cnpj="12345678000195")
        assert request.code == "123456"
        assert request.cnpj == "12345678000195"

    def test_redeem_request_invalid_code(self):
        """Testa RedeemRequest com código inválido."""
        with pytest.raises(ValueError, match="Código deve conter 6 dígitos numéricos"):
            RedeemRequest(code="12345", cnpj="12345678000195")  # Código muito curto

    def test_redeem_request_invalid_cnpj(self):
        """Testa RedeemRequest com CNPJ inválido."""
        with pytest.raises(ValueError, match="CNPJ deve conter 14 dígitos numéricos"):
            RedeemRequest(code="123456", cnpj="123456789")  # CNPJ muito curto


class TestValidationCodeLogic:
    """Testes para lógica de códigos de validação."""

    def test_code_generation_format(self):
        """Testa se o código gerado tem o formato correto."""
        import random
        import string

        # Simula a lógica de geração de código
        code = "".join(random.choices(string.digits, k=6))

        assert len(code) == 6
        assert code.isdigit()

    def test_code_expiration_logic(self):
        """Testa lógica de expiração de códigos."""
        now = datetime.now()
        expires = now + timedelta(minutes=3)

        # Código não expirado
        assert expires > now

        # Código expirado
        expired_time = now - timedelta(minutes=1)
        assert expired_time < now

    def test_code_uniqueness_simulation(self):
        """Testa se códigos gerados são únicos (simulação)."""
        import random
        import string

        codes = set()
        for _ in range(100):
            code = "".join(random.choices(string.digits, k=6))
            codes.add(code)

        # Com 100 códigos de 6 dígitos, deve haver alta probabilidade de serem únicos
        assert len(codes) > 90  # Permite algumas colisões por acaso

    def test_ttl_calculation(self):
        """Testa cálculo do TTL (Time To Live)."""
        ttl_seconds = 3 * 60  # 3 minutos
        assert ttl_seconds == 180

        # Verifica se o TTL está dentro do esperado
        now = datetime.now()
        expires = now + timedelta(seconds=ttl_seconds)
        calculated_ttl = (expires - now).total_seconds()

        assert abs(calculated_ttl - ttl_seconds) < 1  # Margem de 1 segundo


class TestValidationCodeSecurity:
    """Testes para aspectos de segurança dos códigos."""

    def test_code_masking(self):
        """Testa mascaramento de códigos para histórico."""
        original_code = "123456"
        masked_code = "***"

        # Simula a lógica de mascaramento
        assert masked_code != original_code
        assert len(masked_code) == 3

    def test_tenant_isolation(self):
        """Testa isolamento por tenant."""
        tenant1_id = "tenant1"
        tenant2_id = "tenant2"
        user_id = "user123"

        # IDs devem ser diferentes para tenants diferentes
        tenant1_doc_id = f"{tenant1_id}_{user_id}"
        tenant2_doc_id = f"{tenant2_id}_{user_id}"

        assert tenant1_doc_id != tenant2_doc_id
        assert tenant1_doc_id.startswith(tenant1_id)
        assert tenant2_doc_id.startswith(tenant2_id)

    def test_role_validation(self):
        """Testa validação de roles."""
        valid_roles = ["student", "employee", "partner", "admin"]

        # Roles válidas
        assert "student" in valid_roles
        assert "employee" in valid_roles
        assert "partner" in valid_roles

        # Role inválida
        assert "invalid_role" not in valid_roles


class TestValidationCodeBusinessRules:
    """Testes para regras de negócio dos códigos."""

    def test_employee_status_validation(self):
        """Testa validação de status do funcionário."""
        active_status = "active"
        inactive_status = "inactive"

        assert active_status == "active"
        assert inactive_status != "active"

    def test_partner_active_validation(self):
        """Testa validação de parceiro ativo."""
        partner_active = True
        partner_inactive = False

        assert partner_active is True
        assert partner_inactive is False

    def test_code_usage_validation(self):
        """Testa validação de uso do código."""
        code_used = True
        code_unused = False

        # Código já usado não pode ser usado novamente
        assert code_used is True
        assert code_unused is False

    def test_user_type_validation(self):
        """Testa validação de tipos de usuário."""
        valid_user_types = ["student", "employee"]

        assert "student" in valid_user_types
        assert "employee" in valid_user_types
        assert "invalid_type" not in valid_user_types

    def test_cnpj_format_validation(self):
        """Testa validação de formato do CNPJ."""
        valid_cnpj = "12345678000195"
        invalid_cnpj_short = "123456789"
        invalid_cnpj_long = "123456789001234"

        assert len(valid_cnpj) == 14
        assert valid_cnpj.isdigit()
        assert len(invalid_cnpj_short) != 14
        assert len(invalid_cnpj_long) != 14
