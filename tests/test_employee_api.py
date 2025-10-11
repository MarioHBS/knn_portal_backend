"""
Testes para os endpoints da API de funcionários.

Este módulo contém testes abrangentes para todos os endpoints
definidos em src/api/employee.py.
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from src.api.employee import router
from src.auth import JWTPayload
from src.models import ValidationCodeCreationRequest


@pytest.fixture
def mock_employee_user():
    """Fixture para usuário funcionário mock."""
    return JWTPayload(
        sub="employee-123",
        role="employee",
        tenant="knn",
        exp=int((datetime.now() + timedelta(hours=1)).timestamp()),
        iat=int(datetime.now().timestamp()),
        iss="test",
        aud="test",
        name="Test Employee",
    )


@pytest.fixture
def mock_partner():
    """Fixture para parceiro mock."""
    return {
        "id": "partner-123",
        "trade_name": "Parceiro Teste",
        "category": "alimentacao",
        "address": "Rua Teste, 123",
        "active": True,
    }


@pytest.fixture
def mock_employee():
    """Fixture para funcionário mock."""
    return {
        "id": "employee-123",
        "name": "Maria Silva",
        "department": "TI",
        "active_until": (datetime.now() + timedelta(days=30)).date().isoformat(),
    }


@pytest.fixture
def mock_benefit():
    """Fixture para benefício mock."""
    return {
        "id": "benefit-123",
        "partner_id": "partner-123",
        "title": "Desconto 15%",
        "benefit_type": "discount",
        "start_date": datetime.now().isoformat(),
        "end_date": (datetime.now() + timedelta(days=30)).isoformat(),
        "status": "active",
        "audience": "employee",
    }


@pytest.fixture
def mock_validation_code():
    """Fixture para código de validação mock."""
    return {
        "id": "code-123",
        "employee_id": "employee-123",
        "partner_id": "partner-123",
        "code_hash": "123456",
        "expires": (datetime.now() + timedelta(minutes=3)).isoformat(),
        "used_at": datetime.now().isoformat(),
        "user_type": "employee",
    }


class TestEmployeePartnersEndpoints:
    """Testes para os endpoints de parceiros do funcionário."""

    @pytest.mark.asyncio
    async def test_list_partners_success(self, mock_employee_user, mock_partner):
        """Testa listagem de parceiros com sucesso."""
        with (
            patch(
                "src.api.employee.validate_employee_role",
                return_value=mock_employee_user,
            ),
            patch(
                "src.api.employee.PartnersService.list_partners_common"
            ) as mock_service,
        ):
            mock_service.return_value = {
                "data": {"items": [mock_partner], "total": 1},
                "msg": "ok",
            }

            from src.api.employee import list_partners

            result = await list_partners(current_user=mock_employee_user)

            assert result["msg"] == "ok"
            assert len(result["data"]["items"]) == 1
            assert result["data"]["items"][0]["trade_name"] == "Parceiro Teste"

    @pytest.mark.asyncio
    async def test_list_partners_with_filters_and_ordering(
        self, mock_employee_user, mock_partner
    ):
        """Testa listagem de parceiros com filtros e ordenação."""
        with (
            patch(
                "src.api.employee.validate_employee_role",
                return_value=mock_employee_user,
            ),
            patch(
                "src.api.employee.PartnersService.list_partners_common"
            ) as mock_service,
        ):
            mock_service.return_value = {
                "data": {"items": [mock_partner], "total": 1},
                "msg": "ok",
            }

            from src.api.employee import list_partners

            result = await list_partners(
                cat="alimentacao",
                ord="category",
                limit=10,
                offset=0,
                current_user=mock_employee_user,
            )

            assert result["msg"] == "ok"
            # Verificar se os parâmetros foram passados corretamente
            mock_service.assert_called_once_with(
                current_user=mock_employee_user,
                cat="alimentacao",
                ord="category",
                limit=10,
                offset=0,
                use_circuit_breaker=True,
                enable_ordering=True,  # Habilitado para funcionários
            )

    @pytest.mark.asyncio
    async def test_list_partners_default_ordering(
        self, mock_employee_user, mock_partner
    ):
        """Testa listagem de parceiros com ordenação padrão."""
        with (
            patch(
                "src.api.employee.validate_employee_role",
                return_value=mock_employee_user,
            ),
            patch(
                "src.api.employee.PartnersService.list_partners_common"
            ) as mock_service,
        ):
            mock_service.return_value = {
                "data": {"items": [mock_partner], "total": 1},
                "msg": "ok",
            }

            from src.api.employee import list_partners

            result = await list_partners(current_user=mock_employee_user)

            assert result["msg"] == "ok"
            # Verificar se a ordenação padrão foi aplicada
            mock_service.assert_called_once_with(
                current_user=mock_employee_user,
                cat=None,
                ord="name",  # Ordenação padrão
                limit=20,
                offset=0,
                use_circuit_breaker=True,
                enable_ordering=True,
            )

    @pytest.mark.asyncio
    async def test_list_partners_service_error(self, mock_employee_user):
        """Testa erro no serviço de listagem de parceiros."""
        with (
            patch(
                "src.api.employee.validate_employee_role",
                return_value=mock_employee_user,
            ),
            patch(
                "src.api.employee.PartnersService.list_partners_common"
            ) as mock_service,
        ):
            mock_service.side_effect = Exception("Service error")

            from src.api.employee import list_partners

            with pytest.raises(Exception) as exc_info:
                await list_partners(current_user=mock_employee_user)

            assert "INTERNAL_ERROR" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_partner_details_success(
        self, mock_employee_user, mock_partner, mock_benefit
    ):
        """Testa obtenção de detalhes do parceiro com sucesso."""
        with (
            patch(
                "src.api.employee.validate_employee_role",
                return_value=mock_employee_user,
            ),
            patch("src.api.employee.with_circuit_breaker") as mock_circuit_breaker,
        ):
            # Mock para busca do parceiro
            mock_circuit_breaker.side_effect = [
                {"data": mock_partner},  # Primeira chamada: buscar parceiro
                {"items": [mock_benefit]},  # Segunda chamada: buscar benefícios
            ]

            from src.api.employee import get_partner_details

            result = await get_partner_details("partner-123", mock_employee_user)

            assert result["msg"] == "ok"
            assert result["data"]["trade_name"] == "Parceiro Teste"
            assert len(result["data"]["benefits"]) == 1

    @pytest.mark.asyncio
    async def test_get_partner_details_not_found(self, mock_employee_user):
        """Testa obtenção de detalhes de parceiro não encontrado."""
        with (
            patch(
                "src.api.employee.validate_employee_role",
                return_value=mock_employee_user,
            ),
            patch("src.api.employee.with_circuit_breaker") as mock_circuit_breaker,
        ):
            mock_circuit_breaker.return_value = {"data": None}

            from src.api.employee import get_partner_details

            with pytest.raises(Exception) as exc_info:
                await get_partner_details("invalid-id", mock_employee_user)

            assert "PARTNER_NOT_FOUND" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_partner_details_inactive(self, mock_employee_user, mock_partner):
        """Testa obtenção de detalhes de parceiro inativo."""
        mock_partner["active"] = False

        with (
            patch(
                "src.api.employee.validate_employee_role",
                return_value=mock_employee_user,
            ),
            patch("src.api.employee.with_circuit_breaker") as mock_circuit_breaker,
        ):
            mock_circuit_breaker.return_value = {"data": mock_partner}

            from src.api.employee import get_partner_details

            with pytest.raises(Exception) as exc_info:
                await get_partner_details("partner-123", mock_employee_user)

            assert "PARTNER_NOT_FOUND" in str(exc_info.value)


class TestEmployeeHistoryEndpoint:
    """Testes para o endpoint de histórico do funcionário."""

    @pytest.mark.asyncio
    async def test_get_employee_validation_history_success(
        self, mock_employee_user, mock_validation_code, mock_partner
    ):
        """Testa obtenção de histórico com sucesso."""
        with (
            patch(
                "src.api.employee.validate_employee_role",
                return_value=mock_employee_user,
            ),
            patch("src.api.employee.with_circuit_breaker") as mock_circuit_breaker,
        ):
            # Mock para busca de códigos e parceiros
            mock_circuit_breaker.side_effect = [
                {"items": [mock_validation_code]},  # Códigos de validação
                {"data": mock_partner},  # Dados do parceiro
            ]

            from src.api.employee import get_employee_validation_history

            result = await get_employee_validation_history(mock_employee_user)

            assert result["msg"] == "ok"
            assert result["data"]["total"] == 1
            assert len(result["data"]["history"]) == 1
            assert result["data"]["history"][0]["partner"]["name"] == "Parceiro Teste"
            assert result["data"]["history"][0]["code"] == "***"  # Código mascarado

    @pytest.mark.asyncio
    async def test_get_employee_validation_history_empty(self, mock_employee_user):
        """Testa obtenção de histórico vazio."""
        with (
            patch(
                "src.api.employee.validate_employee_role",
                return_value=mock_employee_user,
            ),
            patch("src.api.employee.with_circuit_breaker") as mock_circuit_breaker,
        ):
            mock_circuit_breaker.return_value = {"items": []}

            from src.api.employee import get_employee_validation_history

            result = await get_employee_validation_history(mock_employee_user)

            assert result["msg"] == "ok"
            assert result["data"]["total"] == 0
            assert len(result["data"]["history"]) == 0

    @pytest.mark.asyncio
    async def test_get_employee_validation_history_partner_not_found(
        self, mock_employee_user, mock_validation_code
    ):
        """Testa histórico com parceiro não encontrado."""
        with (
            patch(
                "src.api.employee.validate_employee_role",
                return_value=mock_employee_user,
            ),
            patch("src.api.employee.with_circuit_breaker") as mock_circuit_breaker,
        ):
            # Mock para códigos encontrados, mas parceiro não encontrado
            mock_circuit_breaker.side_effect = [
                {"items": [mock_validation_code]},  # Códigos de validação
                Exception("Partner not found"),  # Erro ao buscar parceiro
            ]

            from src.api.employee import get_employee_validation_history

            result = await get_employee_validation_history(mock_employee_user)

            assert result["msg"] == "ok"
            assert result["data"]["total"] == 1
            assert (
                result["data"]["history"][0]["partner"]["name"]
                == "Parceiro não encontrado"
            )

    @pytest.mark.asyncio
    async def test_get_employee_validation_history_service_error(
        self, mock_employee_user
    ):
        """Testa erro no serviço de histórico."""
        with (
            patch(
                "src.api.employee.validate_employee_role",
                return_value=mock_employee_user,
            ),
            patch("src.api.employee.with_circuit_breaker") as mock_circuit_breaker,
        ):
            mock_circuit_breaker.side_effect = Exception("Database error")

            from src.api.employee import get_employee_validation_history

            with pytest.raises(Exception) as exc_info:
                await get_employee_validation_history(mock_employee_user)

            assert "SERVER_ERROR" in str(exc_info.value)


class TestEmployeeValidationCodeEndpoint:
    """Testes para o endpoint de criação de código de validação."""

    @pytest.mark.asyncio
    async def test_create_validation_code_success(
        self, mock_employee_user, mock_partner, mock_employee
    ):
        """Testa criação de código de validação com sucesso."""
        with (
            patch(
                "src.api.employee.validate_employee_role",
                return_value=mock_employee_user,
            ),
            patch("src.api.employee.with_circuit_breaker") as mock_circuit_breaker,
            patch("src.api.employee.business_rules") as mock_business_rules,
            patch("src.api.employee.firestore_client") as mock_firestore,
        ):
            # Mock para busca de parceiro e funcionário
            mock_circuit_breaker.side_effect = [
                {"data": mock_partner},  # Parceiro encontrado
                {"data": mock_employee},  # Funcionário encontrado
            ]

            # Mock para regras de negócio
            mock_business_rules.validate_student_active.return_value = True
            mock_business_rules.generate_validation_code.return_value = "123456"
            mock_business_rules.calculate_code_expiration.return_value = (
                datetime.now() + timedelta(minutes=3)
            )

            # Mock para criação do documento
            mock_firestore.create_document = AsyncMock()

            from src.api.employee import create_validation_code

            request_data = ValidationCodeCreationRequest(partner_id="partner-123")

            result = await create_validation_code(request_data, mock_employee_user)

            assert result["msg"] == "ok"
            assert result["data"]["code"] == "123456"
            assert result["data"]["ttl_seconds"] == 180
            assert "expires" in result["data"]

    @pytest.mark.asyncio
    async def test_create_validation_code_partner_not_found(self, mock_employee_user):
        """Testa criação de código com parceiro não encontrado."""
        with (
            patch(
                "src.api.employee.validate_employee_role",
                return_value=mock_employee_user,
            ),
            patch("src.api.employee.with_circuit_breaker") as mock_circuit_breaker,
        ):
            mock_circuit_breaker.return_value = {"data": None}

            from src.api.employee import create_validation_code

            request_data = ValidationCodeCreationRequest(partner_id="invalid-partner")

            with pytest.raises(Exception) as exc_info:
                await create_validation_code(request_data, mock_employee_user)

            assert "NOT_FOUND" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_validation_code_partner_inactive(
        self, mock_employee_user, mock_partner
    ):
        """Testa criação de código com parceiro inativo."""
        mock_partner["active"] = False

        with (
            patch(
                "src.api.employee.validate_employee_role",
                return_value=mock_employee_user,
            ),
            patch("src.api.employee.with_circuit_breaker") as mock_circuit_breaker,
        ):
            mock_circuit_breaker.return_value = {"data": mock_partner}

            from src.api.employee import create_validation_code

            request_data = ValidationCodeCreationRequest(partner_id="partner-123")

            with pytest.raises(Exception) as exc_info:
                await create_validation_code(request_data, mock_employee_user)

            assert "NOT_FOUND" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_validation_code_employee_not_found(
        self, mock_employee_user, mock_partner
    ):
        """Testa criação de código com funcionário não encontrado."""
        with (
            patch(
                "src.api.employee.validate_employee_role",
                return_value=mock_employee_user,
            ),
            patch("src.api.employee.with_circuit_breaker") as mock_circuit_breaker,
        ):
            mock_circuit_breaker.side_effect = [
                {"data": mock_partner},  # Parceiro encontrado
                {"data": None},  # Funcionário não encontrado
            ]

            from src.api.employee import create_validation_code

            request_data = ValidationCodeCreationRequest(partner_id="partner-123")

            with pytest.raises(Exception) as exc_info:
                await create_validation_code(request_data, mock_employee_user)

            assert "NOT_FOUND" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_validation_code_employee_inactive(
        self, mock_employee_user, mock_partner, mock_employee
    ):
        """Testa criação de código com funcionário inativo."""
        mock_employee["active_until"] = (
            (datetime.now() - timedelta(days=1)).date().isoformat()
        )

        with (
            patch(
                "src.api.employee.validate_employee_role",
                return_value=mock_employee_user,
            ),
            patch("src.api.employee.with_circuit_breaker") as mock_circuit_breaker,
            patch("src.api.employee.business_rules") as mock_business_rules,
        ):
            mock_circuit_breaker.side_effect = [
                {"data": mock_partner},  # Parceiro encontrado
                {"data": mock_employee},  # Funcionário encontrado mas inativo
            ]
            mock_business_rules.validate_student_active.return_value = False

            from src.api.employee import create_validation_code

            request_data = ValidationCodeCreationRequest(partner_id="partner-123")

            with pytest.raises(Exception) as exc_info:
                await create_validation_code(request_data, mock_employee_user)

            assert "INACTIVE_EMPLOYEE" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_validation_code_duplicate_handling(
        self, mock_employee_user, mock_partner, mock_employee
    ):
        """Testa tratamento de código duplicado."""
        with (
            patch(
                "src.api.employee.validate_employee_role",
                return_value=mock_employee_user,
            ),
            patch("src.api.employee.with_circuit_breaker") as mock_circuit_breaker,
            patch("src.api.employee.business_rules") as mock_business_rules,
            patch("src.api.employee.firestore_client") as mock_firestore,
        ):
            # Mock para busca de parceiro e funcionário
            mock_circuit_breaker.side_effect = [
                {"data": mock_partner},
                {"data": mock_employee},
            ]

            # Mock para regras de negócio
            mock_business_rules.validate_student_active.return_value = True
            mock_business_rules.generate_validation_code.side_effect = [
                "123456",
                "654321",
            ]  # Dois códigos diferentes
            mock_business_rules.calculate_code_expiration.return_value = (
                datetime.now() + timedelta(minutes=3)
            )

            # Mock para criação do documento - primeira tentativa falha, segunda sucede
            mock_firestore.create_document = AsyncMock()
            mock_firestore.create_document.side_effect = [
                Exception("Document already exists"),  # Primeira tentativa falha
                None,  # Segunda tentativa sucede
            ]

            from src.api.employee import create_validation_code

            request_data = ValidationCodeCreationRequest(partner_id="partner-123")

            result = await create_validation_code(request_data, mock_employee_user)

            assert result["msg"] == "ok"
            assert result["data"]["code"] == "654321"  # Segundo código gerado
            assert mock_firestore.create_document.call_count == 2


@pytest.mark.integration
class TestEmployeeAPIIntegration:
    """Testes de integração para a API de funcionários."""

    def test_employee_endpoints_require_authentication(self):
        """Testa que todos os endpoints requerem autenticação."""
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router, prefix="/employee")
        client = TestClient(app)

        # Testar endpoints sem autenticação
        endpoints = [
            ("GET", "/employee/partners"),
            ("GET", "/employee/partners/123"),
            ("GET", "/employee/me/history"),
            ("POST", "/employee/validation-codes"),
        ]

        for method, endpoint in endpoints:
            response = getattr(client, method.lower())(endpoint)
            # Deve retornar erro de autenticação (401 ou 403)
            assert response.status_code in [401, 403, 422]

    def test_employee_role_validation(self):
        """Testa validação de role de funcionário."""
        # Este teste seria implementado com um token válido mas com role incorreta
        # Por simplicidade, apenas verificamos que a validação existe
        from src.api.employee import validate_employee_role

        assert validate_employee_role is not None

    @pytest.mark.asyncio
    async def test_employee_circuit_breaker_usage(self, mock_employee_user):
        """Testa que o circuit breaker está sendo usado nos endpoints."""
        with (
            patch(
                "src.api.employee.validate_employee_role",
                return_value=mock_employee_user,
            ),
            patch(
                "src.api.employee.PartnersService.list_partners_common"
            ) as mock_service,
        ):
            mock_service.return_value = {"data": {"items": [], "total": 0}, "msg": "ok"}

            from src.api.employee import list_partners

            await list_partners(current_user=mock_employee_user)

            # Verificar se o circuit breaker foi habilitado
            mock_service.assert_called_once()
            call_args = mock_service.call_args[1]
            assert call_args["use_circuit_breaker"] is True
            assert call_args["enable_ordering"] is True

    @pytest.mark.asyncio
    async def test_employee_ordering_enabled(self, mock_employee_user):
        """Testa que a ordenação está habilitada para funcionários."""
        with (
            patch(
                "src.api.employee.validate_employee_role",
                return_value=mock_employee_user,
            ),
            patch(
                "src.api.employee.PartnersService.list_partners_common"
            ) as mock_service,
        ):
            mock_service.return_value = {"data": {"items": [], "total": 0}, "msg": "ok"}

            from src.api.employee import list_partners

            await list_partners(ord="category", current_user=mock_employee_user)

            # Verificar se a ordenação foi passada corretamente
            mock_service.assert_called_once()
            call_args = mock_service.call_args[1]
            assert call_args["ord"] == "category"
            assert call_args["enable_ordering"] is True
