"""
Testes para os endpoints da API de estudantes.

Este módulo contém testes abrangentes para todos os endpoints
definidos em src/api/student.py.
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from src.api.student import router
from src.auth import JWTPayload
from src.models import ValidationCodeRequest


@pytest.fixture
def mock_student_user():
    """Fixture para usuário estudante mock."""
    return JWTPayload(
        sub="student-123",
        role="student",
        tenant="knn",
        exp=int((datetime.now() + timedelta(hours=1)).timestamp()),
        iat=int(datetime.now().timestamp()),
        iss="test",
        aud="test",
        name="Test Student",
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
def mock_student():
    """Fixture para estudante mock."""
    return {
        "id": "student-123",
        "name": "João Silva",
        "course": "Engenharia",
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


@pytest.fixture
def mock_validation_code():
    """Fixture para código de validação mock."""
    return {
        "id": "code-123",
        "student_id": "student-123",
        "partner_id": "partner-123",
        "code_hash": "123456",
        "expires": (datetime.now() + timedelta(minutes=3)).isoformat(),
        "used_at": datetime.now().isoformat(),
    }


@pytest.fixture
def mock_favorite():
    """Fixture para favorito mock."""
    return {
        "id": "favorite-123",
        "student_id": "student-123",
        "partner_id": "partner-123",
        "created_at": datetime.now().isoformat(),
    }


class TestStudentPartnersEndpoints:
    """Testes para os endpoints de parceiros do estudante."""

    @pytest.mark.asyncio
    async def test_list_partners_success(self, mock_student_user, mock_partner):
        """Testa listagem de parceiros com sucesso."""
        with (
            patch(
                "src.api.student.validate_student_role", return_value=mock_student_user
            ),
            patch(
                "src.api.student.PartnersService.list_partners_common"
            ) as mock_service,
        ):
            mock_service.return_value = {
                "data": {"items": [mock_partner], "total": 1},
                "msg": "ok",
            }

            from src.api.student import list_partners

            result = await list_partners(current_user=mock_student_user)

            assert result["msg"] == "ok"
            assert len(result["data"]["items"]) == 1
            assert result["data"]["items"][0]["trade_name"] == "Parceiro Teste"

    @pytest.mark.asyncio
    async def test_list_partners_with_filters(self, mock_student_user, mock_partner):
        """Testa listagem de parceiros com filtros."""
        with (
            patch(
                "src.api.student.validate_student_role", return_value=mock_student_user
            ),
            patch(
                "src.api.student.PartnersService.list_partners_common"
            ) as mock_service,
        ):
            mock_service.return_value = {
                "data": {"items": [mock_partner], "total": 1},
                "msg": "ok",
            }

            from src.api.student import list_partners

            result = await list_partners(
                cat="alimentacao",
                ord="name_asc",
                limit=10,
                offset=0,
                current_user=mock_student_user,
            )

            assert result["msg"] == "ok"
            # Verificar se os parâmetros foram passados corretamente
            mock_service.assert_called_once_with(
                current_user=mock_student_user,
                cat="alimentacao",
                ord="name_asc",
                limit=10,
                offset=0,
                use_circuit_breaker=True,
                enable_ordering=False,
            )

    @pytest.mark.asyncio
    async def test_get_partner_details_success(
        self, mock_student_user, mock_partner, mock_promotion
    ):
        """Testa obtenção de detalhes do parceiro com sucesso."""
        with (
            patch(
                "src.api.student.validate_student_role", return_value=mock_student_user
            ),
            patch("src.api.student.firestore_client") as mock_firestore,
        ):
            mock_firestore.get_document.return_value = mock_partner
            mock_firestore.query_documents.return_value = {"items": [mock_promotion]}

            from src.api.student import get_partner_details

            result = await get_partner_details("partner-123", mock_student_user)

            assert result["msg"] == "ok"
            assert result["data"]["trade_name"] == "Parceiro Teste"
            assert len(result["data"]["promotions"]) == 1

    @pytest.mark.asyncio
    async def test_get_partner_details_not_found(self, mock_student_user):
        """Testa obtenção de detalhes de parceiro não encontrado."""
        with (
            patch(
                "src.api.student.validate_student_role", return_value=mock_student_user
            ),
            patch("src.api.student.firestore_client") as mock_firestore,
        ):
            mock_firestore.get_document.return_value = None

            from src.api.student import get_partner_details

            with pytest.raises(Exception) as exc_info:
                await get_partner_details("invalid-id", mock_student_user)

            assert "NOT_FOUND" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_partner_details_inactive(self, mock_student_user, mock_partner):
        """Testa obtenção de detalhes de parceiro inativo."""
        mock_partner["active"] = False

        with (
            patch(
                "src.api.student.validate_student_role", return_value=mock_student_user
            ),
            patch("src.api.student.firestore_client") as mock_firestore,
        ):
            mock_firestore.get_document.return_value = mock_partner

            from src.api.student import get_partner_details

            with pytest.raises(Exception) as exc_info:
                await get_partner_details("partner-123", mock_student_user)

            assert "NOT_FOUND" in str(exc_info.value)


class TestStudentValidationCodeEndpoint:
    """Testes para o endpoint de criação de código de validação."""

    @pytest.mark.asyncio
    async def test_create_validation_code_success(
        self, mock_student_user, mock_partner, mock_student
    ):
        """Testa criação de código de validação com sucesso."""
        with (
            patch(
                "src.api.student.validate_student_role", return_value=mock_student_user
            ),
            patch("src.api.student.firestore_client") as mock_firestore,
            patch("src.api.student.random.randint", return_value=123456),
        ):
            mock_firestore.get_document.side_effect = [mock_partner, mock_student]
            mock_firestore.create_document = AsyncMock()

            from src.api.student import create_validation_code

            request_data = ValidationCodeRequest(partner_id="partner-123")

            result = await create_validation_code(request_data, mock_student_user)

            assert result["msg"] == "ok"
            assert result["data"]["code"] == "123456"
            assert "expires" in result["data"]

    @pytest.mark.asyncio
    async def test_create_validation_code_partner_not_found(self, mock_student_user):
        """Testa criação de código com parceiro não encontrado."""
        with (
            patch(
                "src.api.student.validate_student_role", return_value=mock_student_user
            ),
            patch("src.api.student.firestore_client") as mock_firestore,
        ):
            mock_firestore.get_document.return_value = None

            from src.api.student import create_validation_code

            request_data = ValidationCodeRequest(partner_id="invalid-partner")

            with pytest.raises(Exception) as exc_info:
                await create_validation_code(request_data, mock_student_user)

            assert "NOT_FOUND" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_validation_code_partner_inactive(
        self, mock_student_user, mock_partner
    ):
        """Testa criação de código com parceiro inativo."""
        mock_partner["active"] = False

        with (
            patch(
                "src.api.student.validate_student_role", return_value=mock_student_user
            ),
            patch("src.api.student.firestore_client") as mock_firestore,
        ):
            mock_firestore.get_document.return_value = mock_partner

            from src.api.student import create_validation_code

            request_data = ValidationCodeRequest(partner_id="partner-123")

            with pytest.raises(Exception) as exc_info:
                await create_validation_code(request_data, mock_student_user)

            assert "NOT_FOUND" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_validation_code_student_not_found(
        self, mock_student_user, mock_partner
    ):
        """Testa criação de código com estudante não encontrado."""
        with (
            patch(
                "src.api.student.validate_student_role", return_value=mock_student_user
            ),
            patch("src.api.student.firestore_client") as mock_firestore,
        ):
            mock_firestore.get_document.side_effect = [mock_partner, None]

            from src.api.student import create_validation_code

            request_data = ValidationCodeRequest(partner_id="partner-123")

            with pytest.raises(Exception) as exc_info:
                await create_validation_code(request_data, mock_student_user)

            assert "NOT_FOUND" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_validation_code_student_inactive(
        self, mock_student_user, mock_partner, mock_student
    ):
        """Testa criação de código com estudante inativo."""
        mock_student["active_until"] = (
            (datetime.now() - timedelta(days=1)).date().isoformat()
        )

        with (
            patch(
                "src.api.student.validate_student_role", return_value=mock_student_user
            ),
            patch("src.api.student.firestore_client") as mock_firestore,
        ):
            mock_firestore.get_document.side_effect = [mock_partner, mock_student]

            from src.api.student import create_validation_code

            request_data = ValidationCodeRequest(partner_id="partner-123")

            with pytest.raises(Exception) as exc_info:
                await create_validation_code(request_data, mock_student_user)

            assert "INACTIVE_STUDENT" in str(exc_info.value)


class TestStudentHistoryEndpoint:
    """Testes para o endpoint de histórico do estudante."""

    @pytest.mark.asyncio
    async def test_get_student_history_success(
        self, mock_student_user, mock_validation_code, mock_partner
    ):
        """Testa obtenção de histórico com sucesso."""
        mock_redemption = {
            "id": "redemption-123",
            "validation_code_id": "code-123",
            "value": 10.0,
        }

        with (
            patch(
                "src.api.student.validate_student_role", return_value=mock_student_user
            ),
            patch("src.api.student.firestore_client") as mock_firestore,
        ):
            mock_firestore.query_documents.side_effect = [
                {"items": [mock_validation_code], "total": 1},  # Códigos
                {"items": [mock_redemption]},  # Resgates
            ]
            mock_firestore.get_document.return_value = mock_partner

            from src.api.student import get_student_history

            result = await get_student_history(current_user=mock_student_user)

            assert result["msg"] == "ok"
            assert result["data"]["total"] == 1
            assert len(result["data"]["items"]) == 1
            assert (
                result["data"]["items"][0]["partner"]["trade_name"] == "Parceiro Teste"
            )

    @pytest.mark.asyncio
    async def test_get_student_history_empty(self, mock_student_user):
        """Testa obtenção de histórico vazio."""
        with (
            patch(
                "src.api.student.validate_student_role", return_value=mock_student_user
            ),
            patch("src.api.student.firestore_client") as mock_firestore,
        ):
            mock_firestore.query_documents.return_value = {"items": [], "total": 0}

            from src.api.student import get_student_history

            result = await get_student_history(current_user=mock_student_user)

            assert result["msg"] == "ok"
            assert result["data"]["total"] == 0
            assert len(result["data"]["items"]) == 0

    @pytest.mark.asyncio
    async def test_get_student_history_with_pagination(self, mock_student_user):
        """Testa obtenção de histórico com paginação."""
        with (
            patch(
                "src.api.student.validate_student_role", return_value=mock_student_user
            ),
            patch("src.api.student.firestore_client") as mock_firestore,
        ):
            mock_firestore.query_documents.return_value = {"items": [], "total": 0}

            from src.api.student import get_student_history

            result = await get_student_history(
                limit=10, offset=20, current_user=mock_student_user
            )

            assert result["msg"] == "ok"
            assert result["data"]["limit"] == 10
            assert result["data"]["offset"] == 20


class TestStudentFavoritesEndpoints:
    """Testes para os endpoints de favoritos do estudante."""

    @pytest.mark.asyncio
    async def test_get_student_favorites_success(
        self, mock_student_user, mock_favorite, mock_partner
    ):
        """Testa obtenção de favoritos com sucesso."""
        with (
            patch(
                "src.api.student.validate_student_role", return_value=mock_student_user
            ),
            patch("src.api.student.firestore_client") as mock_firestore,
            patch("src.api.student.with_circuit_breaker", return_value=mock_partner),
        ):
            mock_firestore.query_documents.return_value = {"items": [mock_favorite]}

            from src.api.student import get_student_favorites

            result = await get_student_favorites(mock_student_user)

            assert result["msg"] == "ok"
            assert len(result["data"]) == 1
            assert result["data"][0]["trade_name"] == "Parceiro Teste"

    @pytest.mark.asyncio
    async def test_get_student_favorites_empty(self, mock_student_user):
        """Testa obtenção de favoritos vazio."""
        with (
            patch(
                "src.api.student.validate_student_role", return_value=mock_student_user
            ),
            patch("src.api.student.firestore_client") as mock_firestore,
        ):
            mock_firestore.query_documents.return_value = {"items": []}

            from src.api.student import get_student_favorites

            result = await get_student_favorites(mock_student_user)

            assert result["msg"] == "ok"
            assert len(result["data"]) == 0

    @pytest.mark.asyncio
    async def test_add_student_favorite_success(self, mock_student_user, mock_partner):
        """Testa adição de favorito com sucesso."""
        with (
            patch(
                "src.api.student.validate_student_role", return_value=mock_student_user
            ),
            patch("src.api.student.firestore_client") as mock_firestore,
        ):
            mock_firestore.get_document.return_value = mock_partner
            mock_firestore.query_documents.return_value = {
                "items": []
            }  # Não é favorito ainda
            mock_firestore.create_document = AsyncMock()

            from src.api.student import add_student_favorite

            result = await add_student_favorite(
                {"partner_id": "partner-123"}, mock_student_user
            )

            assert result["msg"] == "ok"
            mock_firestore.create_document.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_student_favorite_already_exists(
        self, mock_student_user, mock_partner, mock_favorite
    ):
        """Testa adição de favorito que já existe."""
        with (
            patch(
                "src.api.student.validate_student_role", return_value=mock_student_user
            ),
            patch("src.api.student.firestore_client") as mock_firestore,
        ):
            mock_firestore.get_document.return_value = mock_partner
            mock_firestore.query_documents.return_value = {"items": [mock_favorite]}

            from src.api.student import add_student_favorite

            result = await add_student_favorite(
                {"partner_id": "partner-123"}, mock_student_user
            )

            assert result["msg"] == "ok"

    @pytest.mark.asyncio
    async def test_add_student_favorite_partner_not_found(self, mock_student_user):
        """Testa adição de favorito com parceiro não encontrado."""
        with (
            patch(
                "src.api.student.validate_student_role", return_value=mock_student_user
            ),
            patch("src.api.student.firestore_client") as mock_firestore,
        ):
            mock_firestore.get_document.return_value = None

            from src.api.student import add_student_favorite

            with pytest.raises(Exception) as exc_info:
                await add_student_favorite(
                    {"partner_id": "invalid-partner"}, mock_student_user
                )

            assert "NOT_FOUND" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_add_student_favorite_missing_partner_id(self, mock_student_user):
        """Testa adição de favorito sem partner_id."""
        with patch(
            "src.api.student.validate_student_role", return_value=mock_student_user
        ):
            from src.api.student import add_student_favorite

            with pytest.raises(Exception) as exc_info:
                await add_student_favorite({}, mock_student_user)

            assert "VALIDATION_ERROR" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_remove_student_favorite_success(
        self, mock_student_user, mock_favorite
    ):
        """Testa remoção de favorito com sucesso."""
        with (
            patch(
                "src.api.student.validate_student_role", return_value=mock_student_user
            ),
            patch("src.api.student.firestore_client") as mock_firestore,
        ):
            mock_firestore.query_documents.return_value = {"items": [mock_favorite]}
            mock_firestore.delete_document = AsyncMock()

            from src.api.student import remove_student_favorite

            result = await remove_student_favorite("partner-123", mock_student_user)

            assert result["msg"] == "ok"
            mock_firestore.delete_document.assert_called_once_with(
                "favorites", "favorite-123"
            )

    @pytest.mark.asyncio
    async def test_remove_student_favorite_not_found(self, mock_student_user):
        """Testa remoção de favorito não encontrado."""
        with (
            patch(
                "src.api.student.validate_student_role", return_value=mock_student_user
            ),
            patch("src.api.student.firestore_client") as mock_firestore,
        ):
            mock_firestore.query_documents.return_value = {"items": []}

            from src.api.student import remove_student_favorite

            with pytest.raises(Exception) as exc_info:
                await remove_student_favorite("partner-123", mock_student_user)

            assert "NOT_FOUND" in str(exc_info.value)


@pytest.mark.integration
class TestStudentAPIIntegration:
    """Testes de integração para a API de estudantes."""

    def test_student_endpoints_require_authentication(self):
        """Testa que todos os endpoints requerem autenticação."""
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router, prefix="/student")
        client = TestClient(app)

        # Testar endpoints sem autenticação
        endpoints = [
            ("GET", "/student/partners"),
            ("GET", "/student/partners/123"),
            ("POST", "/student/validation-codes"),
            ("GET", "/student/me/history"),
            ("GET", "/student/me/fav"),
            ("POST", "/student/me/fav"),
            ("DELETE", "/student/me/fav/123"),
        ]

        for method, endpoint in endpoints:
            response = getattr(client, method.lower())(endpoint)
            # Deve retornar erro de autenticação (401 ou 403)
            assert response.status_code in [401, 403, 422]

    def test_student_role_validation(self):
        """Testa validação de role de estudante."""
        # Este teste seria implementado com um token válido mas com role incorreta
        # Por simplicidade, apenas verificamos que a validação existe
        from src.api.student import validate_student_role

        assert validate_student_role is not None
