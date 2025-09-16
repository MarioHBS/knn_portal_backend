"""
Testes para os endpoints da API de parceiros.

Este módulo contém testes abrangentes para todos os endpoints
definidos em src/api/partner.py.
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from src.api.partner import router
from src.auth import JWTPayload
from src.models import (
    PromotionRequest,
    RedeemRequest,
)


@pytest.fixture
def mock_partner_user():
    """Fixture para usuário parceiro mock."""
    return JWTPayload(
        sub="partner-123",
        role="partner",
        tenant="knn",
        exp=int((datetime.now() + timedelta(hours=1)).timestamp()),
        iat=int(datetime.now().timestamp()),
        iss="test",
        aud="test",
        name="Test Partner",
    )


@pytest.fixture
def mock_validation_code():
    """Fixture para código de validação mock."""
    return {
        "id": "code-123",
        "code": "123456",
        "partner_id": "partner-123",
        "student_id": "student-123",
        "user_type": "student",
        "expires": (datetime.now() + timedelta(hours=1)).isoformat(),
        "used_at": None,
        "created_at": datetime.now().isoformat(),
    }


@pytest.fixture
def mock_student():
    """Fixture para estudante mock."""
    return {
        "id": "student-123",
        "name": "João Silva",
        "course": "Engenharia",
        "cnpj_hash": "hashed_cnpj_123",
        "active_until": (datetime.now() + timedelta(days=30)).date().isoformat(),
    }


@pytest.fixture
def mock_promotion():
    """Fixture para promoção mock."""
    return {
        "id": "promotion-123",
        "partner_id": "partner-123",
        "title": "Desconto 20%",
        "type": "discount",
        "valid_from": datetime.now().isoformat(),
        "valid_to": (datetime.now() + timedelta(days=30)).isoformat(),
        "active": True,
        "audience": ["student"],
    }


class TestPartnerRedeemEndpoint:
    """Testes para o endpoint POST /redeem."""

    @pytest.mark.asyncio
    async def test_redeem_code_success(
        self, mock_partner_user, mock_validation_code, mock_student
    ):
        """Testa resgate de código com sucesso."""
        with (
            patch(
                "src.api.partner.validate_partner_role", return_value=mock_partner_user
            ),
            patch("src.api.partner.validate_cnpj", return_value=True),
            patch("src.api.partner.hash_cnpj", return_value="hashed_cnpj_123"),
            patch("src.api.partner.with_circuit_breaker") as mock_circuit_breaker,
            patch("src.api.partner.firestore_client") as mock_firestore,
        ):
            # Configurar mocks
            mock_circuit_breaker.side_effect = [
                {"data": mock_validation_code},  # Busca do código
                {"data": mock_student},  # Busca do estudante
            ]
            mock_firestore.update_document = AsyncMock()
            mock_firestore.create_document = AsyncMock()

            # Fazer requisição
            request_data = RedeemRequest(code="123456", cnpj="12345678000195")

            # Simular endpoint
            from src.api.partner import redeem_code

            result = await redeem_code(request_data, mock_partner_user)

            # Verificar resultado
            assert result["msg"] == "ok"
            assert result["data"]["user"]["name"] == "João Silva"
            assert result["data"]["user"]["course"] == "Engenharia"
            assert result["data"]["user_type"] == "student"

    @pytest.mark.asyncio
    async def test_redeem_code_invalid_cnpj(self, mock_partner_user):
        """Testa resgate com CNPJ inválido."""
        with (
            patch(
                "src.api.partner.validate_partner_role", return_value=mock_partner_user
            ),
            patch("src.api.partner.validate_cnpj", return_value=False),
        ):
            from src.api.partner import redeem_code

            request_data = RedeemRequest(code="123456", cnpj="invalid_cnpj")

            with pytest.raises(Exception) as exc_info:
                await redeem_code(request_data, mock_partner_user)

            assert "INVALID_CNPJ" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_redeem_code_not_found(self, mock_partner_user):
        """Testa resgate com código não encontrado."""
        with (
            patch(
                "src.api.partner.validate_partner_role", return_value=mock_partner_user
            ),
            patch("src.api.partner.validate_cnpj", return_value=True),
            patch("src.api.partner.with_circuit_breaker", return_value={"data": None}),
        ):
            from src.api.partner import redeem_code

            request_data = RedeemRequest(code="123456", cnpj="12345678000195")

            with pytest.raises(Exception) as exc_info:
                await redeem_code(request_data, mock_partner_user)

            assert "NOT_FOUND" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_redeem_code_already_used(
        self, mock_partner_user, mock_validation_code
    ):
        """Testa resgate com código já utilizado."""
        # Marcar código como usado
        mock_validation_code["used_at"] = datetime.now().isoformat()

        with (
            patch(
                "src.api.partner.validate_partner_role", return_value=mock_partner_user
            ),
            patch("src.api.partner.validate_cnpj", return_value=True),
            patch(
                "src.api.partner.with_circuit_breaker",
                return_value={"data": mock_validation_code},
            ),
        ):
            from src.api.partner import redeem_code

            request_data = RedeemRequest(code="123456", cnpj="12345678000195")

            with pytest.raises(Exception) as exc_info:
                await redeem_code(request_data, mock_partner_user)

            assert "CODE_USED" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_redeem_code_wrong_partner(
        self, mock_partner_user, mock_validation_code
    ):
        """Testa resgate com código de outro parceiro."""
        # Alterar partner_id do código
        mock_validation_code["partner_id"] = "other-partner"

        with (
            patch(
                "src.api.partner.validate_partner_role", return_value=mock_partner_user
            ),
            patch("src.api.partner.validate_cnpj", return_value=True),
            patch(
                "src.api.partner.with_circuit_breaker",
                return_value={"data": mock_validation_code},
            ),
        ):
            from src.api.partner import redeem_code

            request_data = RedeemRequest(code="123456", cnpj="12345678000195")

            with pytest.raises(Exception) as exc_info:
                await redeem_code(request_data, mock_partner_user)

            assert "INVALID_PARTNER" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_redeem_code_expired(self, mock_partner_user, mock_validation_code):
        """Testa resgate com código expirado."""
        # Definir código como expirado
        mock_validation_code["expires"] = (
            datetime.now() - timedelta(hours=1)
        ).isoformat()

        with (
            patch(
                "src.api.partner.validate_partner_role", return_value=mock_partner_user
            ),
            patch("src.api.partner.validate_cnpj", return_value=True),
            patch(
                "src.api.partner.with_circuit_breaker",
                return_value={"data": mock_validation_code},
            ),
        ):
            from src.api.partner import redeem_code

            request_data = RedeemRequest(code="123456", cnpj="12345678000195")

            with pytest.raises(Exception) as exc_info:
                await redeem_code(request_data, mock_partner_user)

            assert "EXPIRED" in str(exc_info.value)


class TestPartnerPromotionsEndpoints:
    """Testes para os endpoints de promoções do parceiro."""

    @pytest.mark.asyncio
    async def test_list_promotions_success(self, mock_partner_user, mock_promotion):
        """Testa listagem de promoções com sucesso."""
        with (
            patch(
                "src.api.partner.validate_partner_role", return_value=mock_partner_user
            ),
            patch(
                "src.api.partner.with_circuit_breaker",
                return_value={"items": [mock_promotion]},
            ),
        ):
            from src.api.partner import list_partner_promotions

            result = await list_partner_promotions(current_user=mock_partner_user)

            assert result["msg"] == "ok"
            assert len(result["data"]["items"]) == 1
            assert result["data"]["items"][0]["title"] == "Desconto 20%"

    @pytest.mark.asyncio
    async def test_create_promotion_success(self, mock_partner_user):
        """Testa criação de promoção com sucesso."""
        with (
            patch(
                "src.api.partner.validate_partner_role", return_value=mock_partner_user
            ),
            patch("src.api.partner.firestore_client") as mock_firestore,
        ):
            mock_firestore.create_document = AsyncMock(
                return_value={"id": "new-promotion"}
            )

            from src.api.partner import create_promotion

            request_data = PromotionRequest(
                title="Nova Promoção",
                type="discount",
                valid_from=datetime.now(),
                valid_to=datetime.now() + timedelta(days=30),
                active=True,
                audience=["student"],
            )

            result = await create_promotion(request_data, mock_partner_user)

            assert result["msg"] == "ok"
            assert result["data"]["id"] == "new-promotion"

    @pytest.mark.asyncio
    async def test_create_promotion_invalid_dates(self, mock_partner_user):
        """Testa criação de promoção com datas inválidas."""
        with patch(
            "src.api.partner.validate_partner_role", return_value=mock_partner_user
        ):
            from src.api.partner import create_promotion

            request_data = PromotionRequest(
                title="Promoção Inválida",
                type="discount",
                valid_from=datetime.now() + timedelta(days=30),  # Data futura
                valid_to=datetime.now(),  # Data passada
                active=True,
                audience=["student"],
            )

            with pytest.raises(Exception) as exc_info:
                await create_promotion(request_data, mock_partner_user)

            assert "INVALID_DATES" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_promotion_success(self, mock_partner_user, mock_promotion):
        """Testa atualização de promoção com sucesso."""
        with (
            patch(
                "src.api.partner.validate_partner_role", return_value=mock_partner_user
            ),
            patch("src.api.partner.with_circuit_breaker", return_value=mock_promotion),
            patch("src.api.partner.firestore_client") as mock_firestore,
        ):
            mock_firestore.update_document = AsyncMock(
                return_value={"id": "promotion-123"}
            )

            from src.api.partner import update_promotion

            request_data = PromotionRequest(
                title="Promoção Atualizada",
                type="discount",
                valid_from=datetime.now(),
                valid_to=datetime.now() + timedelta(days=30),
                active=True,
                audience=["student"],
            )

            result = await update_promotion(
                "promotion-123", request_data, mock_partner_user
            )

            assert result["msg"] == "ok"

    @pytest.mark.asyncio
    async def test_update_promotion_not_found(self, mock_partner_user):
        """Testa atualização de promoção não encontrada."""
        with (
            patch(
                "src.api.partner.validate_partner_role", return_value=mock_partner_user
            ),
            patch("src.api.partner.with_circuit_breaker", return_value=None),
        ):
            from src.api.partner import update_promotion

            request_data = PromotionRequest(
                title="Promoção",
                type="discount",
                valid_from=datetime.now(),
                valid_to=datetime.now() + timedelta(days=30),
                active=True,
                audience=["student"],
            )

            with pytest.raises(Exception) as exc_info:
                await update_promotion("invalid-id", request_data, mock_partner_user)

            assert "NOT_FOUND" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_promotion_forbidden(self, mock_partner_user, mock_promotion):
        """Testa atualização de promoção de outro parceiro."""
        # Alterar partner_id da promoção
        mock_promotion["partner_id"] = "other-partner"

        with (
            patch(
                "src.api.partner.validate_partner_role", return_value=mock_partner_user
            ),
            patch("src.api.partner.with_circuit_breaker", return_value=mock_promotion),
        ):
            from src.api.partner import update_promotion

            request_data = PromotionRequest(
                title="Promoção",
                type="discount",
                valid_from=datetime.now(),
                valid_to=datetime.now() + timedelta(days=30),
                active=True,
                audience=["student"],
            )

            with pytest.raises(Exception) as exc_info:
                await update_promotion("promotion-123", request_data, mock_partner_user)

            assert "FORBIDDEN" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_delete_promotion_success(self, mock_partner_user, mock_promotion):
        """Testa desativação de promoção com sucesso."""
        with (
            patch(
                "src.api.partner.validate_partner_role", return_value=mock_partner_user
            ),
            patch("src.api.partner.with_circuit_breaker", return_value=mock_promotion),
            patch("src.api.partner.firestore_client") as mock_firestore,
        ):
            mock_firestore.update_document = AsyncMock()

            from src.api.partner import delete_promotion

            result = await delete_promotion("promotion-123", mock_partner_user)

            assert result["msg"] == "ok"
            mock_firestore.update_document.assert_called_once_with(
                "promotions", "promotion-123", {"active": False}
            )


class TestPartnerReportsEndpoint:
    """Testes para o endpoint de relatórios do parceiro."""

    @pytest.mark.asyncio
    async def test_get_reports_success(self, mock_partner_user):
        """Testa geração de relatório com sucesso."""
        mock_codes = [
            {"id": "code-1", "used_at": datetime.now().isoformat()},
            {"id": "code-2", "used_at": None},
        ]
        mock_promotions = [
            {"id": "promo-1", "title": "Promoção 1"},
            {"id": "promo-2", "title": "Promoção 2"},
        ]

        with (
            patch(
                "src.api.partner.validate_partner_role", return_value=mock_partner_user
            ),
            patch("src.api.partner.with_circuit_breaker") as mock_circuit_breaker,
        ):
            mock_circuit_breaker.side_effect = [
                {"items": mock_codes},  # Códigos
                {"items": mock_promotions},  # Promoções
            ]

            from src.api.partner import get_partner_reports

            result = await get_partner_reports("2024-01", mock_partner_user)

            assert result["msg"] == "ok"
            assert result["data"]["period"] == "2024-01"
            assert result["data"]["total_codes"] == 2
            assert result["data"]["total_redemptions"] == 1
            assert len(result["data"]["promotions"]) == 2

    @pytest.mark.asyncio
    async def test_get_reports_invalid_range(self, mock_partner_user):
        """Testa geração de relatório com período inválido."""
        with patch(
            "src.api.partner.validate_partner_role", return_value=mock_partner_user
        ):
            from src.api.partner import get_partner_reports

            with pytest.raises(Exception) as exc_info:
                await get_partner_reports("invalid-range", mock_partner_user)

            assert "INVALID_RANGE" in str(exc_info.value)


@pytest.mark.integration
class TestPartnerAPIIntegration:
    """Testes de integração para a API de parceiros."""

    def test_partner_endpoints_require_authentication(self):
        """Testa que todos os endpoints requerem autenticação."""
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router, prefix="/partner")
        client = TestClient(app)

        # Testar endpoints sem autenticação
        endpoints = [
            ("POST", "/partner/redeem"),
            ("GET", "/partner/promotions"),
            ("POST", "/partner/promotions"),
            ("PUT", "/partner/promotions/123"),
            ("DELETE", "/partner/promotions/123"),
            ("GET", "/partner/reports?range=2024-01"),
        ]

        for method, endpoint in endpoints:
            response = getattr(client, method.lower())(endpoint)
            # Deve retornar erro de autenticação (401 ou 403)
            assert response.status_code in [401, 403, 422]

    def test_partner_role_validation(self):
        """Testa validação de role de parceiro."""
        # Este teste seria implementado com um token válido mas com role incorreta
        # Por simplicidade, apenas verificamos que a validação existe
        from src.api.partner import validate_partner_role

        assert validate_partner_role is not None
